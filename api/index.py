"""Vercel serverless function handler for FastAPI"""
from app.main import app

# Vercel expects a handler function
handler = app
