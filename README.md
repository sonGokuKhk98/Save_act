Multimodal AI Reel Intelligence Platform
========================================

This repository contains a full-stack prototype that turns short-form video reels
into structured, searchable, and actionable knowledge.

The system:

- Ingests short-form video (for example, an Instagram Reel URL).
- Downloads and segments the video into keyframes.
- Uses Google Gemini to infer a category and extract structured JSON.
- Stores both the extraction and keyframes in supermemory.ai.
- Provides a set of UI views and agentic tools to help you actually use what you saved:
  workouts, recipes, travel itineraries, products, tutorials, and more.

This document is intentionally detailed. It is meant to be a single place where
you can understand what the project does, how it is wired together, and how to
extend it during or after a hackathon.


Table of Contents
-----------------

1.  Concept and Motivation  
2.  End-to-End User Experience  
3.  High-Level Architecture  
4.  Backend Design  
5.  Frontend Design  
6.  Data Models and JSON Shapes  
7.  AI and Agentic Features  
8.  Installation and Local Setup  
9.  Running the System  
10. Troubleshooting and Common Errors  
11. Extending the System  
12. Project Status and Limitations  


1. Concept and Motivation
-------------------------

### The problem this solves

People constantly save reels for later:

- A workout they want to try.
- A recipe that looked great.
- A travel itinerary for an upcoming trip.
- A cool product setup or tutorial.

The reality is that most of those saved reels are never revisited. When users
do go back, the format is not ideal:

- Hard to skim and search.
- No clear extraction of structured fields.
- No way to quickly act on the information (for example, start a guided
  workout or view an itinerary).

### What this project provides

This repository implements a multimodal reel intelligence platform that:

- Turns a reel into a structured JSON object (category-aware).
- Stores it in supermemory.ai so you can search it later.
- Provides a generic view that adapts to the category and data quality.
- Augments that view with agentic features:
  - Agentic Enhance: more helpful summaries and suggested actions.
  - Agentic Reconstruct: a rich, human-readable narrative for messy data.
- Adds workflow-specific tools, such as:
  - A guided workout timer that uses the extracted exercises and sets.
  - Google Lens / SerpApi integration for product reels to find buy links.
  - A browse experience that groups saved reels by category and reminds you
    why they were saved.


2. End-to-End User Experience
-----------------------------

At a high level, the system exposes several UI screens backed by FastAPI.

### Reel Input (entry point)

Route: `/reel-input`  
Template: `src/models/UI elements/reel_input/code.html`

From here you can:

- Paste an Instagram reel URL.
- See a grid of recent reels pulled from supermemory.
- Use simple search to retrieve previously saved reels.
- Enter processing by clicking "Process Instagram Reel".
- Open the browse page by clicking an icon-only "Saved" button.

When you submit a reel URL:

1. The frontend calls `POST /api/reels/submit`.
2. The backend creates a background task that:
   - Downloads and validates the video.
   - Extracts keyframes using ffmpeg, with intervals chosen from the video
     duration (denser for shorter videos, sparser for longer).
   - Calls Gemini to analyze the content.
   - Normalizes and validates the JSON against Pydantic models.
   - Stores the result in supermemory.ai, linked to any keyframe documents.
3. You are redirected to `/processing-status?task_id=...`.

### Processing Status

Route: `/processing-status`  
Template: `src/models/UI elements/processing_status/code.html`

This view visualizes the lifecycle of the background task:

- A circular progress indicator that increments smoothly in one-percent steps.
- A four-step vertical checklist:
  1. Downloading video.
  2. Analyzing content with Gemini.
  3. Structuring key insights.
  4. Storing data.

The frontend polls `GET /api/reels/status/{task_id}` to obtain:

- `status`: queued, processing, completed, or failed.
- `stage`: a more granular label (downloading, segmenting, analyzing, storing,
  done, error).
- `progress`: integer from 0 to 100.
- `reel_id`: assigned when extraction finishes successfully.

When processing completes:

- The circular progress reaches 100.
- The checklist marks all steps as done.
- A confetti animation runs.
- The primary button switches to "Return to Reel Input" and routes back to
  `/reel-input`. The system no longer forces a redirect into the generic view.

If the `task_id` is unknown (for example, the server restarted), the UI
stops polling and shows a gentle "Session expired" message.

### Generic Extraction View

Route: `/generic-view`  
Template: `src/code.html`

