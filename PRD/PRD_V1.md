This document outlines the requirements for the **Multimodal AI Reel Data Extraction** project, designed as a robust hackathon prototype.

---

## Product Requirements Document (PRD)

### 1. Goals and Objectives

The primary goal of this product is to address the problem of users saving reels but failing to revisit them.

1.  **Core Objective:** Develop a system that can download a video reel and extract comprehensive, structured data from it using a **multimodal LLM**.
2.  **User Value:** Ensure the user "go[es] back to them" by generating a "summarized beautiful and polished version" of the content.
3.  **Output Mandate:** The final output must be stored in the mandatory integration, **supermemeory.ai**.

### 2. Mandatory Technical Stack and Constraints

The core technical architecture must adhere strictly to the specified technologies, particularly the Gemini Stack and required integration.

| Component | Technology | Rationale / Constraint | Source(s) |
| :--- | :--- | :--- | :--- |
| **Core AI Engine** | **Gemini Stack (Gemini 1.5 Pro recommended)** | Required engine for performing comprehensive **multimodal analysis** (video, image, audio detection). The project must "Try to use gemini staxk wherever possible". | `google-generativeai` Python SDK |
| **Orchestration** | Python 3.10+ (with Google AI SDK) | Standard environment for prototype development and robust integration with the Gemini Stack APIs. | `google-generativeai`, `google-ai-generativelanguage` |
| **Output/Retrieval** | **supermemeory.ai** | Mandatory integration for storing the "summarized beautiful and polished version". | supermemeory.ai REST API |
| **Output Format** | JSON Schema (Pydantic models) | The output must be highly constrained and structured to reliably produce detailed formats like step-by-step cards and routines. | JSON Schema validation |
| **Storage** | Cloud Storage (e.g., Google Cloud Storage, S3) | Required for temporarily hosting the potentially large downloaded reel files and segmented audio/video components during processing. | `google-cloud-storage` or `boto3` |
| **Video Processing** | FFmpeg, OpenCV | Video segmentation, keyframe extraction, audio extraction | `ffmpeg-python`, `opencv-python` |
| **Audio Processing** | Whisper API / SpeechRecognition | Audio transcription for enhanced context | `openai-whisper` or `google-cloud-speech` |
| **HTTP Client** | Requests / httpx | API communication with supermemeory.ai | `requests`, `httpx` |
| **Data Validation** | Pydantic | Schema validation and data modeling | `pydantic` |
| **Async Processing** | asyncio / Celery | Background job processing for long-running tasks | `asyncio`, `celery` (optional) |
| **Configuration** | Environment Variables | API keys, storage credentials | `python-dotenv` |

### 3. Core Feature Requirements: Data Extraction (The "More Features")

The system must utilize Gemini's capabilities to perform specialized feature extraction based on the detected category of the reel. The output must be detailed and actionable.

#### A. **Workout Video Extraction (🏋️)**
*   **Detection Requirements:** Detect exercise names, sets, reps, durations, and music tempo.
*   **Required Output:** A **Workout routine with timers & rest periods**.
    *   *Example:* “3 rounds: 30s squats, 15s rest, 30s burpees…”.

#### B. **Recipe / Cooking Extraction (🍳)**
*   **Detection Requirements:** Detect ingredients, steps, and utensils.
*   **Required Output:** A **Step-by-step recipe card with measurements**.
    *   *Example:* “2 cups flour, 1 tbsp butter, whisk 2 min…”.

#### C. **Travel / Things to Do Extraction (🧳)**
*   **Detection Requirements:** Detect locations, activities, and sequence.
*   **Required Output:** An **Itinerary with map links or booking sites**.
    *   *Example:* “Day 1: Louvre Museum [Google Maps link]”.

#### D. **Product Video Extraction (🛍️)**
*   **Detection Requirements:** Detect brand logos, product names, URLs, or price tags.
*   **Required Output:** A **Product catalog with purchase links**.
    *   *Example:* “Nike Air Zoom Pegasus — ₹8,499 — [Amazon link]”.

#### E. **Educational / How-to Extraction (💡)**
*   **Detection Requirements:** Detect tools, sequence of tasks, and visual references.
*   **Required Output:** A **Tutorial summary with resource links**.
    *   *Example:* “Use Canva → Import asset → Add animation…”.

#### F. **Music / Mood Extraction (🎶)**
*   **Detection Requirements:** Detect lyrics, genre, and background visuals.
*   **Required Output:** **Song metadata + Spotify/YT link**.

### 4. System Architecture

#### 4.1 High-Level Architecture

