# Instagram Metrics Integration - Summary

## What Was Implemented

We've integrated **real-time Instagram metrics fetching** into the Reel Intelligence Agent Flow. The system now fetches live data from Instagram when generating intelligence for reels.

## Key Changes

### 1. New Instagram API Client (`src/services/instagram_api_client.py`)

A comprehensive client for interacting with Instagram's Graph API:

**Features:**
- Extract media ID from Instagram URLs
- Fetch detailed media information
- Get real-time insights/metrics
- Retrieve comments
- Fallback to web scraping when API is unavailable

**Supported Metrics:**
- Likes, Views, Comments (basic)
- Shares, Saves (engagement)
- Reach, Impressions (distribution)
- Engagement rate (calculated)

### 2. Updated Agent Flow

**Agent 0 - Reel Context Builder** now:
1. Detects Instagram URLs
2. Attempts to fetch real-time metrics from Instagram API
3. Falls back to cached metrics if API fails
4. Includes metrics source in the output (`instagram_api` or `extraction_cache`)

**State Object** now includes:
- `instagram_metrics`: Full Instagram API response with real-time data

**Final Intelligence Object** includes:
- Real-time metrics with timestamp
- Source attribution (API vs cache)
- Additional engagement metrics (shares, saves, reach)

### 3. Enhanced Streamlit UI

**New Metrics Display:**
- 📊 Real-Time Instagram Metrics section
- Visual metrics cards (Likes, Views, Comments, Engagement Rate)
- Additional metrics (Shares, Saves, Reach) when available
- Timestamp showing when metrics were fetched
- Clear indication of data source

## How It Works

### Flow Diagram

```
User clicks "Generate Agentic Flow"
            │
            ▼
┌───────────────────────────────────────┐
│  Agent 0: Reel Context Builder        │
│                                       │
│  1. Parse document content            │
│  2. Extract source URL                │
│  3. Check if Instagram URL            │
│     │                                 │
│     ├─ YES → Fetch from Instagram API │
│     │         │                       │
│     │         ├─ Success → Use API    │
│     │         │            metrics    │
│     │         │                       │
│     │         └─ Fail → Use cached    │
│     │                   metrics       │
│     │                                 │
│     └─ NO → Use cached metrics        │
│                                       │
│  4. Build reel context with metrics   │
└───────────────────────────────────────┘
            │
            ▼
     (Continue to other agents...)
```

### Metrics Priority

1. **Instagram Graph API** (if token available and reel is from your account)
   - Most comprehensive
   - Real-time data
   - Includes advanced metrics

2. **Web Scraping** (yt-dlp fallback for public reels)
   - Works for any public reel
   - Basic metrics only
   - May be rate-limited

3. **Cached Metrics** (from original extraction)
   - Always available
   - May be outdated
   - Stored in document

## Setup Instructions

### Quick Start (Scraping Method)

No setup required! The system will automatically use web scraping for public reels.

```bash
# Just run the app
streamlit run streamlit_search.py
```

### Full Setup (API Method)

For your own Instagram Business/Creator account:

1. **Create Facebook App**
   - Go to developers.facebook.com
   - Create a Business app
   - Add Instagram Graph API product

2. **Get Access Token**
   - Use Graph API Explorer
   - Grant required permissions
   - Copy access token

3. **Configure Environment**
   ```bash
   # Add to .env
   INSTAGRAM_ACCESS_TOKEN=your_token_here
   ```

4. **Test**
   ```bash
   python src/services/instagram_api_client.py "YOUR_INSTAGRAM_URL"
   ```

See `INSTAGRAM_API_SETUP.md` for detailed instructions.

## Usage Examples

### Example 1: Reel from Your Account (with API)

```python
# .env file has INSTAGRAM_ACCESS_TOKEN set

# In Streamlit:
# 1. Search for your reel
# 2. Click "View Details"
# 3. Click "Generate Agentic Flow"

# Result:
# ✅ Instagram metrics fetched successfully
# Metrics source: instagram_api
# Displays: Likes, Views, Comments, Shares, Saves, Reach, Impressions
```

### Example 2: Public Reel (scraping fallback)

```python
# No INSTAGRAM_ACCESS_TOKEN or reel from different account

# In Streamlit:
# 1. Search for any public reel
# 2. Click "View Details"
# 3. Click "Generate Agentic Flow"

# Result:
# ℹ️ API not available, using fallback scraping method
# Metrics source: instagram_api (via scraping)
# Displays: Likes, Views, Comments
```

### Example 3: Offline/Cached Metrics

```python
# Instagram is unreachable or reel is deleted

# In Streamlit:
# 1. Search for reel
# 2. Click "View Details"
# 3. Click "Generate Agentic Flow"

# Result:
# ⚠️ Could not fetch Instagram metrics
# Metrics source: extraction_cache
# Displays: Cached metrics from original extraction
```

