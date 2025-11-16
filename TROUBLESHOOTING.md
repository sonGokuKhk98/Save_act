# Troubleshooting Guide - AI Reconstruct & Document ID Flow

## Common Issues and Solutions

### 1. JSON Parsing Error

**Error Message:**
```
{"detail":"Failed to parse reconstruction JSON from Gemini: Expecting ',' delimiter: line 4 column 150 (char 297)"}
```

**Cause:** Gemini returned malformed JSON with unescaped quotes, trailing commas, or invalid syntax.

**Solution:**
✅ **Already Fixed!** The enhanced parsing now:
- Tries multiple extraction methods
- Logs full response for debugging
- Has better prompt instructions

**If Still Occurring:**
1. Check server logs for the full Gemini response
2. Look for the logged "Extracted JSON string"
3. Manually validate the JSON at https://jsonlint.com
4. Report the pattern to improve prompts further

**Debug Steps:**
```bash
# Check server logs
tail -f server.log | grep "Failed to parse"

# You should see:
# Failed to parse reconstruction JSON from Gemini. Raw response:
# {full gemini response}
# Extracted JSON string:
# {extracted json}
```

---

### 2. Document Not Found

**Error Message:**
```
{"detail":"Document {document_id} not found in cache or Supermemory: ..."}
```

**Cause:** Invalid document_id or document was deleted from Supermemory.

**Solutions:**

1. **Verify document_id is correct:**
```bash
# Check if document exists in Supermemory
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.supermemory.ai/v3/documents/{document_id}
```

2. **Check API key is configured:**
```bash
# In your .env file
cat .env | grep SUPERMEMORY_API_KEY
```

3. **Try fetching document first:**
```bash
# This will cache it
curl http://localhost:8000/api/reels/document/{document_id}

# Then try reconstruct
curl http://localhost:8000/api/agents/reconstruct/{document_id}
```

---

### 3. Empty or Missing rich_text

**Error Message:**
```
{"detail":"Reconstruction plan rich_text must be a non-empty string."}
```

**Cause:** Gemini didn't provide the `rich_text` field in the response.

**Solutions:**

1. **Check if Gemini API is working:**
```bash
# Test with a simple document
curl http://localhost:8000/api/agents/reconstruct/{document_id}
```

2. **Try with a different model:**
   - The system automatically falls back from Pro to Flash models
   - Check server logs to see which model was used

3. **Verify the extraction has content:**
```bash
# Check the cached document
curl http://localhost:8000/api/reels/{document_id}
```

---

### 4. Gemini API Quota Exceeded

**Error Message:**
```
{"detail":"Gemini error while generating reconstruction plan: ResourceExhausted..."}
```

**Cause:** Gemini API quota limit reached.

**Solutions:**

1. **System automatically tries fallback:**
   - First tries Pro models
   - Falls back to Flash models on quota error
   - Check logs to see which model was used

2. **Wait and retry:**
```bash
# Wait a few minutes for quota to reset
sleep 300

# Retry
curl http://localhost:8000/api/agents/reconstruct/{document_id}
```

3. **Check your Gemini API quota:**
   - Visit Google AI Studio
   - Check your quota limits
   - Consider upgrading if needed

---

### 5. Frontend Not Loading Document

**Symptoms:**
- Blank screen after clicking search result
- Console errors about `window.__REEL_ID__`

**Solutions:**

1. **Check URL has document_id:**
```javascript
// In browser console
console.log(window.location.search);
// Should show: ?document_id=abc123
```

2. **Check if document_id is set:**
```javascript
// In browser console
console.log(window.__REEL_ID__);
// Should show: abc123
```

3. **Check network tab:**
   - Look for call to `/api/reels/document/{document_id}`
   - Check if it returned 200 OK
   - Verify response has document, keyframes, custom_id

4. **Clear cache and reload:**
```javascript
// In browser console
localStorage.clear();
sessionStorage.clear();
location.reload();
```

---

### 6. AI Reconstruct Button Not Working

**Symptoms:**
- Button click does nothing
- No network request in dev tools

**Solutions:**

1. **Check if button exists:**
```javascript
// In browser console
console.log(document.getElementById('gx-agentic-reconstruct'));
// Should show: <button id="gx-agentic-reconstruct">...</button>
```

2. **Check if document_id is set:**
```javascript
// In browser console
console.log(window.__REEL_ID__);
// Should show: abc123
```

3. **Check console for errors:**
```javascript
// Open browser console (F12)
// Look for any JavaScript errors
```

4. **Manually trigger the API call:**
```javascript
// In browser console
fetch(`/api/agents/reconstruct/${window.__REEL_ID__}`)
  .then(r => r.json())
  .then(console.log);
```

---

### 7. Keyframes Not Loading

**Symptoms:**
- Document loads but no keyframe images
- Thumbnails missing

**Solutions:**