This is the main "what did the AI extract?" screen. It can be reached by:

- Clicking a reel card in the search results.
- Clicking a reel card in the browse view.
- Following links that contain a `document_id` directly.

The generic view:

- Fetches extraction data either from:
  - The in-memory cache via `reel_id`, or
  - Supermemory directly via `document_id` using `/api/reels/document/{document_id}`.
- Sets up a global `window.__EXTRACTION__` object.
- Renders a category-aware layout that includes:
  - Sticky title row showing category, confidence, and a short tagline.
  - Visual context section with a keyframe thumbnail.
  - Key Items section (ingredients, products, exercises, activities).
  - Details section (servings, durations, difficulty, location, etc.).
  - Steps section (instructions, workout steps, how-to steps).
  - Additional Context section with AI-generated or reconstructed narrative.

It also performs normalization to cope with messy or inconsistent JSON:

- Converts character-split objects such as `{ "0": "F", "1": "l", ... }` into
  plain strings.
- Fills `raw.ingredients`, `raw.instructions`, `raw.items`, and
  `raw.servings` from `raw.additional_context` when those top-level fields
  are empty.
- Handles singular vs plural keys such as `product_names` versus
  `product_name`, and `brand_names` versus `brand_name`.
- Linkifies URLs and phone numbers in additional context.

On top of this baseline view, the page offers Agentic Enhance and AI
Reconstruct actions, described later.

### Guided Workout Timer

Route: `/extracted-view`  
Template: `src/models/UI elements/extracted_data_display_1/code.html`

This view turns a workout reel into a usable workout timer:

- Reads extracted exercises and associated metadata (sets, reps, durations).
- Let the user:
  - Choose time per exercise or per set.
  - Choose number of sets.
  - Ignore any AI estimates if they prefer.
- Provides explicit controls:
  - "Next Set" to move to the next set of the current exercise.
  - "Next Exercise" to jump to the next exercise.
- Loops through sets and exercises correctly while respecting user overrides.
- Works with both `reel_id` and `document_id` for retrieving JSON.

For workout reels, the Agentic Enhance panel simplifies the suggestions to a
single pathway: "Start workout" which routes directly to this guided timer.

### Browse Reels

Route: `/browse-reels`  
Template: `src/models/UI elements/browse_reels/code.html`

This view is designed to answer the question:

> "What have I saved recently, and why did I save it?"

Features:

- Groups saved reels by category (workout, recipe, product, travel, educational,
  music, and a generic bucket).
- Uses `/api/reels/recent` to pull:
  - Up to a safe number of recent documents from supermemory.
  - Rich metadata including:
    - Title.
    - Category.
    - Summary (if supermemory produced one).
    - Thumbnail:
      - Either from the text document metadata.
      - Or backfilled by searching for associated image documents (keyframes)
        with the same `customId`.
- Within each category section:
  - Shows cards with title, short summary, and thumbnail or a fallback icon.
  - Clicking a card opens the generic view for that document.


3. High-Level Architecture
--------------------------

Conceptually, the end-to-end flow looks like this:

    Reel URL
      |
      v
    FastAPI backend (submit endpoint)
      |
      |--- VideoDownloader: downloads media
      |--- VideoSegmenter: extracts keyframes, determines duration
      |--- GeminiAnalyzer: calls Gemini with keyframes and metadata
      |--- Validation: Pydantic models per category
      |--- Storage: supermemory.ai (text + images with shared customId)
      v
    Result stored
      |
      +-> UI: Reel Input / Browse / Generic View
      |
      +-> AI Agents:
             Agentic Enhance (intelligence plan)
             AI Reconstruct (rich narrative summary)

The main technologies involved are:

- FastAPI for HTTP APIs and HTML page routing.
- Google Gemini models via `langchain-google-genai`.
- LangGraph for orchestrating multi-step "intelligence plans".
- ffmpeg and ffprobe for video processing and keyframe extraction.
- supermemory.ai for storage and retrieval.
- Tailwind CSS (via CDN) for styling the HTML views.


4. Backend Design
-----------------

The backend is implemented primarily in:

- `api_main.py` (FastAPI application entrypoint).
- `src/api/` (request handlers and domain-specific APIs).
- `src/services/` (reusable service logic).
- `src/models/` (Pydantic models for structured data).
- `src/utils/` (configuration, helpers).

### API entrypoint: api_main.py

Responsibilities:

