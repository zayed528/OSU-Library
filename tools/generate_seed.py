"""
generate_seed.py
-----------------
Creates a simulated dataset for OSU Thompson Library.

Floors 1-4  → 'group' layouts (individual + duo + group-of-4 + rooms)
Floors 5-11 → 'quiet' layouts (mostly individual + duo + some 4-seaters)

Output: data/seedData.json
"""

import json
from pathlib import Path


# BASIC METADATA

LIB_ID = "thompson"
LIB_NAME = "Thompson Library"


# CONFIGURATION

# NOTE: No 6-seater tables anywhere per your requirement.

# Floors 1–4: mixed layouts (individual + duo + group4 + study rooms)
LOWER_FLOOR_LAYOUTS = {
    1: dict(ind=25, duo=10, g4=10, rooms=2, room_cap=[6, 8]),
    2: dict(ind=22, duo=12, g4=10, rooms=2, room_cap=[6, 8]),
    3: dict(ind=26, duo=10, g4=10, rooms=2, room_cap=[6, 8]),
    4: dict(ind=20, duo=12, g4=10, rooms=1, room_cap=[8]),
}

# Floors 5–11: quiet floors (mostly individual + duo + small group)
# ~49 seats per floor (20*1 + 10*2 + 3*4 = 49)
UPPER_FLOOR_PLAN = dict(ind=20, duo=10, g4=3)


# OUTPUT CONTAINER

OUT = {
    "libraryId": LIB_ID,
    "name": LIB_NAME,
    "floors": [],
    "tables": [],
}

def add_table(tables, floor_id, idx, ttype, cap, tags):
    """
    Add a new table entry with a unique tableId like 'F5-T07'.
    """
    tables.append({
        "tableId": f"{floor_id}-T{idx:02d}",
        "floorId": floor_id,
        "type": ttype,   # "individual" | "duo" | "group" | "room"
        "capacity": cap,
        "tags": tags[:],
    })
    return idx + 1

def build_lower_floors():
    """
    Floors 1-4 : collaborative floors with group areas and bookable rooms.
    """
    for level in range(1, 5):
        floor_id = f"F{level}"
        OUT["floors"].append({"floorId": floor_id, "level": level, "layout": "group"})
        cfg = LOWER_FLOOR_LAYOUTS[level]
        idx = 1

        for _ in range(cfg["ind"]):
            idx = add_table(OUT["tables"], floor_id, idx, "individual", 1, ["open"])

        for _ in range(cfg["duo"]):
            idx = add_table(OUT["tables"], floor_id, idx, "duo", 2, ["open"])

        for _ in range(cfg["g4"]):
            idx = add_table(OUT["tables"], floor_id, idx, "group", 4, ["group"])

        for rc in cfg["room_cap"]:
            idx = add_table(OUT["tables"], floor_id, idx, "room", rc, ["group-room", "bookable"])

def build_upper_floors():
    """
    Floors 5-11 : quiet floors with mostly 1- and 2-seaters, few 4-seaters.
    """
    for level in range(5, 12):
        floor_id = f"F{level}"
        OUT["floors"].append({"floorId": floor_id, "level": level, "layout": "quiet"})
        idx = 1

        for _ in range(UPPER_FLOOR_PLAN["ind"]):
            idx = add_table(OUT["tables"], floor_id, idx, "individual", 1, ["quiet", "solo"])

        for _ in range(UPPER_FLOOR_PLAN["duo"]):
            idx = add_table(OUT["tables"], floor_id, idx, "duo", 2, ["quiet"])

        for _ in range(UPPER_FLOOR_PLAN["g4"]):
            idx = add_table(OUT["tables"], floor_id, idx, "group", 4, ["quiet-group"])

def main():
    """
    Build floors and tables, then write data/seedData.json.
    """
    build_lower_floors()
    build_upper_floors()

    out_path = Path("data/seedData.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(OUT, f, indent=2)

    print(f"Wrote {out_path}")
    print(f"Floors: {len(OUT['floors'])}")
    print(f"Tables: {len(OUT['tables'])}")

if __name__ == "__main__":
    main()
