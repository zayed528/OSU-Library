import os
import boto3
from typing import List, Dict

REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table("LibraryTables")
rekognition = boto3.client('rekognition', region_name=REGION)

# Rekognition Model Configuration
MODEL_ARN = 'arn:aws:rekognition:us-east-1:343218220776:project/seat_occupancy_detector/version/seat_occupancy_detector.2025-10-25T19.02.59/1761433379854'
BUCKET = 'my-seat-occupancy-imgs'
MIN_CONFIDENCE = 90

# Image to Table mapping (you need to maintain this mapping)
IMAGE_TO_TABLE_MAP = {
    'IMG_5159 Medium.jpeg': 'F1-T02',  # Map to F1-T02; it should be occupied
    'IMG_5168 Medium.jpeg': 'F1-T31',  # Map to F1-T31; it should be occupied
    'IMG_5156 Medium.jpeg': 'F1-T03',  # Map to F1-T03; it should be available
    # Add more mappings as you take photos of different tables
}

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

def detect_occupied_chairs_from_image(photo: str) -> int:
    """
    Use AWS Rekognition to detect occupied chairs in an image.
    Returns the count of occupied chairs detected (persons detected).
    """
    try:
        response = rekognition.detect_custom_labels(
            ProjectVersionArn=MODEL_ARN,
            Image={'S3Object': {'Bucket': BUCKET, 'Name': photo}},
            MinConfidence=MIN_CONFIDENCE
        )
        
        occupied_count = 0
        print(f"  Detected {len(response['CustomLabels'])} label(s):")
        for label in response['CustomLabels']:
            print(f"    - {label['Name']} (Confidence: {label['Confidence']:.2f}%)")
            # Check if person is detected (occupied chair)
            if 'person' in label['Name'].lower() or 'occupied' in label['Name'].lower():
                occupied_count += 1
        
        return occupied_count
    except Exception as e:
        print(f"  [ERROR] CV Detection failed for {photo}: {str(e)}")
        return 0

def process_image_with_cv(photo: str, table_id: str) -> None:
    """
    Process an image using CV to detect occupancy and update the table.
    """
    print(f"\n[CV Processing] Image: {photo} -> Table: {table_id}")
    
    # Detect occupied chairs using CV
    occupied_count = detect_occupied_chairs_from_image(photo)
    
    if occupied_count == 0:
        # No occupied chairs detected, reset all to FREE
        print(f"  No occupied chairs detected. Resetting {table_id} to FREE.")
        reset_all_seats_to_free(table_id)
    else:
        # Mark first N seats as occupied based on detection
        occupied_indices = list(range(occupied_count))
        print(f"  Detected {occupied_count} occupied chair(s). Updating seats: {occupied_indices}")
        
        # First reset all seats to FREE
        reset_all_seats_to_free(table_id)
        # Then mark detected occupied seats
        update_table_with_occupied_chairs(table_id, occupied_indices)

if __name__ == "__main__":
    print("OSU Library - CV-Based Chair Occupancy Detection")
    print("=" * 60)
    print("Using AWS Rekognition Custom Model for Real-time Detection\n")

    # Process all images with CV detection
    for photo, table_id in IMAGE_TO_TABLE_MAP.items():
        process_image_with_cv(photo, table_id)
    
    print("\n" + "=" * 60)
    print("✓ CV Processing Complete!")