- Create the FastAPI app instance.
- Mount static routes for the HTML views:
  - `/reel-input`
  - `/processing-status`
  - `/generic-view`
  - `/browse-reels`
  - `/extracted-view`
- Mount `/temp` as a static route for serving locally stored keyframes from
  `temp_storage`.
- Include the routers:
  - `src/api/reels.py` (core operations).
  - `src/api/product_lens.py` (Google Lens).
  - `src/api/agent_actions.py` (Agentic Enhance and AI Reconstruct).

### Core router: src/api/reels.py

Key responsibilities:

- Simple in-memory stores:
  - `TASKS`: maps `task_id` to processing status.
  - `REELS`: caches recent extractions for quick access.

- Endpoints:

  - `POST /api/reels/submit`
    - Takes `instagram_url`.
    - Schedules a background extraction task.
    - Immediately returns:
      - `task_id`
      - `status`
      - Estimated time to completion.

  - `GET /api/reels/status/{task_id}`
    - Returns a `StatusResponse` with:
      - `status`
      - `stage`
      - `progress`
      - `reel_id` (after completion)
      - `error` (if any).

  - `GET /api/reels/{reel_id}`
    - Fetches a reel from the in-memory `REELS` dictionary.

  - `POST /api/reels/search`
    - Accepts:
      - `query`
      - `limit`
    - Calls supermemory search:
      - Filters to `type == "text"`.
      - Extracts titles, metadata, and scores.
      - For each result:
        - Uses text document metadata to get `thumbnail_url` if available.
        - If missing and `customId` is present:
          - Searches for image documents sharing the same `customId`.
          - Fetches those documents and uses their `url` or image metadata
            for thumbnails.
    - Returns a `SearchResponse` used by:
      - The Reel Input predictive search grid.

  - `GET /api/reels/recent`
    - Similar to search, but:
      - Uses a broad query (`q: "*"`) and a low `chunkThreshold`.
      - Sorts results by `extracted_at` descending.
      - Clamps the client-provided `limit` to avoid overloading upstream.
      - Uses the same thumbnail backfill based on `customId`.
    - Used by the browse view to group reels by category.

  - `GET /api/reels/document/{document_id}`
    - Fetches a text document by id from supermemory.
    - Reads its `metadata.customId`.
    - Runs another search for image documents sharing that `customId`.
    - Returns a combined response containing:
      - The main text document.
      - An array of keyframe image documents, each with metadata:
        - `url`
        - `title`
        - `summary`
        - `extracted_at`
        - `frame_index`

### Agent router: src/api/agent_actions.py

Main responsibilities:

- Provide higher-level AI experiences on top of the existing extraction.
- Reuse the same Gemini model selection logic used in the core analyzer,
  including:
  - Preferred models: `gemini-2.5-pro`, `gemini-2.5-flash`, and 2.0 variants.
  - Quota-aware fallback when a model returns `ResourceExhausted`.
- Ensure that:
  - `raw_data` is serialized safely (for example, dates via `default=str`).
  - Documents not in the in-memory `REELS` cache are fetched from supermemory
    on demand.

Exposed endpoints:

- `GET /api/agents/plan/{reel_id}`  
  Build a category-aware "enhancement plan" for the given reel.

- `GET /api/agents/product-plan/{reel_id}`  
  Legacy alias that delegates to the generic plan endpoint.

- `GET /api/agents/reconstruct/{document_id}`  
  Produce a reconstruction plan:
  - `heading`
  - `subtitle`
  - `rich_text`

- `GET /api/agents/intelligence-plan/{document_id}`  
  LangGraph-based intelligence plan that:
  - Runs one or more agents over the structured JSON.
  - Proposes:
    - A more human, high-signal heading and subtitle.
    - A set of bullet points summarizing the content.
    - Suggested actions the UI can render as buttons.

### Product Lens router: src/api/product_lens.py

Responsibilities:

- Implement `GET /api/products/lens/{reel_id}`:
  - Reads the reel from `REELS`.
  - Extracts the `thumbnail_url`, which points to a keyframe image.
  - Calls SerpApi’s `google_lens` engine with that URL.
  - Normalizes the result into:
    - `visual_matches`.
    - `product_matches`.
  - Returns a JSON payload for the UI.


5. Frontend Design
------------------

The UI is composed of static HTML files with inline JavaScript. Tailwind CSS is
included via CDN for rapid styling and iteration.

The main files live under `src/models/UI elements/` plus the generic view
(`src/code.html`).