```
┌─────────────┐
│   User      │
│  Input      │ (Reel URL/File)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│   Video Download & Preprocessing    │
│  - Download reel from URL           │
│  - Validate video format            │
│  - Upload to Cloud Storage          │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│   Video Segmentation Module         │
│  - Extract keyframes (1 per 2-5s)  │
│  - Extract audio track              │
│  - Generate audio transcript        │
│  - Store segments in temp storage   │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│   Gemini Multimodal Analysis        │
│  - Category Detection               │
│  - Feature Extraction               │
│  - Structured Data Generation       │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│   Data Validation & Transformation  │
│  - Pydantic schema validation       │
│  - Format conversion (JSON/MD)      │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│   supermemeory.ai Integration       │
│  - API authentication               │
│  - Data upload                      │
│  - Storage confirmation              │
└─────────────────────────────────────┘
```

#### 4.2 Component Specifications

**Video Download & Preprocessing Service**
- **Input:** Reel URL (Instagram, TikTok, YouTube Shorts) or local file path
- **Output:** Video file stored in cloud storage bucket
- **Requirements:**
  - Support common video formats: MP4, MOV, AVI
  - Maximum file size: 500MB (configurable)
  - Video duration limit: 5 minutes
  - Generate unique file identifiers (UUID-based)

**Video Segmentation Service**
- **Keyframe Extraction:**
  - Extract 1 keyframe every 2-5 seconds
  - Use FFmpeg: `ffmpeg -i input.mp4 -vf "fps=1/3" keyframe_%04d.jpg`
  - Store keyframes in temporary cloud storage
- **Audio Extraction:**
  - Extract audio track: `ffmpeg -i input.mp4 -vn -acodec copy output.aac`
  - Generate transcript using Whisper or Google Speech-to-Text
  - Store transcript as JSON with timestamps

**Gemini Multimodal Analysis Service**
- **API Endpoint:** `gemini-1.5-pro` (or `gemini-1.5-flash` for faster processing)
- **Input Format:**
  - Video file (direct upload to Gemini API)
  - OR: Keyframe images + audio transcript (multimodal prompt)
- **Processing Strategy:**
  - Two-stage approach: Category detection → Feature extraction
  - Use Function Calling / Structured Output for JSON schema enforcement
- **Rate Limits:** Respect Gemini API rate limits (60 requests/minute for free tier)

**Data Validation Service**
- **Schema Validation:** Use Pydantic models for each category type
- **Error Handling:** Return validation errors with specific field-level feedback
- **Transformation:** Convert validated data to supermemeory.ai expected format

**supermemeory.ai Integration Service**
- **Authentication:** API key-based authentication
- **Data Format:** JSON payload with structured content
- **Retry Logic:** Exponential backoff for failed requests (max 3 retries)

### 5. Data Models and Schemas

#### 5.1 Base Schema Structure

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class BaseExtraction(BaseModel):
    """Base model for all extraction types"""
    category: Literal["workout", "recipe", "travel", "product", "educational", "music"]
    title: str
    description: str
    source_url: Optional[str] = None
    extracted_at: datetime
    confidence_score: float = Field(ge=0.0, le=1.0)
```

#### 5.2 Category-Specific Schemas

**Workout Schema:**
```python
class Exercise(BaseModel):
    name: str
    sets: Optional[int] = None
    reps: Optional[int] = None
    duration_seconds: Optional[int] = None
    rest_seconds: Optional[int] = None

class WorkoutRoutine(BaseExtraction):
    category: Literal["workout"] = "workout"
    exercises: List[Exercise]
    total_rounds: Optional[int] = None
    estimated_duration_minutes: float
    difficulty_level: Literal["beginner", "intermediate", "advanced"]
    music_tempo_bpm: Optional[int] = None
```

**Recipe Schema:**
```python
class Ingredient(BaseModel):
    name: str
    quantity: str  # e.g., "2 cups", "1 tbsp"
    notes: Optional[str] = None

class RecipeStep(BaseModel):
    step_number: int
    instruction: str
    duration_minutes: Optional[float] = None
    utensils: List[str] = []

class RecipeCard(BaseExtraction):
    category: Literal["recipe"] = "recipe"
    ingredients: List[Ingredient]
    steps: List[RecipeStep]
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    servings: Optional[int] = None
    cuisine_type: Optional[str] = None
```

**Travel Schema:**
```python
class Activity(BaseModel):
    name: str
    location: str
    google_maps_link: Optional[str] = None
    booking_link: Optional[str] = None
    estimated_duration_hours: Optional[float] = None

class TravelItinerary(BaseExtraction):
    category: Literal["travel"] = "travel"
    destination: str
    activities: List[Activity]
    day_breakdown: Optional[List[dict]] = None  # Day-by-day activities
    estimated_budget: Optional[str] = None
```

**Product Schema:**
```python
class Product(BaseModel):
    name: str
    brand: Optional[str] = None
    price: Optional[str] = None
    currency: Optional[str] = None
    purchase_links: List[str] = []  # Amazon, brand website, etc.
    product_category: Optional[str] = None

