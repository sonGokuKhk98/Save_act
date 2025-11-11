# Complete Code Execution Flow

## 🚀 Entry Point

**File**: `main.py` or `test_instagram.py`

```python
# User runs: python test_instagram.py "https://instagram.com/reel/ABC123/"

extractor = ReelExtractor()  # ← Initialization happens here
result = extractor.extract(
    input_source="https://instagram.com/reel/ABC123/",
    source_type="url"
)
```

---

## 📍 Step 0: Initialization

**File**: `main.py` lines 22-30

```python
def __init__(self):
    Config.validate()                    # ← Check API keys exist
    Config.ensure_temp_storage()         # ← Create temp_storage/ directory
    
    self.downloader = VideoDownloader()  # ← Initialize downloader
    self.segmenter = VideoSegmenter()    # ← Initialize segmenter
    self.analyzer = GeminiAnalyzer()     # ← Initialize analyzer (loads Gemini model)
    self.storage = SupermemeoryClient()  # ← Initialize storage client
```

**What happens:**
1. Validates `.env` has API keys
2. Creates `temp_storage/` directory
3. Initializes all 4 services

---

## 📥 Step 1: Video Download

**File**: `main.py` lines 64-72

```python
# Step 1: Download/Process video
print("📥 Step 1: Processing video...")
video_path, error = self.downloader.process(input_source, source_type)
```

**Calls**: `src/services/video_downloader.py` line 145

```python
def process(self, input_source: str, source_type: str = "file"):
    if source_type == "url":
        return self.download_from_url(input_source)  # ← Goes here for Instagram URL
```

**Then**: `video_downloader.py` lines 27-108

```python
def download_from_url(self, url: str):
    import yt_dlp
    
    # Generate unique filename
    unique_filename = generate_unique_filename("video", ".mp4")
    # → Returns: "a2ca0686-1b9e-4d1f-b824-a54d836f46ff.mp4"
    
    temp_path = get_temp_file_path(unique_filename)
    # → Returns: Path("temp_storage/a2ca0686-1b9e-4d1f-b824-a54d836f46ff.mp4")
    
    # Configure yt-dlp
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': str(temp_path.with_suffix('')),  # Without .mp4 extension
    }
    
    # Download video
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])  # ← Downloads video from Instagram
    
    # Find downloaded file (yt-dlp might add extension)
    # Checks: temp_path, temp_path.with_suffix('.mp4'), etc.
    
    # Validate file
    is_valid, error = validate_video_file(downloaded_file)
    # → Checks: file exists, size < 500MB, is video format
    
    return downloaded_file, None  # ← Returns: (Path, None)
```

**Result**: 
- Video saved to: `temp_storage/a2ca0686-1b9e-4d1f-b824-a54d836f46ff.mp4`
- Returns: `(Path, None)` to `main.py`

---

## ✂️ Step 2: Video Segmentation

**File**: `main.py` lines 74-95

```python
# Step 2: Segment video (keyframes, audio)
print("✂️  Step 2: Segmenting video...")
segmentation = self.segmenter.segment_video(
    video_path,                    # ← Path from Step 1
    extract_keyframes=True,
    extract_audio=True,
    transcribe=False               # ← Skipped for speed
)
```

**Calls**: `src/services/video_segmenter.py` line 171

```python
def segment_video(self, video_path: Path, ...):
    result = {
        "keyframes": [],
        "audio_path": None,
        "transcript": None,
        "errors": []
    }
    
    # Extract keyframes
    if extract_keyframes:
        keyframes, error = self.extract_keyframes(video_path)  # ← Step 2a
```

### Step 2a: Extract Keyframes

**File**: `video_segmenter.py` lines 42-91