### Reel Input

File: `reel_input/code.html`

- Sticky header with:
  - Icon at left.
  - Central title ("Reel Input") and subtitle.
  - Icon-only "Saved" button at right which opens `/browse-reels`.
- Search bar:
  - Calls `POST /api/reels/search` and displays a grid of result cards.
- Recent reels section:
  - On load, calls `GET /api/reels/recent?limit=8`.
  - Falls back to a gradient placeholder if no thumbnail is available.
- Reel URL field and "Process Instagram Reel" button:
  - On click, calls `POST /api/reels/submit`.
  - Redirects to `/processing-status?task_id=...`.

### Processing Status

File: `processing_status/code.html`

- Top app bar with "Processing Reel" and back button.
- Centered circular progress indicator, implemented using SVG arcs.
- Four-step vertical list with dynamic icons:
  - Pending, active (spinner), and done (checkmark) states.
- The primary button:
  - Initially "Cancel", wired as a placeholder.
  - After completion:
    - Text changes to "Return to Reel Input".
    - Clicking routes to `/reel-input`.

### Generic View

File: `src/code.html`

Key features from a UX perspective:

- Title row:
  - Category label and confidence pill.
  - Reel title (sticky).
  - Chips for status, category, and any relevant tags.
  - Buttons:
    - "Agentic Enhance" (pulsing to draw attention).
    - "Agentic Reconstruct" (glowing yellow).
- Summary paragraph below the title; scrolls with the content while the title
  stays fixed.
- Visual Context section:
  - Shows a keyframe image (or fallback).
  - Indicates that the AI is using this frame as an anchor.
- Primary structured sections:
  - Key Items: recipes, products, exercises, activities, etc.
  - Details: servings, difficulty, durations, location, etc.
  - Steps: instructions, sequences, routines.
  - Additional Context: raw or reconstructed narrative.
- Loading skeleton:
  - Title and sections show grey placeholders until the data loads and the
    hydration function finishes.

Category-specific touches:

- Product reels:
  - "Take Action" sheet includes:
    - Copy product list.
    - "Find similar products (Google Lens)", wired to `GET /api/products/lens/{reel_id}`.
  - Product parsing accounts for multiple key variants in `additional_context`.

- Travel reels:
  - Itinerary in `additional_context` is rendered as:
    - Day-by-day blocks (for example, "Day 5-6: Mt. Fuji Area").
    - Activities with Google Maps links.
    - Optional booking links.

- Workout reels:
  - Agentic Enhance suggestions are collapsed to a single "Start workout"
    action, to keep the call to action focused.

### Browse Reels

File: `browse_reels/code.html`

- Sticky top bar with:
  - Back arrow to `/reel-input`.
  - Title ("Browse Saved Reels").
  - Subtitle describing the purpose.
- Content:
  - On load, calls `GET /api/reels/recent?limit=50`.
  - Groups by category using a predefined category order.
  - For each category with results:
    - A heading line showing category name and number of reels.
    - A grid of cards:
      - Thumbnail.
      - Title.
      - Short explanation of why the reel was saved (based on summary).
  - Clicking a card opens `/generic-view?document_id=...`.


6. Data Models and JSON Shapes
------------------------------

The project uses Pydantic models under `src/models/` to describe the structured
schema for each category.

The base extraction model (`BaseExtraction` in `base.py`) typically contains:

- `category`: string, such as `workout`, `recipe`, `travel`, `product`,
  `educational`, `music`, or `generic`.
- `title`: human-readable title inferred from the reel.
- `description`: short summary.
- `confidence_score`: numeric estimate of the AI’s confidence.
- `source_url`: the original reel URL.
- `raw_data`: dictionary with the full category-specific payload.

Examples (simplified):

### Workout

```json
{
  "category": "workout",
  "title": "Full Body Dumbbell Routine",
  "description": "A 30-minute full body workout using a single pair of dumbbells.",
  "raw_data": {
    "exercises": [
      {
        "name": "Goblet Squat",
        "sets": 3,
        "reps": 12,
        "rest_seconds": 60
      }
    ]
  }
}
```

### Recipe

```json
{
  "category": "recipe",
  "title": "One-Pan Lemon Chicken Pasta",
  "raw_data": {
    "ingredients": [
      "200 g pasta",
      "2 chicken breasts",
      "1 lemon",
      "2 cloves garlic"
    ],
    "instructions": [
      "Boil pasta until al dente.",
      "Cook chicken in a pan.",
      "Add garlic and lemon juice."
    ],
    "servings": 2
  }
}
```

