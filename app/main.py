"""Thompson Library API (DynamoDB)

This FastAPI application provides a small set of endpoints to interact with
library "tables" (study tables with seats) backed by DynamoDB. The code is
kept intentionally thin: data access is delegated to `app.store_dynamo` and
this module wires the HTTP routes and request/response validation.

Important behaviors:
- `/hold` marks a seat as HELD and inserts a short-lived hold record.
- `/confirm` converts a hold to an occupied seat and removes the hold.
- `/health` triggers `expire_holds()` which performs a best-effort sweep to
    free seats whose holds have expired. DynamoDB TTL is still relied on for
    eventual cleanup of hold records.

Security note: environment configuration (region, table names) is read via
environment variables. For local development you can use a `.env` file but
never commit credentials to source control.
"""
from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
import logging
from botocore.exceptions import ClientError
import uvicorn


log = logging.getLogger("library")
logging.basicConfig(level=logging.INFO)

from app.store_dynamo import (
        get_floor_tables, get_table, save_table,
        create_hold, get_hold, delete_hold, expire_holds
)


app = FastAPI(title="Thompson Library API (DynamoDB)")

# -------- Pydantic schemas (for docs/validation) --------
class Seat(BaseModel):
    """Schema for a single seat on a table.

    - `seatId` is an identifier for the seat (string)
    - `status` is one of: FREE, HELD, OCCUPIED (string)
    - `occupantUserId` optionally indicates who is occupying the seat
    """
    seatId: str
    status: str
    occupantUserId: Optional[str] = None

class Table(BaseModel):
        """Schema for a study table.

        - `tableId`, `floorId`, and `type` are identifiers/metadata.
        - `capacity` is the number of seats.
        - `seats` is a list of Seat objects and should have length == capacity.
        - `isOpenToJoin` is a boolean used by the matching route to filter
            tables that allow other users to join.
        - `courseCodes` and `topicTags` provide optional filtering metadata.
        """
        tableId: str
        floorId: str
        type: str
        capacity: int
        tags: list[str] = []
        seats: List[Seat] = []
        isOpenToJoin: bool = False
        topicTags: list[str] = []
        courseCodes: list[str] = []

class HoldRequest(BaseModel):
        """Request body to create a short-lived hold for a seat.

        - `tableId`: target table id
        - `seatIndex`: index into the `seats` array for the seat to hold
        - `ttlSec`: requested hold time in seconds (default 420 here; the
            store may enforce a different actual TTL)
        """
        tableId: str
        seatIndex: int
        ttlSec : int = 420

class ConfirmRequest(BaseModel):
    """Request body to confirm a previously-created hold.

    The `holdId` must reference an existing (non-expired) hold. Optional
    fields such as `courseCodes` and `topicTags` are stored on the table
    metadata to help matching/searching.
    """
    holdId: str
    courseCodes: list[str] = []
    topicTags: list[str] = []
    isOpenToJoin: bool = False

# -------- Routes --------
@app.get("/health")
def health():
    # Run a best-effort sweep for expired holds when the health check is
    # called. This keeps seats up-to-date for local/low-traffic deployments.
    # In production consider a periodic background job or a stream-based
    # approach instead.
    expire_holds()
    return {"ok": True}

@app.get("/floor/{floor_id}/tables", response_model=List[Table])
def list_floor_tables(floor_id: str):
    return get_floor_tables(floor_id)

@app.post("/hold")
def hold_seat(req: HoldRequest):
    tab = get_table(req.tableId)
    if not tab:
        raise HTTPException(404, "Table not found")
    if req.seatIndex < 0 or req.seatIndex >= tab["capacity"]:
        raise HTTPException(400, "Bad seat index")
    seat = tab["seats"][req.seatIndex]
    if seat["status"] != "FREE":
        raise HTTPException(409, "Seat not free")
    # Mark the seat as HELD locally and persist the table. A separate
    # 'hold' record is created so the system can expire the reservation
    # independently (DynamoDB TTL + optional sweeper).
    seat["status"] = "HELD"
    save_table(tab)
    hold_id = create_hold(req.tableId, req.seatIndex, ttl_sec=120)
    # Response includes the hold id the client must present when confirming.
    return {"holdId": hold_id, "expiresIn": 420}

@app.post("/confirm")
def confirm_seat(req: ConfirmRequest):
    hold = get_hold(req.holdId)
    if not hold:
        raise HTTPException(410, "Hold expired or not found")

    tab = get_table(hold["tableId"])
    if not tab:
        raise HTTPException(404, "Table not found")

    idx = int(hold["seatIndex"])
    if idx < 0 or idx >= len(tab.get("seats", [])):
        raise HTTPException(400, f"Bad seat index {idx}")

    # Mark seat as occupied
    seat = tab["seats"][idx]
    if seat.get("status") == "OCCUPIED":
        raise HTTPException(409, f"Seat {idx} already occupied")
    # Transition the seat to OCCUPIED and update optional metadata such as
    # whether the table is open to join. The hold record is removed once
    # the seat is confirmed.
    seat["status"] = "OCCUPIED"
    tab["isOpenToJoin"] = bool(req.isOpenToJoin)

    save_table(tab)
    delete_hold(req.holdId)

    return {"ok": True, "tableId": tab["tableId"], "seatIndex": idx}



@app.post("/release/{table_id}/{seat_index}")
def release_seat(table_id: str, seat_index: int):
    tab = get_table(table_id)
    if not tab:
        raise HTTPException(404, "Table not found")
    if seat_index < 0 or seat_index >= tab["capacity"]:
        raise HTTPException(400, "Bad seat index")
    # Force a seat to FREE (used when a user explicitly releases their seat).
    tab["seats"][seat_index]["status"] = "FREE"
    save_table(tab)
    return {"ok": True}

# (Optional) Study-buddy finder
@app.get("/match", response_model=List[Table])
def match_tables(
    floor_id: Optional[str], 
    courses: List[str] = Query(default=[]), 
    open_only: bool = True,
):
    floors = [floor_id] if floor_id else [f"F{i}" for i in range(1, 12)]
    out: List[dict] = []
    for f in floors:
        for t in get_floor_tables(f):
            # Filter out tables that aren't open to join when requested.
            if open_only and not t.get("isOpenToJoin", False):
                continue
            if courses:
                have = [c.upper() for c in t.get("courseCodes", [])]
                want = [c.upper() for c in courses]
                if not set(have) & set(want):
                    continue
            out.append(t)
    return out

@app.get("/holds/{hold_id}")
def get_hold_debug(hold_id: str):
    h = get_hold(hold_id)
    if not h:
        raise HTTPException(404, "Hold not found (may have expired)")
    return h    

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
    