```python
def extract_keyframes(self, video_path: Path, interval_seconds: int = 3):
    # Create directory for keyframes
    keyframe_dir = get_temp_file_path(f"keyframes_{video_path.stem}")
    # → Returns: Path("temp_storage/keyframes_a2ca0686-1b9e-4d1f-b824-a54d836f46ff")
    
    keyframe_dir.mkdir(parents=True, exist_ok=True)  # ← Creates directory
    
    output_pattern = str(keyframe_dir / "keyframe_%04d.jpg")
    # → "temp_storage/keyframes_.../keyframe_%04d.jpg"
    
    # Run FFmpeg command
    cmd = [
        "ffmpeg",
        "-i", str(video_path),           # Input video
        "-vf", f"fps=1/{interval_seconds}",  # 1 frame per 3 seconds
        "-q:v", "2",                     # High quality
        output_pattern,
        "-y"                             # Overwrite
    ]
    
    subprocess.run(cmd, ...)  # ← Executes FFmpeg
    
    # Find all extracted keyframes
    keyframe_files = sorted(keyframe_dir.glob("keyframe_*.jpg"))
    # → Returns: [Path("keyframe_0001.jpg"), Path("keyframe_0002.jpg"), ...]
    
    return keyframe_files, None
```

**Result**: 
- Keyframes saved to: `temp_storage/keyframes_.../keyframe_0001.jpg`, etc.
- Returns: `([Path, Path, ...], None)`

### Step 2b: Extract Audio

**File**: `video_segmenter.py` lines 93-129

```python
def extract_audio(self, video_path: Path):
    audio_filename = generate_unique_filename(video_path.name, ".aac")
    # → Returns: "5b1da845-b249-4fb4-b54d-ad7f91ea550e.aac"
    
    audio_path = get_temp_file_path(audio_filename)
    # → Returns: Path("temp_storage/5b1da845-b249-4fb4-b54d-ad7f91ea550e.aac")
    
    # Run FFmpeg command
    cmd = [
        "ffmpeg",
        "-i", str(video_path),    # Input video
        "-vn",                     # No video (audio only)
        "-acodec", "copy",         # Copy audio codec
        str(audio_path),
        "-y"
    ]
    
    subprocess.run(cmd, ...)  # ← Executes FFmpeg
    
    return audio_path, None
```

**Result**:
- Audio saved to: `temp_storage/5b1da845-b249-4fb4-b54d-ad7f91ea550e.aac`
- Returns: `(Path, None)`

### Step 2c: Transcription (Optional, Skipped)

**File**: `video_segmenter.py` lines 131-169

```python
def transcribe_audio(self, audio_path: Path):
    import whisper
    model = whisper.load_model("base")  # ← Loads model (slow first time)
    result = model.transcribe(str(audio_path))  # ← Transcribes (CPU intensive)
    return {"text": result["text"], ...}, None
```

**Note**: Skipped by default for speed

**Back to**: `video_segmenter.py` line 171

```python
def segment_video(...):
    result = {
        "keyframes": [Path, Path, ...],  # ← From Step 2a
        "audio_path": Path,              # ← From Step 2b
        "transcript": None,               # ← Skipped
        "errors": []
    }
    return result  # ← Returns to main.py
```

**Result**: Returns dict with keyframes and audio paths

---

## 🤖 Step 3: Gemini AI Analysis

**File**: `main.py` lines 97-108

```python
# Step 3: Analyze with Gemini
print("🤖 Step 3: Analyzing with Gemini AI...")
transcript_text = None  # ← No transcript (skipped)

extraction, error = self.analyzer.analyze_video(
    video_path,                    # ← Path from Step 1
    keyframes=segmentation["keyframes"],  # ← List of keyframe paths
    transcript=transcript_text,     # ← None
    preferred_category=None         # ← Auto-detect
)
```

**Calls**: `src/services/gemini_analyzer.py` line 408

```python
def analyze_video(self, video_path, keyframes, transcript, preferred_category):
    # Detect category if not provided
    if not preferred_category:
        category, error = self.detect_category(video_path, keyframes, transcript)
        # ← Step 3a: Detect category first
```

### Step 3a: Category Detection

**File**: `gemini_analyzer.py` lines 59-100

```python
def detect_category(self, video_path, keyframes, transcript):
    categories = ["workout", "recipe", "travel", "product", "educational", "music"]
    
    prompt = """
    Analyze this video content and determine its category.
    Categories: workout, recipe, travel, product, educational, music
    Return ONLY the category name (one word).
    """
    
    # Build content for analysis
    content_parts = [prompt]
    
    # Add video if provided
    if video_path.exists():
        video_file = genai.upload_file(path=str(video_path))  # ← Uploads video
        content_parts.append(video_file)
    
    # Add keyframes if provided
    if keyframes:
        for keyframe_path in keyframes[:5]:  # ← First 5 keyframes only
            if Path(keyframe_path).exists():
                content_parts.append(genai.upload_file(path=str(keyframe_path)))
    
    # Generate response
    response = self.model.generate_content(content_parts)  # ← Calls Gemini API
    category = response.text.strip().lower()
    
    return category, None  # ← Returns: ("workout", None)
```

