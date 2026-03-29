# app/app.py
from app import create_app

# Expose Flask app for serverless deployment
app = create_app()
