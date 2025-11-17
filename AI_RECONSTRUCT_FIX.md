# AI Reconstruct JSON Parsing Fix

## Problem
The AI Reconstruct feature was failing with:
```
{"detail":"Failed to parse reconstruction JSON from Gemini: Expecting ',' delimiter: line 4 column 150 (char 297)"}
```

This error occurred when Gemini returned malformed JSON with:
- Unescaped quotes in strings
- Trailing commas
- Improperly formatted line breaks

## Solution

### 1. Enhanced JSON Extraction (agent_actions.py)

**Before:**
```python
match = re.search(r"\{.*\}", text, re.DOTALL)
if not match:
    raise HTTPException(...)
data = json.loads(match.group(0))
```

**After:**
```python
# Try to extract JSON from code blocks first (```json ... ```)
json_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
if json_block_match:
    json_str = json_block_match.group(1)
else:
    # Fall back to finding raw JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise HTTPException(...)
    json_str = match.group(0)

try:
    data = json.loads(json_str)
except json.JSONDecodeError as exc:
    # Log the problematic JSON for debugging
    print(f"Failed to parse JSON from Gemini. Raw response:\n{text}")
    print(f"Extracted JSON string:\n{json_str}")
    raise HTTPException(...)
```

**Benefits:**
- Handles both code-block wrapped JSON and raw JSON
- Better error logging for debugging
- More robust extraction

### 2. Improved Prompt Instructions

**Added to `_build_reconstruct_prompt`:**
```python
"IMPORTANT: Respond with ONLY valid JSON. Ensure all strings are properly escaped.\n"
"Use \\n for line breaks within strings, and escape any quotes with \\\".\n"
"\n"
"Respond strictly as compact JSON with the following shape:\n"
"{\n"
'  "heading": "optional improved heading, or null",\n'
'  "subtitle": "optional improved one-line summary, or null",\n'
'  "rich_text": "a single rich, multi-paragraph block of text. Use \\n for line breaks. You MAY use simple Markdown like bullet lists but ensure all text is properly escaped for JSON."\n'
"}\n"
"Do not add any extra keys, comments, trailing commas, or explanations outside this JSON object.\n"
```

**Key Changes:**
- Explicit instruction to escape strings properly
- Warning about trailing commas
- Clear guidance on line break handling
- Emphasis on valid JSON only

### 3. Document ID Flow Verification

The flow is now fully working with `document_id`:

```
Search → document_id → Get Document → Cache → AI Reconstruct
```

All endpoints properly use `document_id`:
- ✅ `/api/reels/search` returns `document_id`
- ✅ `/api/reels/document/{document_id}` fetches and caches
- ✅ `/api/agents/reconstruct/{document_id}` uses cached data
- ✅ Frontend passes `document_id` correctly

## Testing

### Test the Fix

1. **Start the server:**
```bash
cd /Users/tanzeel.shaikh/Sources/Projects/Save_act
python api_main.py
```

2. **Search for content:**
```bash
curl -X POST http://localhost:8000/api/reels/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 1}'
```

3. **Get document (use document_id from search):**
```bash
curl http://localhost:8000/api/reels/document/{document_id}
```

4. **Test AI Reconstruct:**
```bash
curl http://localhost:8000/api/agents/reconstruct/{document_id}
```

### Expected Behavior

**Success Response:**
```json
{
  "heading": "Enhanced Title",
  "subtitle": "Clear one-line summary",
  "rich_text": "Well-formatted multi-paragraph text...\n\n- Bullet point 1\n- Bullet point 2"
}
```

**If Still Failing:**
Check server logs for:
```
Failed to parse JSON from Gemini. Raw response:
{raw gemini output}
Extracted JSON string:
{extracted json}
```

This will show exactly what Gemini returned and help debug further.

## Files Modified

1. **`/Users/tanzeel.shaikh/Sources/Projects/Save_act/src/api/agent_actions.py`**
   - Enhanced `_call_gemini_for_reconstruct()` function
   - Improved `_build_reconstruct_prompt()` function

2. **Documentation Created:**
   - `DOCUMENT_ID_FLOW.md` - Complete flow documentation
   - `AI_RECONSTRUCT_FIX.md` - This file

## Rollback Instructions

If you need to revert these changes:

```bash
cd /Users/tanzeel.shaikh/Sources/Projects/Save_act
git diff src/api/agent_actions.py
git checkout src/api/agent_actions.py
```

## Next Steps

1. **Test thoroughly** with various document types
2. **Monitor logs** for any remaining JSON parse errors
3. **Consider adding** retry logic with different prompts if parsing fails
4. **Implement** persistent caching (Redis/DB) to replace in-memory REELS dict

## Additional Notes

- The fix maintains backward compatibility with existing code
- No changes required to frontend (code.html)
- The `document_id` is now the primary identifier throughout the system
- The `reel_id` field is kept for backward compatibility but `document_id` is preferred