**Result**: Category detected (e.g., "workout")

### Step 3b: Extract Structured Data

**File**: `gemini_analyzer.py` lines 408-425

```python
def analyze_video(...):
    # After category detection...
    preferred_category = "workout"  # ← From Step 3a
    
    # Choose extractor based on category
    category_extractors = {
        "workout": self.extract_workout_routine,  # ← This one
        "recipe": self.extract_recipe,
        # ... etc
    }
    
    extractor = category_extractors["workout"]
    return extractor(video_path, keyframes, transcript)  # ← Calls workout extractor
```

**Calls**: `gemini_analyzer.py` lines 130-207

```python
def extract_workout_routine(self, video_path, keyframes, transcript):
    prompt = """
    Analyze this workout video and extract the complete workout routine.
    Extract: exercise names, sets, reps, durations, rest periods, etc.
    Return the data in JSON format.
    """
    
    return self._extract_structured_data(
        prompt,
        WorkoutRoutine,  # ← Pydantic model class
        video_path,
        keyframes,
        transcript
    )
```

### Step 3c: Structured Data Extraction

**File**: `gemini_analyzer.py` lines 328-406

```python
def _extract_structured_data(self, prompt, model_class, video_path, keyframes, transcript):
    # Build content for analysis
    content_parts = [prompt]
    
    # Add video
    if video_path.exists():
        video_file = genai.upload_file(path=str(video_path))  # ← Uploads video
        content_parts.append(video_file)
    
    # Add keyframes (up to 10)
    if keyframes:
        for keyframe_path in keyframes[:10]:
            if Path(keyframe_path).exists():
                content_parts.append(genai.upload_file(path=str(keyframe_path)))
    
    # Add transcript if available
    if transcript:
        content_parts.append(f"\nAudio Transcript:\n{transcript}")
    
    # Convert Pydantic model to JSON Schema
    json_schema = model_class.model_json_schema()  # ← Generates JSON Schema
    # → Returns: {
    #     "type": "object",
    #     "properties": {
    #         "category": {"type": "string", "enum": ["workout"]},
    #         "exercises": {"type": "array", "items": {...}},
    #         ...
    #     },
    #     "required": ["category", "title", "exercises", ...]
    # }
    
    # Configure Gemini for structured output
    generation_config = genai.types.GenerationConfig(
        response_mime_type="application/json",  # ← Must return JSON
        response_schema=json_schema             # ← Must match this schema
    )
    
    # Call Gemini API
    response = self.model.generate_content(
        content_parts,              # ← Video + keyframes + prompt
        generation_config=generation_config  # ← With schema enforcement
    )
    # ← This takes 30-90 seconds (network upload + AI processing)
    
    # Parse JSON response
    json_data = json.loads(response.text)
    # → Returns: {
    #     "category": "workout",
    #     "title": "HIIT Cardio Blast",
    #     "exercises": [
    #         {"name": "Squats", "sets": 3, "reps": 15, ...},
    #         ...
    #     ],
    #     ...
    # }
    
    # Add defaults for missing fields
    if model_class == WorkoutRoutine:
        if "estimated_duration_minutes" not in json_data:
            json_data["estimated_duration_minutes"] = 20.0
    
    # Validate and create Pydantic model instance
    instance = model_class(**json_data)  # ← Validates types, required fields
    # → Returns: WorkoutRoutine object
    
    return instance, None  # ← Returns: (WorkoutRoutine, None)
```

**Result**: 
- `WorkoutRoutine` object with validated data
- Returns to `main.py`

---

## 💾 Step 4: Store in Supermemeory.ai

**File**: `main.py` lines 118-129

```python
# Step 4: Store in supermemeory.ai
print("💾 Step 4: Storing in supermemeory.ai...")
storage_result, storage_error = self.storage.store_extraction(
    extraction,                    # ← WorkoutRoutine object from Step 3
    source_url=input_source       # ← Original Instagram URL
)
```

**Calls**: `src/services/supermemeory_client.py` lines 50-103

