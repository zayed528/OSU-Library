import boto3
import io
from PIL import Image, ImageDraw, ImageFont

# -------------------------------
# Replace with your info
# -------------------------------
MODEL_ARN = 'arn:aws:rekognition:us-east-1:343218220776:project/seat_occupancy_detector/version/seat_occupancy_detector.2025-10-25T19.02.59/1761433379854'
BUCKET = 'my-seat-occupancy-imgs'
PHOTO = 'IMG_5168 Medium.jpeg'  # note the space!
MIN_CONFIDENCE = 90
# -------------------------------

def display_image(bucket, photo, response):
    """Download image from S3 and draw bounding boxes for detected labels."""
    s3 = boto3.resource('s3')
    obj = s3.Object(bucket, photo)
    stream = io.BytesIO(obj.get()['Body'].read())
    image = Image.open(stream)
    draw = ImageDraw.Draw(image)
    img_width, img_height = image.size

    for label in response['CustomLabels']:
        print(f"Label: {label['Name']}, Confidence: {label['Confidence']:.2f}")
        if 'Geometry' in label:
            box = label['Geometry']['BoundingBox']
            left = img_width * box['Left']
            top = img_height * box['Top']
            width = img_width * box['Width']
            height = img_height * box['Height']

            # Draw rectangle
            draw.rectangle([left, top, left + width, top + height], outline='green', width=3)

            # Draw label text
            try:
                fnt = ImageFont.truetype('/Library/Fonts/Arial.ttf', 20)
            except:
                fnt = ImageFont.load_default()
            draw.text((left, top - 15), label['Name'], fill='green', font=fnt)

    image.show()

def detect_custom_labels():
    """Detect custom labels using Rekognition and display image."""
    client = boto3.client('rekognition')
    response = client.detect_custom_labels(
        ProjectVersionArn=MODEL_ARN,
        Image={'S3Object': {'Bucket': BUCKET, 'Name': PHOTO}},
        MinConfidence=MIN_CONFIDENCE
    )
    print(f"\nDetected {len(response['CustomLabels'])} labels:")
    display_image(BUCKET, PHOTO, response)

if __name__ == '__main__':
    detect_custom_labels()