class ProductCatalog(BaseExtraction):
    category: Literal["product"] = "product"
    products: List[Product]
```

**Educational Schema:**
```python
class TutorialStep(BaseModel):
    step_number: int
    description: str
    tools_required: List[str] = []
    resource_links: List[str] = []

class TutorialSummary(BaseExtraction):
    category: Literal["educational"] = "educational"
    topic: str
    steps: List[TutorialStep]
    prerequisites: List[str] = []
    estimated_time_minutes: Optional[int] = None
```

**Music Schema:**
```python
class SongMetadata(BaseExtraction):
    category: Literal["music"] = "music"
    song_title: Optional[str] = None
    artist: Optional[str] = None
    genre: Optional[str] = None
    lyrics_snippet: Optional[str] = None
    spotify_link: Optional[str] = None
    youtube_link: Optional[str] = None
    mood: Optional[str] = None
```

### 6. API Specifications

#### 6.1 Internal API Structure

**Main Processing Endpoint:**
```python
POST /api/v1/extract
Content-Type: application/json

Request Body:
{
    "source": "url" | "file",
    "input": "https://instagram.com/reel/..." | "/path/to/video.mp4",
    "preferred_category": "auto" | "workout" | "recipe" | ...,
    "options": {
        "extract_audio": true,
        "keyframe_interval": 3,  # seconds
        "include_transcript": true
    }
}

Response:
{
    "job_id": "uuid",
    "status": "processing" | "completed" | "failed",
    "estimated_completion_time": "2024-01-01T12:00:00Z"
}
```

**Status Check Endpoint:**
```python
GET /api/v1/extract/{job_id}

Response:
{
    "job_id": "uuid",
    "status": "processing" | "completed" | "failed",
    "progress": 0.75,
    "result": { ... } | null,
    "error": { "message": "...", "code": "..." } | null
}
```

#### 6.2 supermemeory.ai Integration API

**Expected Payload Format:**
```python
POST https://api.supermemeory.ai/v1/memories
Headers:
    Authorization: Bearer {api_key}
    Content-Type: application/json

Body:
{
    "title": "Workout Routine: HIIT Training",
    "content": { ... },  # Category-specific schema
    "category": "workout",
    "tags": ["fitness", "hiit", "exercise"],
    "metadata": {
        "source_url": "...",
        "extracted_at": "2024-01-01T12:00:00Z"
    }
}
```

### 7. Processing Flow Requirements (Technical)

The system flow must leverage the specific capabilities of the Gemini Stack to transform raw video data into structured outputs.

#### 7.1 Multimodal Ingestion Pipeline

1. **Video Upload to Gemini:**
   - Use `google-generativeai` SDK: `genai.upload_file(path="video.mp4")`
   - Handle file size limits (Gemini 1.5 Pro supports up to 2M tokens)
   - For large videos: Use segmented approach with keyframes

2. **Alternative: Keyframe + Transcript Approach:**
   - Extract keyframes (1 per 2-5 seconds)
   - Generate audio transcript with timestamps
   - Create multimodal prompt combining:
     - Keyframe images (base64 encoded or file references)
     - Audio transcript text
     - Structured output schema

#### 7.2 File Segmentation Implementation

**Keyframe Extraction:**
```python
import ffmpeg

def extract_keyframes(video_path: str, interval: int = 3) -> List[str]:
    """Extract keyframes every N seconds"""
    output_pattern = f"keyframe_%04d.jpg"
    ffmpeg.input(video_path).filter('fps', fps=1/interval).output(
        output_pattern
    ).run()
```

**Audio Extraction & Transcription:**
```python
def extract_and_transcribe_audio(video_path: str) -> dict:
    """Extract audio and generate transcript"""
    audio_path = extract_audio(video_path)
    transcript = whisper_model.transcribe(audio_path)
    return {
        "text": transcript["text"],
        "segments": transcript["segments"]  # With timestamps
    }
```

#### 7.3 Structured Output Definition

**Gemini Function Calling / Structured Output:**
```python
from google.generativeai import GenerativeModel
import google.generativeai as genai

# Define schema using Gemini's function calling
workout_schema = {
    "name": "extract_workout_routine",
    "description": "Extract workout routine from video",
    "parameters": {
        "type": "object",
        "properties": {
            "exercises": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "sets": {"type": "integer"},
                        "reps": {"type": "integer"},
                        "duration_seconds": {"type": "integer"},
                        "rest_seconds": {"type": "integer"}
                    }
                }
            },
            # ... more properties
        },
        "required": ["exercises"]
    }
}

model = GenerativeModel('gemini-1.5-pro')
response = model.generate_content(
    video_file,
    generation_config={
        "response_mime_type": "application/json",
        "response_schema": workout_schema
    }
)
```

#### 7.4 Final Storage and Retrieval

**supermemeory.ai Integration:**
```python
import httpx

