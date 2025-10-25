"""Seed helper to populate the DynamoDB tables from local seed JSON.

This script is intended for local development to populate the `tables`
DynamoDB table with sample data. It performs the following steps:

- Reads `data/seedData.json` (relative to the repository root when invoked
    from the project root).
- For each table object in the `tables` array, it expands the `seats`
    list to include seat objects (with `seatId` and initial `status` of
    "FREE").
- Adds minimal defaults used by the matching/confirmation flows
    (`isOpenToJoin`, `topicTags`, `courseCodes`).
- Calls `upsert_table` to persist each table item into DynamoDB.

Notes:
- This module deliberately avoids importing heavy dependencies or
    performing validation beyond existence checks: it's a small dev helper.
- The seed JSON file is expected to contain an object with a top-level
    `tables` list. See `data/seedData.json` for the format.
"""

import json
from pathlib import Path
from app.store_dynamo import upsert_table

# Path is intentionally relative so running `python -m app.seed` from the
# repository root will find `data/seedData.json`. Adjust if you run the
# module from a different working directory.
SEED_PATH = Path("data/seedData.json")


def run_seed() -> None:
        """Read seed JSON and insert table items into DynamoDB.

        Raises SystemExit when the seed file is missing so callers get a clear
        error message.
        """
        if not SEED_PATH.exists():
                raise SystemExit("data/seedData.json not found. Run tools/generate_seed.py first.")

        seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))

        count = 0
        for t in seed.get("tables", []):
                # Expand seats to a list of seat objects. We generate a stable
                # `seatId` using the tableId and seat index. Each seat starts as
                # FREE so the app can put holds against them.
                t["seats"] = [
                        {"seatId": f"{t['tableId']}-S{i}", "status": "FREE"}
                        for i in range(t["capacity"])
                ]

                # Defaults used by matching and metadata features. The seed source
                # may omit these keys; ensure they exist so downstream code can
                # safely read them without additional checks.
                t.setdefault("isOpenToJoin", False)
                t.setdefault("topicTags", [])
                t.setdefault("courseCodes", [])

                # Persist the table item into DynamoDB. This upserts (create or
                # overwrite) the item so the seed script can be re-run safely.
                upsert_table(t)
                count += 1

        print(f"Seeded {count} tables to DynamoDB")


if __name__ == "__main__":
        run_seed()
