# SeatSense 

SeatSense helps patrons find open seats in the Thompson Library with a real‑time dashboard powered by Computer Vision. It includes:
- A Library API that serves occupancy data from DynamoDB.
- A simple dashboard frontend (vanilla HTML/CSS/JS).
- An optional Community Forum (separate API + frontend).
- A Rekognition demo script for image-based seat detection.

## Overview
SeatSense uses Amazon Rekognition (Custom Labels) to detect seat occupancy and stores normalized results in DynamoDB. A lightweight dashboard fetches from a FastAPI backend to show availability by floor and table. A separate forum service lets users post questions and replies.

## Features
- Real‑time seat occupancy
- Interactive dashboard
- Community forum
- Privacy‑first design (no PII; bounding boxes only)
- Cloud‑native storage (DynamoDB + S3)
- Clean, typed APIs (FastAPI + Pydantic)
- Environment‑based configuration
- Easy local development (run services side‑by‑side)

## Architecture
- Two FastAPI services + two static frontends.
  - Library API (Thompson dashboard) on port 8000 → `app/main.py`
  - Community Forum API on port 8002 → `forum/backend/main.py`
- AWS: Rekognition Custom Labels, S3 (images), DynamoDB (tables/chairs/holds, forum content).
- Frontends are static HTML/JS:
  - Dashboard: `app/frontend/product_demo.html` (calls Library API)
  - Forum: `forum/frontend/index.html` (calls Forum API)

## Tech Stack
- Languages: Python, JavaScript, HTML5, CSS3
- Backend: FastAPI, Uvicorn, Pydantic, python‑dotenv
- AWS SDK: Boto3 (DynamoDB, Rekognition, S3)
- Frontend: Vanilla JS (Fetch API), CSS Grid/Flex
- Imaging: Pillow (PIL) for annotation
- Data: JSON over HTTP, DynamoDB items

## Project Structure
```
OSU-Library/
├─ README.md
├─ requirements.txt
├─ app/
│  ├─ main.py                 # Library API (port 8000)
│  ├─ store_dynamo.py         # DynamoDB access for library data
│  ├─ store.py                # (if used) local store variants
│  ├─ schemas.py              # Pydantic models
│  ├─ update_chairs.py        # helpers to adjust occupancy
│  ├─ seed.py                 # seed helper(s)
│  ├─ test_rekognition.py     # Rekognition demo script
│  └─ frontend/
│     ├─ product_demo.html    # dashboard UI
│     ├─ app.js               # dashboard logic (hits :8000)
│     └─ styles.css
├─ forum/
│  ├─ backend/
│  │  ├─ main.py              # Forum API (port 8002)
│  │  └─ forum_store.py       # DynamoDB access for forum data
│  └─ frontend/
│     ├─ index.html
│     ├─ js/app.js            # hits :8002
│     └─ css/styles.css
├─ landing/                   # marketing/landing page
├─ data/                      # sample/seed data
└─ tools/
   └─ generate_seed.py
```

## Prerequisites
- macOS/Linux with Python 3.10+ (3.12 recommended)
- pip
- AWS account/credentials with access to Rekognition, DynamoDB, and S3

## Installation
```bash
# clone
git clone https://github.com/zayed528/SeatSense.git
cd SeatSense

# create virtual env
python3 -m venv .venv
source .venv/bin/activate

# install deps for Library API + tools
pip install -r requirements.txt

# install Forum API deps
pip install -r forum/backend/requirements.txt
```

## Configuration
Export environment variables (use temporary creds for local dev).
```bash
export AWS_DEFAULT_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="YOUR_KEY_ID"
export AWS_SECRET_ACCESS_KEY="YOUR_SECRET"
export AWS_SESSION_TOKEN="YOUR_SESSION_TOKEN"    # only if using temp creds
```
Optional overrides used by the Rekognition demo:
```bash
export REKOGNITION_MODEL_ARN="arn:aws:rekognition:...:project/.../version/.../..."
export SEATS_IMAGES_BUCKET="your-s3-bucket"
export TEST_IMAGE_KEY="IMG_5168 Medium.jpeg"   # S3 key (with spaces if needed)
```
Tip: you can put these into a local `.env` (not committed) and load via python‑dotenv.