### Travel

```json
{
  "category": "travel",
  "title": "Japan Autumn Trip Highlights",
  "raw_data": {
    "itinerary": [
      {
        "day_range": "Day 5-6",
        "destination_location": "Mt. Fuji Area",
        "activities": [
          {
            "name": "Mount Fuji Viewpoint",
            "location": "Near Mount Fuji, Japan",
            "google_maps_link": "https://www.google.com/maps/place/Mount+Fuji"
          }
        ]
      }
    ]
  }
}
```

These shapes are what the generic UI uses when rendering category-specific
sections. The agentic features receive the same JSON as part of their prompt
context.


7. AI and Agentic Features
--------------------------

This project goes beyond simple extraction by layering in "agents" that reason
over the extracted JSON and propose better representations or actions.

### Agentic Enhance

Endpoint: `GET /api/agents/intelligence-plan/{document_id}`  
UI trigger: Agentic Enhance button in the generic view header.

Conceptually:

- The backend builds a system prompt that:
  - Describes the category (workout, recipe, etc.).
  - Explains what the extraction JSON contains.
  - Asks Gemini to produce:
    - A clearer heading.
    - A more user-friendly subtitle.
    - A short set of bullet points.
    - A set of suggested actions that can be rendered as buttons.
- The result is a "plan" object.

The frontend, via `applyAiPlan(plan)`:

- Updates the main title and summary if the current ones look generic.
- Shows a dedicated AI section with:
  - Heading and subtitle.
  - Bullet list of highlights.
  - Clickable suggested actions.
- Behaviors of suggested actions:
  - If the description looks like `URL: https://...`, clicking opens the link.
  - For travel suggestions, clicking may copy an itinerary summary to the
    clipboard.
  - For generic suggestions, clicking copies "label – description" so the user
    can paste it elsewhere.
- Once clicked:
  - The action button is visually marked as "applied".
  - The AI section flashes to indicate a change was applied.

### AI Reconstruct

Endpoint: `GET /api/agents/reconstruct/{document_id}`  
UI trigger: Agentic Reconstruct button in the generic view header; also invoked
automatically once after load.

Concept:

- Some reels have semi-structured or messy additional context.
- Instead of trying to fully re-normalize the JSON, the agent:
  - Receives all the structured data and additional context.
  - Produces a single, cohesive `rich_text` summary, plus optional updated
    `heading` and `subtitle`.

The frontend:

- Normalizes `rich_text` with `normalizeRichText()`:
  - Strips markdown bullet markers, stars, and heading symbols.
  - Preserves paragraphs and line breaks.
- Injects the result into the Additional Context section as:
  - A visually distinct block labeled "Agentic Reconstruction".
  - Optionally followed by a keyframe gallery reinserted below.
- Leaves Key Items, Details, and Steps untouched so structured sections are
  not lost.


8. Installation and Local Setup
-------------------------------

### Prerequisites

- Python 3.11 or later (the provided virtual environment targets 3.11).
- FFmpeg and ffprobe:
  - macOS: `brew install ffmpeg`.
  - Linux: `sudo apt-get install ffmpeg`.
- Network access to:
  - Google Gemini (via the Gemini API).
  - supermemory.ai.
  - SerpApi (for Google Lens).

### Clone and environment

From the project root (`Act/`):

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment variables

Create a `.env` file in the project root:

```bash
GEMINI_API_KEY=your_gemini_api_key_here

SUPERMEMORY_API_KEY=your_supermemory_api_key_here
SUPERMEMEORY_API_KEY=your_supermemory_api_key_here   # for backwards compatibility
SUPERMEMORY_BASE_URL=https://api.supermemory.ai/

SERPAPI_API_KEY=your_serpapi_api_key_here

MAX_VIDEO_SIZE_MB=500
KEYFRAME_INTERVAL_SECONDS=5
MAX_VIDEO_DURATION_MINUTES=5
TEMP_STORAGE_PATH=./temp_storage
CLEANUP_AFTER_HOURS=24
```

The `Config` class in `src/utils/config.py` validates that:

- `GEMINI_API_KEY` is defined.
- `SUPERMEMORY_API_KEY` (or the variant spelling) is defined.


9. Running the System
---------------------

To run the FastAPI app with hot reload:

