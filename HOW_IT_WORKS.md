# How the Code Works - Brief Overview

## 🎯 High-Level Flow

```
Instagram URL → Download → Segment → Analyze → Validate → Store
```

## 📋 Step-by-Step Process

### 1. **Entry Point** (`main.py`)
- User provides Instagram URL or local video file
- `ReelExtractor` class orchestrates the entire process

### 2. **Video Download** (`src/services/video_downloader.py`)
- Uses `yt-dlp` to download video from Instagram
- Validates file format and size
- Saves to `temp_storage/` with unique filename

### 3. **Video Segmentation** (`src/services/video_segmenter.py`)
- **Keyframes**: FFmpeg extracts 1 frame every 3 seconds
- **Audio**: FFmpeg extracts audio track
- **Transcription**: Whisper transcribes audio (optional, slow)

### 4. **AI Analysis** (`src/services/gemini_analyzer.py`)
- **Category Detection**: Gemini analyzes video to detect type (workout/recipe/travel/etc.)
- **Data Extraction**: 
  - Uploads video + keyframes to Gemini
  - Uses JSON Schema to enforce structure
  - Returns structured JSON matching Pydantic models

### 5. **Data Validation** (`src/models/*.py`)
- Pydantic models validate the JSON response
- Ensures all required fields are present
- Type checking and constraints

### 6. **Storage** (`src/services/supermemeory_client.py`)
- Stores extracted data in supermemeory.ai
- Generates tags based on category
- Returns confirmation

## 🔑 Key Components

### **Data Models** (`src/models/`)
- Define structure for each category (workout, recipe, travel, etc.)
- Pydantic models with validation
- Convert to JSON Schema for Gemini

### **Services** (`src/services/`)
- **VideoDownloader**: Downloads videos
- **VideoSegmenter**: Extracts keyframes/audio
- **GeminiAnalyzer**: AI analysis with structured output
- **SupermemeoryClient**: Stores results

### **Configuration** (`src/utils/config.py`)
- Loads API keys from `.env`
- Manages settings (file sizes, intervals, etc.)

## 🧠 How Gemini Structured Output Works

1. **Pydantic Model** defines structure:
   ```python
   class WorkoutRoutine(BaseExtraction):
       exercises: List[Exercise]
       difficulty_level: Literal["beginner", "intermediate", "advanced"]
   ```

2. **Convert to JSON Schema**:
   ```python
   json_schema = WorkoutRoutine.model_json_schema()
   ```

3. **Pass to Gemini**:
   ```python
   generation_config = GenerationConfig(
       response_mime_type="application/json",
       response_schema=json_schema  # Enforces structure!
   )
   ```

4. **Gemini returns** JSON matching the schema exactly

5. **Validate with Pydantic**:
   ```python
   instance = WorkoutRoutine(**json_data)  # Validates types, required fields
   ```

## 🔄 Complete Flow Example

**Input**: `https://instagram.com/reel/ABC123/`

1. **Download**: `yt-dlp` downloads → `temp_storage/xyz.mp4`
2. **Segment**: 
   - Extract 10 keyframes → `temp_storage/keyframes_xyz/`
   - Extract audio → `temp_storage/xyz.aac`
3. **Analyze**:
   - Upload video + keyframes to Gemini
   - Gemini detects: "workout" category
   - Gemini extracts: exercises, sets, reps, duration
   - Returns JSON matching `WorkoutRoutine` schema
4. **Validate**: Pydantic validates JSON → creates `WorkoutRoutine` object
5. **Store**: Send to supermemeory.ai → saved!

## ⚡ Performance Bottlenecks

1. **Audio Transcription** (1-5 min) - CPU intensive, optional
2. **Gemini Analysis** (30-90 sec) - Network upload + AI processing
3. **Keyframe Extraction** (10-30 sec) - FFmpeg processing

## 🎨 Architecture Pattern

- **Separation of Concerns**: Each service has one responsibility
- **Dependency Injection**: Services are initialized and passed around
- **Error Handling**: Each step returns (result, error) tuples
- **Validation**: Pydantic ensures data integrity
- **Configuration**: Centralized in Config class

## 💡 Key Design Decisions

1. **Pydantic Models**: Type safety and validation
2. **JSON Schema**: Enforces structure at AI generation time
3. **Optional Transcription**: Can skip for speed
4. **Fallback Models**: Tries multiple Gemini models
5. **Graceful Degradation**: Continues even if some steps fail