async def store_in_supermemeory(data: dict, api_key: str):
    """Store extracted data in supermemeory.ai"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.supermemeory.ai/v1/memories",
            headers={"Authorization": f"Bearer {api_key}"},
            json=data,
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
```

### 8. Error Handling and Resilience

#### 8.1 Error Categories

1. **Download Errors:**
   - Invalid URL format
   - Network timeouts
   - Unsupported video platform
   - File size exceeds limits

2. **Processing Errors:**
   - Video format not supported
   - Gemini API rate limits exceeded
   - Invalid video content (corrupted file)
   - Audio extraction failures

3. **Analysis Errors:**
   - Gemini API failures
   - Schema validation failures
   - Category detection ambiguity

4. **Storage Errors:**
   - supermemeory.ai API failures
   - Authentication errors
   - Network connectivity issues

#### 8.2 Retry Strategy

- **Exponential Backoff:** For transient failures (API rate limits, network issues)
- **Max Retries:** 3 attempts with backoff: 1s, 2s, 4s
- **Permanent Failures:** Log and return error to user immediately

#### 8.3 Error Response Format

```python
{
    "error": {
        "code": "PROCESSING_FAILED",
        "message": "Failed to extract audio from video",
        "details": {
            "step": "audio_extraction",
            "original_error": "..."
        },
        "retryable": true
    }
}
```

### 9. Performance Requirements

#### 9.1 Processing Time Targets

- **Video Download:** < 30 seconds (for typical reel size ~50MB)
- **Keyframe Extraction:** < 10 seconds
- **Audio Transcription:** < 60 seconds (for 5-minute video)
- **Gemini Analysis:** < 90 seconds (depends on video length)
- **Total End-to-End:** < 5 minutes for typical reel

#### 9.2 Resource Constraints

- **Memory:** Maximum 4GB RAM usage per processing job
- **Storage:** Temporary files cleaned up after 24 hours
- **API Rate Limits:** Respect Gemini API quotas (60 req/min free tier)

#### 9.3 Scalability Considerations

- **Async Processing:** Use asyncio for concurrent API calls
- **Job Queue:** Optional Celery integration for background processing
- **Caching:** Cache category detection results for similar videos

### 10. Security and Privacy

#### 10.1 API Key Management

- Store API keys in environment variables (`.env` file)
- Never commit API keys to version control
- Use secret management service in production (AWS Secrets Manager, GCP Secret Manager)

#### 10.2 Data Privacy

- **Temporary Storage:** Delete video files after processing completion
- **Cloud Storage:** Use signed URLs with expiration (24 hours)
- **API Communication:** Use HTTPS for all external API calls
- **Data Retention:** Store only extracted structured data, not raw video

#### 10.3 Input Validation

- Validate video file formats before processing
- Sanitize URLs to prevent SSRF attacks
- Limit file size to prevent DoS attacks

### 11. Development Environment Setup

#### 11.1 Required Dependencies

```txt
# requirements.txt
google-generativeai>=0.3.0
google-cloud-storage>=2.10.0
ffmpeg-python>=0.2.0
opencv-python>=4.8.0
openai-whisper>=20231117
pydantic>=2.0.0
httpx>=0.25.0
python-dotenv>=1.0.0
asyncio>=3.4.3
```

#### 11.2 Environment Variables

```bash
# .env.example
GEMINI_API_KEY=your_gemini_api_key
SUPERMEMEORY_API_KEY=your_supermemeory_api_key
GOOGLE_CLOUD_STORAGE_BUCKET=your_bucket_name
GOOGLE_CLOUD_PROJECT_ID=your_project_id
MAX_VIDEO_SIZE_MB=500
KEYFRAME_INTERVAL_SECONDS=3
```

#### 11.3 Local Development Setup

1. Install FFmpeg: `brew install ffmpeg` (macOS) or `apt-get install ffmpeg` (Linux)
2. Install Python dependencies: `pip install -r requirements.txt`
3. Set up environment variables: `cp .env.example .env` and fill in values
4. Run local server: `python main.py`

### 12. Testing Requirements

#### 12.1 Unit Tests

- Test each extraction category schema validation
- Test video segmentation functions
- Test API client error handling

#### 12.2 Integration Tests

- Test end-to-end flow with sample video files
- Test supermemeory.ai integration (mock or sandbox)
- Test Gemini API integration with test videos

#### 12.3 Test Data

- Maintain sample videos for each category (workout, recipe, travel, etc.)
- Test edge cases: corrupted files, unsupported formats, very short/long videos

---

The process essentially turns chaotic, saved content into a highly structured database of actionable information, making the saved reels immediately useful, much like a meticulous librarian who sorts and indexes every item you throw into your "to read later" pile.