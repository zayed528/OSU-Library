"""Dynamo-backed store helpers for the Library app.

This module provides thin helper functions for two DynamoDB tables:
- a table that holds 'table' records (table metadata and seats)
- a table that tracks temporary "holds" for seats

Notes / expectations:
- Environment variables are used to locate the DynamoDB tables and region.
- The module intentionally keeps functions small and thin; callers handle
  higher-level business logic and retries.
- The holds table uses an `expiresAt` numeric attribute as a TTL marker.
  DynamoDB's TTL feature can remove expired items automatically; the
  `expire_holds` function performs a best-effort sweep to free seats
  immediately in case your application requires active cleanup.

Security note: this module calls `load_dotenv()` to load environment
variables from a local `.env` file if present. Do NOT commit files that
contain credentials (AWS keys, tokens) into source control. Prefer IAM
roles, temporary credentials, or a secrets manager in production.
"""

import os
import time
import uuid
from typing import List, Optional
import logging

import boto3
from boto3.dynamodb.conditions import Key, Attr
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load a local .env file if present. This is convenient for local dev only.
# Make sure any .env with secrets is in .gitignore and never pushed.
load_dotenv()

# Configuration: prefer explicit environment variables; provide safe defaults
REGION = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
TABLES_NAME = os.getenv("DDB_TABLES", "LibraryTables")
HOLDS_NAME  = os.getenv("DDB_HOLDS", "LibraryHolds")

dynamodb = boto3.resource("dynamodb", region_name=REGION)
tables_tbl = dynamodb.Table(TABLES_NAME)
holds_tbl  = dynamodb.Table(HOLDS_NAME)

def now() -> int:
    """Return current time as integer epoch seconds.

    Used for TTL calculation (expiresAt).
    """
    return int(time.time())


# ---------- TABLES ----------
def upsert_table(item: dict) -> None:
    """Create or overwrite a table item in the tables table.

    This is a thin wrapper around `put_item`.
    """
    tables_tbl.put_item(Item=item)


def get_floor_tables(floor_id: str) -> List[dict]:
    """Return all table items for a given floor.

    Tries a GSI query first (fast and cheap). If the GSI is missing or the
    query fails, falls back to a scan with a filter expression (less efficient).
    """
    try:
        resp = tables_tbl.query(
            IndexName="GSI_FloorId",
            KeyConditionExpression=Key("floorId").eq(floor_id),
        )
        return resp.get("Items", [])
    except Exception:
        # Query might fail if the index doesn't exist or due to permissions.
        logger.debug("GSI query failed for floor %s, falling back to scan", floor_id)
        scan = tables_tbl.scan(FilterExpression=Attr("floorId").eq(floor_id))
        return scan.get("Items", [])


def get_all_tables() -> List[dict]:
    """Get all library tables from DynamoDB.
    
    Returns a list of all table items. Use scan() for simplicity.
    For large datasets, consider pagination.
    """
    try:
        resp = tables_tbl.scan()
        return resp.get("Items", [])
    except Exception as e:
        logger.error(f"Error scanning all tables: {e}")
        return []


def get_table(table_id: str) -> Optional[dict]:
    """Get a single table item by tableId (primary key).

    Returns the raw DynamoDB item dict or None if not found.
    """
    resp = tables_tbl.get_item(Key={"tableId": table_id})
    return resp.get("Item")


def save_table(item: dict) -> None:
    """Persist a table item to the tables table.

    Thin wrapper around `put_item` kept for symmetry with `get_table`.
    """
    tables_tbl.put_item(Item=item)


# ---------- HOLDS ----------
def create_hold(table_id: str, seat_index: int, ttl_sec: int = 120) -> str:
    """Create a temporary hold for a seat and return the holdId.

    The hold record contains an `expiresAt` epoch so TTL-based cleanup can
    remove it automatically. The application may also run `expire_holds`
    periodically for immediate housekeeping.
    """
    hold_id = str(uuid.uuid4())
    holds_tbl.put_item(
        Item={
            "holdId": hold_id,
            "tableId": table_id,
            "seatIndex": seat_index,
            "expiresAt": now() + ttl_sec,  # TTL attribute (epoch seconds)
        }
    )
    return hold_id


def get_hold(hold_id: str) -> Optional[dict]:
    """Return hold item by holdId or None if not present."""
    resp = holds_tbl.get_item(Key={"holdId": hold_id})
    return resp.get("Item")


def delete_hold(hold_id: str) -> None:
    """Delete a hold by its holdId."""
    holds_tbl.delete_item(Key={"holdId": hold_id})


def expire_holds() -> None:
    """Best-effort sweep for expired holds.

    This scans the entire holds table and for each expired hold will:
    - fetch the associated table item
    - if the seat is still marked HELD, change it to FREE and save the table
    - delete the hold record

    Note: scanning can be expensive for large tables. For production use,
    prefer a targeted approach (e.g. DynamoDB Streams + Lambda) or paging
    the scan with limits.
    """
    resp = holds_tbl.scan()
    for h in resp.get("Items", []):
        if h.get("expiresAt", 0) < now():
            tab = get_table(h["tableId"])
            if tab:
                idx = h["seatIndex"]
                if 0 <= idx < len(tab["seats"]) and tab["seats"][idx].get("status") == "HELD":
                    tab["seats"][idx]["status"] = "FREE"
                    save_table(tab)
            delete_hold(h["holdId"])
