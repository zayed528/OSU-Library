#!/bin/bash
# Startup script for SeatSense FastAPI Backend

# Set AWS environment variables
export AWS_DEFAULT_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}"
export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}"
export AWS_SESSION_TOKEN="${AWS_SESSION_TOKEN}"

# Start the FastAPI server
cd /home/ubuntu/OSU-Library
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001
