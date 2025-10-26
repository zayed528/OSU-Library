import os
import boto3
from typing import List

REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table("LibraryTables")

def update_table_with_occupied_chairs(table_id: str, occupied_seat_indices: List[int]) -> None:
    """
    Mark given seat indices as OCCUPIED and set occupantUserId.
    Uses per-seat update expressions (no whole-item overwrite).
    """
    if not occupied_seat_indices:
        print(f"[{table_id}] Nothing to update.")
        return

    # optional fetch to validate seat bounds and show current status
    item = table.get_item(Key={"tableId": table_id}).get("Item")
    if not item:
        print(f"[ERROR] tableId '{table_id}' not found.")
        return

    seats = item.get("seats", [])
    n = len(seats)
    print(f"[{table_id}] seats={n}, updating indices={occupied_seat_indices}")

    for i in occupied_seat_indices:
        if i < 0 or i >= n:
            print(f"  - skip index {i}: out of range (0..{n-1})")
            continue

        # SET status + occupantUserId
        update_expr = "SET #seats[%d].#status = :occ, #seats[%d].#uid = :uid" % (i, i)
        expr_names = {"#seats": "seats", "#status": "status", "#uid": "occupantUserId"}
        expr_vals = {":occ": "OCCUPIED", ":uid": f"student_{i+1}"}

        table.update_item(
            Key={"tableId": table_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_vals,
            ConditionExpression="attribute_exists(tableId)"
        )
        print(f"  ✓ seat[{i}] -> OCCUPIED (occupantUserId=student_{i+1})")

def reset_all_seats_to_free(table_id: str) -> None:
    """
    Reset all seats to FREE and REMOVE occupantUserId (no None values).
    """
    item = table.get_item(Key={"tableId": table_id}).get("Item")
    if not item:
        print(f"[ERROR] tableId '{table_id}' not found.")
        return

    seats = item.get("seats", [])
    n = len(seats)
    print(f"[{table_id}] resetting {n} seats to FREE")

    for i in range(n):
        # Some items may not have occupantUserId – we can safely REMOVE it anyway.
        update_expr = f"SET #seats[{i}].#status = :free REMOVE #seats[{i}].#uid"
        expr_names = {"#seats": "seats", "#status": "status", "#uid": "occupantUserId"}
        expr_vals = {":free": "FREE"}

        table.update_item(
            Key={"tableId": table_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_vals,
            ConditionExpression="attribute_exists(tableId)"
        )

    print(f"  ✓ all seats FREE for {table_id}")

if __name__ == "__main__":
    print("OSU Library - Update Chair Occupancy from CV Detection")
    print("=" * 60)

    # Example: post-CV mapping
    # IMG_5159 Medium.jpeg -> F1-T02 (chairs 0,1 occupied)
    # Hardcoded based on visual inspection of images
    update_table_with_occupied_chairs("F1-T02", [0])

    # IMG_5168 Medium.jpeg -> F1-T03 (chair 0 occupied)
    # Hardcoded based on visual inspection of images
    update_table_with_occupied_chairs("F1-T03", [0])

    # Example reset (optional)
    # reset_all_seats_to_free("F1-T02")