```bash
uvicorn api_main:app --reload
```

Then open these URLs in a browser:

- `http://127.0.0.1:8000/reel-input` – main entrypoint.
- `http://127.0.0.1:8000/browse-reels` – browse saved reels.
- `http://127.0.0.1:8000/docs` – interactive API documentation.


10. Troubleshooting and Common Errors
-------------------------------------

This project interacts with several external services. Some common issues:

### FFmpeg not found

Symptom:

- Video processing fails early.

Resolution:

- macOS:

```bash
brew install ffmpeg
  ```

- Linux:

  ```bash
sudo apt-get install ffmpeg
```

### ModuleNotFoundError for langgraph or langchain_google_genai

Symptom:

- Imports fail when starting the server.

Resolution:

- Ensure you have installed all dependencies:

```bash
  pip install -r requirements.txt
  ```

### SERPAPI_API_KEY not configured

Symptom:

- The Google Lens action fails with a 500 error from `/api/products/lens/{reel_id}`.

Resolution:

- Obtain a key from SerpApi.
- Add `SERPAPI_API_KEY` to `.env`.
- Restart the FastAPI server.

### Gemini model not found or quota exceeded

Symptoms:

- Errors mentioning:
  - `models/gemini-1.5-flash` not found.
  - `ResourceExhausted: 429 You exceeded your current quota`.

Resolution:

- The agent layer already:
  - Uses new Gemini model names.
  - Falls back from pro to flash models when quota is exceeded.
- If all models fail:
  - Check your Gemini project configuration and billing.
  - Ensure the models you are calling are available for your account.

### "No extraction data found on window.__EXTRACTION__"

Symptom:

- Generic view shows an error in the console and fails to render content.

Resolution:

- This typically happens if the generic view is opened with an invalid or
  stale `document_id` or `reel_id`.
- Navigate to the generic view by:
  - Going through the Reel Input → Processing flow, or
  - Clicking from Browse or Search, which ensures a valid ID.

### "Document not in cache and SUPERMEMORY_API_KEY not configured"

Symptom:

- Agentic Enhance or AI Reconstruct fail for older reels not in the in-memory
  cache.

Resolution:

- Ensure `SUPERMEMORY_API_KEY` is present in `.env`.
- The router will then be able to fetch the document directly from supermemory.


11. Extending the System
------------------------

This project is designed as a hackable base for experimentation.

Ideas for extension:

### New categories

1. Add a new Pydantic model under `src/models/`.
2. Update the Gemini analyzer service to emit that schema.
3. Extend `src/code.html` to:
   - Recognize the new category.
   - Render any new fields in appropriate sections.

### Smarter product experiences

- Use the existing Product Lens endpoint and:
  - Build a modal that shows multiple visual matches.
  - Present best matches with images, prices, and "Buy" buttons.
  - Attach the keyframe image inline with the product list for context.

### Stronger browse experience

- Extend `browse_reels/code.html` to:
  - Show filters for time range (for example, "last 7 days").
  - Provide a secondary sort (for example, by category then date).
  - Include a "why I saved this" string derived purely from the AI summary.

### Persisting agentic changes

- Currently:
  - Agentic Enhance and AI Reconstruct update the in-memory extraction
    representation for the current session.
- You can extend this by:
  - Posting the updated title/description back to a new endpoint.
  - Creating a "version 2" document in supermemory that contains:
    - The original extraction.
    - The reconstructed rich text.
    - The intelligence plan.


12. Project Status and Limitations
----------------------------------

This repository is a prototype, not a hardened production service.

Some known constraints:

- In-memory stores:
  - `TASKS` and `REELS` are held in memory only.
  - Restarting the server loses in-flight tasks and cached extractions.

- Error handling:
  - Many external calls rely on best-effort retries at the client level
    rather than a robust retry/backoff strategy.

- Security and auth:
  - There is no authentication layer or per-user isolation.
  - All data is treated as belonging to a single logical user.

Despite these limitations, the architecture and pieces are intentionally
structured as you would in a larger system:

- Clear separation between API routers, services, and models.
- A generic but extensible extraction view.
- Agentic layers built on top of core structured data.
- External storage (supermemory.ai) that allows future retrieval-intensive
  workflows.

If you are using this as a base for a hackathon or prototype, you can focus on
your domain-specific ideas while relying on this project for the heavy lifting
of reel ingestion, analysis, and interaction.


