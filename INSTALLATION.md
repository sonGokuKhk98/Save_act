# Installation Guide

## Prerequisites

- Python 3.9 or higher
- pip package manager
- Virtual environment (recommended)

## Setup Steps

### 1. Clone the Repository

```bash
cd /Users/tanzeel.shaikh/Sources/Projects/Save_act
```

### 2. Create Virtual Environment (if not already created)

```bash
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Additional System Dependencies

#### FFmpeg (for video processing)

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Gemini API Key (required for agent flow)
GEMINI_API_KEY=your_gemini_api_key_here

# Supermemory API Key (required for search and storage)
SUPERMEMORY_API_KEY=your_supermemory_api_key_here

# Instagram Access Token (optional - for real-time metrics)
# If not set, will use web scraping fallback
INSTAGRAM_ACCESS_TOKEN=your_instagram_token_here
```

**Note**: Instagram access token is optional. Without it, the system will use web scraping to fetch basic metrics. For comprehensive metrics from your own Instagram Business account, see `INSTAGRAM_API_SETUP.md`.

### 6. Verify Installation

Test the agent flow module:

```bash
python src/services/reel_intelligence_agent.py
```

Expected output:
```
Reel Intelligence Agent Flow Module

Agent Flow:
  [0] Reel Context Builder
  [1] Gemini Content Understanding
  [2] Trust Score Calculator
  [3] Type-Specific Enrichment
  [4] Orchestrator

Use generate_reel_intelligence() to process a reel.
```

### 7. Run the Streamlit App

```bash
streamlit run streamlit_search.py
```

The app should open in your browser at `http://localhost:8501`

## Troubleshooting

### Import Errors for LangGraph

If you see import errors for `langgraph` or `langchain`:

```bash
pip install --upgrade langgraph langchain langchain-core langchain-google-genai
```

### Gemini API Issues

Make sure your Gemini API key is valid:
- Get a key from: https://makersuite.google.com/app/apikey
- Ensure it's properly set in your `.env` file

### Supermemory API Issues

Verify your Supermemory API key:
- Get a key from: https://supermemory.ai
- Check that it's correctly configured in `.env`

### FFmpeg Not Found

If video processing fails:
- Ensure FFmpeg is installed and in your PATH
- Test with: `ffmpeg -version`

## Optional Dependencies

### For Development

```bash
pip install pytest black flake8 mypy
```

### For Production

```bash
pip install gunicorn  # For serving the app
```

## Next Steps

1. **Search for Reels**: Use the search interface to find saved reels
2. **View Details**: Click on any result to see detailed information
3. **Generate Intelligence**: Click "🤖 Generate Agentic Flow" to run the multi-agent system
4. **Explore Results**: Review trust scores, content analysis, and type-specific enrichments

## Support

For issues or questions, please refer to:
- Main README: `README.md`
- Agent Flow Documentation: `AGENT_FLOW.md`
- User Flow Diagram: `USER_FLOW_DIAGRAM.md`

