# Multimodal AI Reel Data Extraction

A system that extracts structured, actionable data from video reels using Gemini AI and stores it in supermemeory.ai.

## 🎯 Overview

This project addresses the problem of users saving reels but failing to revisit them. It automatically extracts structured data from video reels (workout routines, recipes, travel itineraries, products, tutorials, music) and stores them in a searchable format.

## 🏗️ Architecture

```
Video Input → Download → Segment → Analyze → Validate → Store
   ↓            ↓          ↓         ↓          ↓         ↓
Local/URL   Cloud/     Keyframes  Gemini    Pydantic  supermemeory.ai
           Local      + Audio    AI        Models
```

## 📁 Project Structure

```
Act/
├── src/
│   ├── models/          # Pydantic data models (6 categories)
│   ├── services/        # Business logic services
│   │   ├── video_downloader.py    # Video download/preprocessing
│   │   ├── video_segmenter.py      # Keyframe & audio extraction
│   │   ├── gemini_analyzer.py      # Gemini AI analysis
│   │   └── supermemeory_client.py  # supermemeory.ai integration
│   └── utils/           # Helper functions
│       ├── config.py    # Configuration management
│       └── file_utils.py # File handling utilities
├── tests/               # Test files
├── temp_storage/        # Temporary video files
├── main.py              # Main orchestration script
├── requirements.txt    # Python dependencies
└── .env                 # Environment variables (create from .env.example)
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+ (tested with 3.11.13)
- FFmpeg installed (`brew install ffmpeg` on macOS)
- API keys:
  - Gemini API key
  - supermemeory.ai API key

### 2. Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install FFmpeg (if not already installed)
# macOS:
brew install ffmpeg

# Linux:
sudo apt-get install ffmpeg

# Optional: Install Whisper for audio transcription
pip install openai-whisper
```

### 3. Configuration

Create a `.env` file in the project root:

```bash
# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Supermemeory.ai API
SUPERMEMEORY_API_KEY=your_supermemeory_api_key_here
SUPERMEMEORY_BASE_URL=https://api.supermemory.ai/

# Processing Configuration (optional)
MAX_VIDEO_SIZE_MB=500
KEYFRAME_INTERVAL_SECONDS=3
MAX_VIDEO_DURATION_MINUTES=5
TEMP_STORAGE_PATH=./temp_storage
```

### 4. Usage

#### Basic Usage (Local File)

```bash
python main.py path/to/video.mp4
```

#### With Options

```bash
# Specify category
python main.py video.mp4 --category workout

# Skip keyframe extraction (faster)
python main.py video.mp4 --no-keyframes

# Skip audio transcription (faster)
python main.py video.mp4 --no-transcribe
```

#### Programmatic Usage

```python
from main import ReelExtractor

extractor = ReelExtractor()
result = extractor.extract(
    input_source="path/to/video.mp4",
    source_type="file",
    preferred_category="workout"  # Optional
)

if result["success"]:
    print(f"Category: {result['extraction'].category}")
    print(f"Title: {result['extraction'].title}")
    print(f"Stored: {result['stored']}")
```

## 📊 Supported Categories

### 1. 🏋️ Workout Videos
Extracts:
- Exercise names
- Sets, reps, durations
- Rest periods
- Total rounds
- Difficulty level
- Music tempo (BPM)

### 2. 🍳 Recipe Videos
Extracts:
- Ingredients with quantities
- Step-by-step instructions
- Prep/cook time
- Utensils needed
- Servings

### 3. 🧳 Travel Videos
Extracts:
- Destination
- Activities and locations
- Google Maps links
- Booking links
- Day-by-day itinerary
- Estimated budget

### 4. 🛍️ Product Videos
Extracts:
- Product names
- Brand names
- Prices
- Purchase links
- Product categories

### 5. 💡 Educational/Tutorial Videos
Extracts:
- Topic/subject
- Step-by-step instructions
- Tools required
- Resource links
- Prerequisites
- Estimated time

### 6. 🎶 Music Videos
Extracts:
- Song title
- Artist name
- Genre
- Lyrics snippet
- Spotify/YouTube links
- Mood/vibe

## 🔧 Services

### VideoDownloader
- Downloads videos from URLs (to be implemented)
- Processes local video files
- Validates file format and size

### VideoSegmenter
- Extracts keyframes (1 per 2-5 seconds)
- Extracts audio track
- Transcribes audio using Whisper

### GeminiAnalyzer
- Detects video category
- Extracts structured data using Gemini 1.5 Pro
- Validates output against Pydantic schemas

### SupermemeoryClient
- Stores extracted data in supermemeory.ai
- Generates tags based on category
- Handles API errors and retries

## 📝 Data Models

All data models use Pydantic for validation:

- `BaseExtraction` - Base model with common fields
- `WorkoutRoutine` - Workout extraction
- `RecipeCard` - Recipe extraction
- `TravelItinerary` - Travel extraction
- `ProductCatalog` - Product extraction
- `TutorialSummary` - Educational extraction
- `SongMetadata` - Music extraction

## 🐛 Troubleshooting

### FFmpeg not found
```bash
# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg
```

### Whisper not installed
```bash
pip install openai-whisper
```

### API Key errors
- Ensure `.env` file exists with correct API keys
- Check that keys are valid and have proper permissions

### Video processing errors
- Check video format (MP4, MOV, AVI supported)
- Ensure file size is under 500MB (configurable)
- Check video duration is under 5 minutes (configurable)

## 📚 Next Steps

- [ ] Add URL downloading support (Instagram, TikTok, YouTube Shorts)
- [ ] Add cloud storage integration (GCS, S3)
- [ ] Add web API (FastAPI)
- [ ] Add batch processing
- [ ] Add progress tracking
- [ ] Add error recovery and retry logic

## 📄 License

This is a hackathon prototype project.

