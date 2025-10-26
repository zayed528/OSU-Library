"""Vercel serverless function handler for FastAPI"""
from mangum import Mangum
from app.main import app

# Mangum wraps FastAPI for AWS Lambda/Vercel serverless
handler = Mangum(app, lifespan="off")