1. **Check if keyframes exist:**
```bash
curl http://localhost:8000/api/reels/document/{document_id}
# Check "keyframes" array in response
```

2. **Verify customId is present:**
```bash
curl http://localhost:8000/api/reels/document/{document_id}
# Check "custom_id" field in response
```

3. **Check Supermemory has images:**
```bash
# Search for images with customId
curl -X POST https://api.supermemory.ai/v3/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "q": "images",
    "filters": {
      "AND": [
        {"key": "customId", "value": "YOUR_CUSTOM_ID", "negate": false}
      ]
    }
  }'
```

---

### 8. Search Returns No Results

**Symptoms:**
- Search completes but returns empty results array

**Solutions:**

1. **Check Supermemory has data:**
```bash
curl -X POST https://api.supermemory.ai/v3/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q": "your search query"}'
```

2. **Verify API key is correct:**
```bash
cat .env | grep SUPERMEMORY_API_KEY
```

3. **Check search filters:**
   - Current implementation filters for `type: "text"`
   - Removes duplicates by documentId
   - Limits results to requested limit

4. **Try broader search:**
```bash
curl -X POST http://localhost:8000/api/reels/search \
  -H "Content-Type: application/json" \
  -d '{"query": "", "limit": 50}'
```

---

## Debugging Checklist

When something goes wrong, check these in order:

### 1. Environment Setup
- [ ] `.env` file exists with `SUPERMEMORY_API_KEY`
- [ ] `GEMINI_API_KEY` is set (if using Gemini)
- [ ] Server is running on correct port
- [ ] No firewall blocking requests

### 2. API Connectivity
- [ ] Can reach Supermemory API
- [ ] Can reach Gemini API
- [ ] Network requests succeed in browser dev tools
- [ ] CORS is not blocking requests

### 3. Data Flow
- [ ] Search returns document_id
- [ ] Document fetch succeeds
- [ ] Document is cached in REELS
- [ ] Frontend sets window.__REEL_ID__
- [ ] AI Reconstruct can access cached data

### 4. Logs
- [ ] Check server logs for errors
- [ ] Check browser console for errors
- [ ] Check network tab for failed requests
- [ ] Look for Gemini response logs

---

## Useful Commands

### Check Server Status
```bash
curl http://localhost:8000/health
```

### Test Full Flow
```bash
# 1. Search
curl -X POST http://localhost:8000/api/reels/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 1}' \
  | jq '.results[0].document_id'

# 2. Get document (use document_id from above)
curl http://localhost:8000/api/reels/document/DOCUMENT_ID \
  | jq '.custom_id'

# 3. AI Reconstruct
curl http://localhost:8000/api/agents/reconstruct/DOCUMENT_ID \
  | jq '.'
```

### Check Cache
```python
# In Python shell or script
from src.api.reels import REELS
print(f"Cached documents: {len(REELS)}")
print(f"Document IDs: {list(REELS.keys())}")
```

### Clear Cache
```python
# In Python shell or script
from src.api.reels import REELS
REELS.clear()
print("Cache cleared")
```

---

## Getting Help

If you're still stuck after trying these solutions:

1. **Collect Information:**
   - Error message (full text)
   - Server logs (last 50 lines)
   - Browser console errors
   - Network tab screenshot
   - document_id you're trying to use

2. **Check Documentation:**
   - `DOCUMENT_ID_FLOW.md` - Complete flow explanation
   - `AI_RECONSTRUCT_FIX.md` - Fix details
   - `CHANGES_SUMMARY.md` - What changed
   - `FLOW_DIAGRAM.md` - Visual flow

3. **Test Isolation:**
   - Test each endpoint separately
   - Verify Supermemory API directly
   - Verify Gemini API directly
   - Test with known good document_id

4. **Report Issue:**
   - Include all collected information
   - Describe steps to reproduce
   - Note what you've already tried
   - Include relevant log excerpts

---

## Prevention

To avoid issues in the future:

1. **Always use document_id** from search results
2. **Fetch document before** calling AI endpoints
3. **Check server logs** regularly for warnings
4. **Monitor API quotas** for Gemini and Supermemory
5. **Test changes** with known good document_ids
6. **Keep documentation** updated with new patterns

---

## Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| JSON parse error | Check server logs for full response |
| Document not found | Verify document_id, check API key |
| Empty rich_text | Check Gemini API, try different model |
| Quota exceeded | Wait and retry, system auto-falls back |
| Frontend blank | Check URL has document_id param |
| Button not working | Check window.__REEL_ID__ is set |
| No keyframes | Check customId exists in Supermemory |
| No search results | Verify API key, check Supermemory data |

---

## Version Info

- **Last Updated:** November 16, 2025
- **Applies To:** AI Reconstruct Fix v1.0
- **Related Files:** 
  - `src/api/agent_actions.py`
  - `src/api/reels.py`
  - `src/code.html`

