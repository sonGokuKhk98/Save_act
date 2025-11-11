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

### 4. Processing Flow Requirements

The system flow must leverage the specific capabilities of the Gemini Stack to transform raw video data into structured outputs.

1.  **Multimodal Ingestion:** The solution must be capable of directly feeding the downloaded video files or segmented video data (keyframes, audio transcripts) into the Gemini model.
2.  **File Segmentation:** The backend (Python) must handle file splitting, separating audio and video components for detailed analysis (e.g., using specialized audio libraries alongside Gemini).
3.  **Structured Output Definition:** System prompts must be meticulously defined to ensure the output is highly constrained (e.g., using a **JSON schema**) to contain specific actionable fields, such as "timers & rest periods" or "map links".
4.  **Final Storage and Retrieval:** The final, structured output is transmitted to and stored within **supermemeory.ai**.

The process essentially turns chaotic, saved content into a highly structured database of actionable information, making the saved reels immediately useful, much like a meticulous librarian who sorts and indexes every item you throw into your "to read later" pile.