## Benefits

### 1. Real-Time Data
- Always get the latest engagement metrics
- Track how reels perform over time
- More accurate trust scores

### 2. Comprehensive Metrics
- Beyond basic likes/views
- Understand reach and impressions
- Track saves and shares

### 3. Reliable Fallbacks
- API fails → Scraping
- Scraping fails → Cached data
- Always have some metrics

### 4. Better Trust Scores
- More accurate with real-time data
- Consider additional engagement signals
- Reflect current popularity

## API vs Scraping Comparison

| Feature | Instagram API | Web Scraping | Cached |
|---------|--------------|--------------|---------|
| **Setup Required** | Yes (token) | No | No |
| **Works For** | Your account | Public reels | All reels |
| **Metrics** | Comprehensive | Basic | Basic |
| **Reliability** | High | Medium | High |
| **Real-time** | Yes | Yes | No |
| **Rate Limits** | 200/hour | Varies | None |
| **Cost** | Free | Free | Free |

## Metrics Explained

### Basic Metrics

- **Likes**: Number of users who liked the reel
- **Views**: Number of times the reel was viewed
- **Comments**: Number of comments on the reel
- **Engagement Rate**: (Likes / Views) × 100

### Advanced Metrics (API only)

- **Shares**: How many times the reel was shared
- **Saves**: How many users saved the reel
- **Reach**: Unique accounts that saw the reel
- **Impressions**: Total times the reel was displayed

## Trust Score Impact

The trust score calculation now considers:

1. **Engagement Rate**: Higher engagement = higher trust
2. **Reach vs Impressions**: Organic reach is valued
3. **Saves**: Indicates valuable content
4. **Shares**: Shows viral potential
5. **Comments**: Indicates active engagement
6. **Recency**: Fresh metrics are more reliable

Example trust score reasoning:
```
"Trust Score: 87/100

This reel shows strong engagement with a 15.3% engagement rate 
(2,300 likes from 15,000 views). The content has been saved 450 
times and shared 120 times, indicating high value to viewers. 
Real-time metrics fetched 2 minutes ago show continued growth."
```

## Monitoring & Debugging

### Check Metrics Source

In the intelligence output, look for:
```json
{
  "reel_context": {
    "metrics": {
      "likes": 2500,
      "views": 15000,
      "source": "instagram_api",  // or "extraction_cache"
      "fetched_at": "2024-01-15T10:30:00"
    }
  }
}
```

### Console Output

```
🔨 [Agent 0] Reel Context Builder - Starting...
   📊 Fetching real-time Instagram metrics...
   ✅ Instagram metrics fetched successfully
✅ [Agent 0] Context built for: Amazing Workout Routine
   📊 Metrics source: instagram_api
```

### Troubleshooting

**No metrics displayed:**
- Check if Instagram URL is valid
- Verify access token (if using API)
- Check console for error messages

**Metrics seem outdated:**
- Verify `fetched_at` timestamp
- Check if using cached metrics
- Ensure API token is valid

**API errors:**
- Check token expiration
- Verify account permissions
- Review rate limits

## Future Enhancements

### Planned Features

1. **Metrics History Tracking**
   - Store metrics snapshots over time
   - Show growth trends
   - Compare performance

2. **Comments Analysis**
   - Fetch and analyze comments
   - Sentiment analysis on comments
   - Identify common themes

3. **Competitor Analysis**
   - Compare metrics with similar reels
   - Industry benchmarks
   - Performance insights

4. **Automated Refresh**
   - Periodic metrics updates
   - Webhook notifications
   - Real-time dashboards

5. **Multi-Platform Support**
   - TikTok metrics
   - YouTube Shorts metrics
   - Cross-platform comparison

## Files Modified/Created

### New Files
- `src/services/instagram_api_client.py` - Instagram API integration
- `INSTAGRAM_API_SETUP.md` - Setup guide
- `INSTAGRAM_METRICS_INTEGRATION.md` - This file

### Modified Files
- `src/services/reel_intelligence_agent.py` - Added Instagram metrics fetching
- `streamlit_search.py` - Enhanced UI for metrics display

## Testing

### Test Instagram API Client

```bash
# Test with Instagram URL
python src/services/instagram_api_client.py "https://www.instagram.com/reel/ABC123/"
```

### Test in Agent Flow

```bash
# Run test with sample data
python test_agent_flow.py

# Or use Streamlit
streamlit run streamlit_search.py
```

## Conclusion

The Instagram metrics integration provides:
- ✅ Real-time engagement data
- ✅ Comprehensive metrics
- ✅ Reliable fallbacks
- ✅ Better trust scores
- ✅ Enhanced user experience

The system intelligently handles different scenarios (API available, scraping, cached) to ensure metrics are always available for trust score calculation and user insights.