```python
def store_extraction(self, extraction: BaseExtraction, source_url: str):
    # Prepare payload
    payload = {
        "title": extraction.title,              # ← "HIIT Cardio Blast"
        "content": extraction.model_dump(),     # ← Full JSON data
        "category": extraction.category,       # ← "workout"
        "tags": self._generate_tags(extraction),  # ← ["workout", "intermediate"]
        "metadata": {
            "source_url": source_url,
            "extracted_at": extraction.extracted_at.isoformat(),
            "confidence_score": extraction.confidence_score
        }
    }
    
    # Use supermemory package
    if self.use_package:
        result = self.client.memories.create(**payload)  # ← Calls supermemory API
        return result, None
```

**Result**: Data stored in supermemeory.ai

---

## ✅ Final Result

**File**: `main.py` lines 131-132

```python
result["success"] = True
return result  # ← Returns to caller
```

**Result structure**:
```python
{
    "success": True,
    "extraction": WorkoutRoutine(...),  # ← Pydantic model instance
    "stored": True,
    "errors": [],
    "temp_files": [Path, Path, ...]     # ← Files to cleanup
}
```

---

## 📊 Complete Flow Diagram

```
User Input (Instagram URL)
    ↓
[main.py] ReelExtractor.__init__()
    ├─ Config.validate()
    ├─ VideoDownloader()
    ├─ VideoSegmenter()
    ├─ GeminiAnalyzer()  ← Loads Gemini model
    └─ SupermemeoryClient()
    ↓
[main.py] extract()
    ↓
[Step 1] video_downloader.py::download_from_url()
    ├─ yt_dlp.YoutubeDL().download()  ← Downloads video
    ├─ validate_video_file()          ← Validates
    └─ Returns: (Path, None)
    ↓
[Step 2] video_segmenter.py::segment_video()
    ├─ extract_keyframes()
    │   └─ subprocess.run(["ffmpeg", ...])  ← Extracts frames
    ├─ extract_audio()
    │   └─ subprocess.run(["ffmpeg", ...])  ← Extracts audio
    └─ Returns: {keyframes: [...], audio_path: Path}
    ↓
[Step 3] gemini_analyzer.py::analyze_video()
    ├─ detect_category()
    │   ├─ genai.upload_file(video)      ← Uploads video
    │   ├─ genai.upload_file(keyframes)  ← Uploads images
    │   └─ model.generate_content()      ← Gets category
    ├─ extract_workout_routine()
    │   ├─ model_class.model_json_schema()  ← Generates schema
    │   ├─ genai.upload_file(video + keyframes)
    │   ├─ model.generate_content(schema)  ← Gets structured JSON
    │   ├─ json.loads(response.text)       ← Parses JSON
    │   └─ WorkoutRoutine(**json_data)     ← Validates & creates object
    └─ Returns: (WorkoutRoutine, None)
    ↓
[Step 4] supermemeory_client.py::store_extraction()
    ├─ extraction.model_dump()           ← Converts to dict
    ├─ client.memories.create(payload)   ← Stores in API
    └─ Returns: (result, None)
    ↓
[main.py] Returns result dict
```

---

## 🔑 Key Code Patterns

### 1. **Error Handling Pattern**
```python
result, error = some_function()
if error:
    return None, error  # ← Early return on error
# Continue with result
```

### 2. **Service Initialization**
```python
class Service:
    def __init__(self):
        Config.validate()  # ← Validate config first
        # Initialize service
```

### 3. **Pydantic Validation**
```python
json_data = json.loads(response.text)  # ← Parse JSON
instance = ModelClass(**json_data)     # ← Validate & create object
```

### 4. **Structured Output**
```python
json_schema = model_class.model_json_schema()  # ← Generate schema
generation_config = GenerationConfig(
    response_mime_type="application/json",
    response_schema=json_schema  # ← Enforce structure
)
```

---

## ⏱️ Time at Each Step

1. **Download**: ~5 seconds (network dependent)
2. **Keyframes**: ~15 seconds (FFmpeg processing)
3. **Audio**: ~3 seconds (FFmpeg processing)
4. **Transcription**: ~45 seconds (if enabled, CPU intensive)
5. **Gemini Analysis**: ~60 seconds (upload + AI processing)
6. **Storage**: ~2 seconds (API call)

**Total**: ~1.5 minutes (without transcription) or ~2.5 minutes (with transcription)

