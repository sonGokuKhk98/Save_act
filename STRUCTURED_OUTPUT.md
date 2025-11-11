# How Structured Response is Defined

## Current Approach

Currently, we're using a **two-step approach**:

### 1. **Prompt-Based JSON Request**
In the prompt, we ask Gemini to return JSON:
```python
prompt = """
Analyze this workout video and extract the complete workout routine.

Extract:
- Exercise names
- Sets and reps
- Duration in seconds
...

Return the data in JSON format.
"""
```

### 2. **JSON Format Configuration**
We tell Gemini to return JSON:
```python
generation_config = genai.types.GenerationConfig(
    response_mime_type="application/json"  # Just tells it to return JSON
)
```

### 3. **Post-Validation with Pydantic**
After getting the response, we validate it:
```python
json_data = json.loads(response.text)  # Parse JSON
instance = model_class(**json_data)     # Validate with Pydantic
```

## Problem with Current Approach

❌ **No schema enforcement** - Gemini doesn't know the exact structure
❌ **Inconsistent responses** - May return missing fields or wrong types
❌ **Post-validation errors** - We catch errors after the fact
❌ **Manual defaults** - We have to add defaults manually

## Better Approach: JSON Schema

Gemini supports **structured output with JSON Schema**! This enforces the structure at generation time.

### How to Use JSON Schema

```python
# Convert Pydantic model to JSON Schema
json_schema = model_class.model_json_schema()

# Use it in generation config
generation_config = genai.types.GenerationConfig(
    response_mime_type="application/json",
    response_schema=json_schema  # Enforce structure!
)
```

## Current Code Location

The structured output is defined in:
- **File**: `src/services/gemini_analyzer.py`
- **Method**: `_extract_structured_data()` (line 328-402)
- **Current approach**: Lines 369-371

## Example: Workout Routine Schema

The structure is defined by the Pydantic model:

```python
class WorkoutRoutine(BaseExtraction):
    category: Literal["workout"] = "workout"
    exercises: List[Exercise]  # Required
    total_rounds: Optional[int]
    estimated_duration_minutes: Optional[float]
    difficulty_level: Literal["beginner", "intermediate", "advanced"]
    music_tempo_bpm: Optional[int]
```

This gets converted to JSON Schema automatically by Pydantic.

## Why It's Not Using Schema Yet

The current code only uses:
- `response_mime_type="application/json"` ✅
- But NOT `response_schema` ❌

This means Gemini returns JSON, but doesn't enforce the structure.

## How to Fix

We should add:
```python
json_schema = model_class.model_json_schema()
generation_config = genai.types.GenerationConfig(
    response_mime_type="application/json",
    response_schema=json_schema  # Add this!
)
```

This will:
✅ Enforce structure at generation time
✅ Ensure all required fields are present
✅ Validate types before response
✅ Reduce validation errors