## Running Locally
### Library API (port 8000)
```bash
# from repo root
python3 app/main.py
# -> http://127.0.0.1:8000 (docs: http://127.0.0.1:8000/docs)
```

### Community Forum API (port 8002)
```bash
# from repo root
python3 forum/backend/main.py
# -> http://127.0.0.1:8002 (docs: http://127.0.0.1:8002/docs)
```

### Frontends
- Thompson dashboard: open `app/frontend/product_demo.html` in your browser (or use VS Code “Live Server”). It expects the Library API on http://127.0.0.1:8000.
- Community forum: open `forum/frontend/index.html`. It expects the Forum API on http://127.0.0.1:8002.

If the dashboard shows a connection error, do a hard refresh (Cmd+Shift+R). The dashboard JS (`app/frontend/app.js`) already points to port 8000.

## Seed Data
You can pre-populate tables/chairs:
```bash
# examples (depending on your flow)
python3 app/seed.py
python3 tools/generate_seed.py
```
Also see `data/seedData.json` if you want to import sample items into DynamoDB.

## Rekognition Demo
The script draws detections on an S3 image using your custom model.
```bash
# set env (see Configuration), then:
python3 app/test_rekognition.py
```
What it does:
- Calls Rekognition Custom Labels `DetectCustomLabels` with your `MODEL_ARN`.
- Downloads the image from S3 and annotates bounding boxes using Pillow.
- Saves/opens a local preview with drawn boxes.

## API Reference
### Library API Endpoints (app/main.py)
- GET `/` → health info
- GET `/health` → runs a light sweep to expire holds
- GET `/floor/{floor_id}/tables` → list tables for a floor (F1..F11)
- POST `/hold` → hold a seat `{ tableId, seatIndex, ttlSec? }`
- POST `/confirm` → confirm a hold to OCCUPIED `{ holdId, ... }`
- POST `/release/{table_id}/{seat_index}` → release a seat to FREE
- GET `/api/library/tables` → aggregate of all floors for dashboard

### Forum API Endpoints (forum/backend/main.py)
- GET `/` → API info
- GET `/api/questions` → list questions
- GET `/api/questions/{post_id}` → question detail
- POST `/api/questions` → create question
- POST `/api/questions/{post_id}/replies` → add reply
- GET `/api/questions/search/?q=term` → search
- DELETE `/api/questions/{post_id}` → delete question

## Deployment
- Package each API separately (Docker or a simple service on your host).
- Configure environment variables in the target environment (no secrets in code).
- Serve frontends via static hosting (S3/CloudFront, Netlify, GitHub Pages).
- Enable CORS for the deployed origins.

## Troubleshooting
- Port already in use:
  ```bash
  lsof -i :8000 | awk 'NR>1 {print $2}' | xargs -r kill -9
  lsof -i :8002 | awk 'NR>1 {print $2}' | xargs -r kill -9
  ```
- ModuleNotFoundError: No module named 'app'
  - Run from the repo root: `python3 app/main.py` (not from inside `app/`).
- Dashboard still says “port 8001”
  - Hard refresh (Cmd+Shift+R) or disable cache in DevTools → Network → refresh.
- AWS access errors
  - Verify credentials/region are exported and not expired.

## FAQ
- Can I run both services together? Yes—Library API on 8000 and Forum API on 8002. The frontends are separate HTML files.
- Do you store faces or PII? No. Only seat/person bounding boxes and counts; no identities.
- Can I point the dashboard to a cloud API? Yes—change `API_BASE_URL` in `app/frontend/app.js`.

## Roadmap
- Historical analytics (trends, heatmaps, peak hours)
- Threshold alerts/notifications
- Admin UI for managing spaces, cameras, and moderation
- Multi‑location support and RBAC

## Contributing
PRs and issues welcome. Please open an issue to discuss major changes first.

## Authors
- Zayed Ali 
- Akshat Satyadev

## License
MIT 