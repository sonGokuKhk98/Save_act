# Actify - Multimodal Reel Intelligence Platform

Transform short-form videos into structured, searchable, actionable knowledge.

## What It Does

Actify turns Instagram Reels into intelligent, structured data:

- **Ingest**: Download videos from Instagram/TikTok/YouTube Shorts
- **Analyze**: Extract structured JSON using Google Gemini (category-aware)
- **Store**: Save to Supermemory.ai with searchable keyframes
- **Act**: Guided workouts, recipes, travel plans, product search with Google Lens

## Key Features

### Smart Extraction
- **6 Categories**: Workout, Recipe, Travel, Product, Educational, Music
- **Multimodal AI**: Analyzes video, keyframes, and audio transcripts
- **Adaptive Density**: Dynamic keyframe extraction based on video length

### Agentic Intelligence
- **Agentic Enhance**: AI-powered summaries with actionable suggestions
- **AI Reconstruct**: Rich narrative generation from messy data
- **Category-Aware**: Different intelligence strategies per content type

### Workflow Tools
- **Guided Workout Timer**: Real-time exercise tracking with customizable sets/reps
- **Google Lens Integration**: Visual product search with buy links (SerpApi)
- **Smart Browse**: Category-grouped reels with thumbnails and summaries
- **Semantic Search**: Find saved reels by meaning, not keywords

## Architecture

```
Reel URL → FastAPI Backend
           ↓
    ┌──────┴──────┐
    │ VideoDownloader (yt-dlp)
    │ VideoSegmenter (ffmpeg)
    │ GeminiAnalyzer (Gemini 2.5)
    │ Supermemory Storage
    └──────┬──────┘
           ↓
    Tailwind UI + Agentic Features
```

**Stack**: FastAPI · Gemini 2.5 Pro/Flash · LangGraph · FFmpeg · Supermemory.ai · SerpApi

## Quick Start

### Prerequisites
- Python 3.11+
- FFmpeg: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux)

### Install
```bash
git clone <repo>
cd Act
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure
Create `.env`:
```bash
GEMINI_API_KEY=your_key
SUPERMEMORY_API_KEY=your_key
SERPAPI_API_KEY=your_key  # Optional, for Google Lens
```

### Run
```bash
uvicorn api_main:app --reload
```

Open: `http://127.0.0.1:8000/reel-input`

## Usage Flow

1. **Submit** → Paste reel URL at `/reel-input`
2. **Process** → Watch progress at `/processing-status`
3. **View** → Structured data at `/generic-view`
4. **Enhance** → Click "Agentic Enhance" for AI insights
5. **Act** → Start workout, copy recipe, find products, etc.

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/reels/submit` | Submit reel for processing |
| `GET /api/reels/status/{task_id}` | Check processing status |
| `GET /api/reels/search` | Semantic search saved reels |
| `GET /api/reels/recent` | Browse recent reels |
| `GET /api/agents/intelligence-plan/{id}` | Agentic enhancement |
| `GET /api/agents/reconstruct/{id}` | AI reconstruction |
| `GET /api/products/lens/{id}` | Google Lens product search |

## Project Structure

```
Act/
├── api_main.py                 # FastAPI entrypoint
├── main.py                     # Core extraction orchestrator
├── src/
│   ├── api/                    # API routers
│   │   ├── reels.py           # Core reel operations
│   │   ├── agent_actions.py   # Agentic features
│   │   └── product_lens.py    # Google Lens integration
│   ├── services/               # Business logic
│   │   ├── gemini_analyzer.py # AI extraction
│   │   ├── video_downloader.py
│   │   ├── video_segmenter.py
│   │   └── supermemeory_client.py
│   ├── models/                 # Pydantic schemas
│   └── utils/                  # Config, helpers
└── public/                     # Frontend HTML/JS
    ├── reel-input.html
    ├── generic-view.html
    ├── browse-reels.html
    └── processing-status.html
```

## Key Technologies

- **AI/ML**: Google Gemini 2.5 Pro/Flash, LangGraph, LangChain
- **Backend**: FastAPI, Pydantic, yt-dlp, FFmpeg
- **Storage**: Supermemory.ai (vector search + metadata)
- **Frontend**: Tailwind CSS, Vanilla JS
- **APIs**: SerpApi (Google Lens)

## Extending

### Add New Category
1. Define Pydantic model in `src/models/`
2. Add extractor in `src/services/gemini_analyzer.py`
3. Update UI renderer in `public/generic-view.html`

### Custom Agentic Actions
1. Add endpoint in `src/api/agent_actions.py`
2. Wire button in `public/generic-view.html`
3. Define prompt strategy per category

## Deployment

### Production Considerations
- **Backend**: Deploy to Render/Railway (FastAPI + workers)
- **Frontend**: Static HTML to Vercel/Netlify
- **Secrets**: Use Render Secret Files for cookies
- **Cleanup**: Auto-deletes temp files (videos/keyframes) after processing
- **Scaling**: Background tasks for async video processing

### Instagram Authentication
For reliable Instagram downloads, add cookies via Render Secret Files:
```bash
# Upload instagram_cookies.txt to /etc/secrets/
# Include sessionid cookie from logged-in session
```

## Limitations

- **In-Memory Cache**: Server restart loses task state
- **Single User**: No auth/multi-tenancy
- **Rate Limits**: Instagram requires authenticated cookies
- **Model Quota**: Gemini quota exceeded → auto-fallback to Flash

## Troubleshooting

| Issue | Fix |
|-------|-----|
| FFmpeg not found | `brew install ffmpeg` |
| Gemini quota exceeded | System auto-falls back to Flash models |
| Instagram rate limit | Add cookies via Secret Files or use throwaway account |
| Module not found | `pip install -r requirements.txt` |

## License

MIT

## Built For

Google AI Hackathon - Gemini Multimodal Intelligence Challenge
