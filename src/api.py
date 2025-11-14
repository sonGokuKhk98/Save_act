from fastapi import FastAPI
from src.main import ReelExtractor

app = FastAPI(
    title="Multimodal AI Reel Data Extraction API",
    description="An API to extract structured data from video reels using Gemini AI.",
    version="1.0.0"
)

reel_extractor = ReelExtractor()

@app.get("/")
def read_root():
    """
    Root endpoint to check if the API is running.
    """
    return {"status": "online"}
