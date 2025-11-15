# Instagram API Integration Setup

## Overview

The Reel Intelligence Agent Flow now integrates with Instagram's Graph API to fetch real-time metrics (likes, views, comments, shares, saves, reach, impressions) for reels.

## Two Methods of Fetching Metrics

### Method 1: Instagram Graph API (Recommended)
- **Pros**: Official API, reliable, comprehensive metrics
- **Cons**: Requires Facebook/Instagram Business account, API setup
- **Metrics Available**: Likes, views, comments, shares, saves, reach, impressions, engagement

### Method 2: Web Scraping Fallback (using yt-dlp)
- **Pros**: No API setup required, works for public reels
- **Cons**: Less reliable, may break if Instagram changes HTML, limited metrics
- **Metrics Available**: Likes, views, comments (basic)

## Setup Instagram Graph API (Method 1)

### Step 1: Create a Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click "My Apps" → "Create App"
3. Select "Business" as app type
4. Fill in app details and create

### Step 2: Add Instagram Graph API

1. In your app dashboard, click "Add Product"
2. Find "Instagram Graph API" and click "Set Up"
3. Follow the setup wizard

### Step 3: Get Instagram Business Account

1. Convert your Instagram account to a Business or Creator account
2. Link it to a Facebook Page
3. Note your Instagram Business Account ID

### Step 4: Generate Access Token

#### Option A: Short-lived Token (Testing)

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app
3. Click "Generate Access Token"
4. Grant permissions:
   - `instagram_basic`
   - `instagram_manage_insights`
   - `pages_read_engagement`
   - `pages_show_list`
5. Copy the access token

#### Option B: Long-lived Token (Production)

```bash
# Exchange short-lived token for long-lived token (60 days)
curl -i -X GET "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=YOUR_SHORT_LIVED_TOKEN"
```

#### Option C: Never-expiring Token (Best for Production)

1. Get a long-lived user access token (60 days)
2. Use it to get a Page access token
3. The Page access token doesn't expire

```bash
# Get Page access token
curl -i -X GET "https://graph.facebook.com/v18.0/me/accounts?access_token=YOUR_LONG_LIVED_TOKEN"
```

### Step 5: Configure Environment Variable

Add to your `.env` file:

```bash
INSTAGRAM_ACCESS_TOKEN=your_access_token_here
```

### Step 6: Test the Integration

```bash
python src/services/instagram_api_client.py "https://www.instagram.com/reel/ABC123/"
```

## API Permissions Required

- `instagram_basic`: Read basic Instagram account info
- `instagram_manage_insights`: Read insights and metrics
- `pages_read_engagement`: Read engagement metrics
- `pages_show_list`: List pages connected to account

## Important Notes

### Limitations

1. **Own Content Only**: The Instagram Graph API can only fetch metrics for content from accounts you manage
2. **Business/Creator Accounts**: Only works with Instagram Business or Creator accounts
3. **Rate Limits**: Facebook has rate limits on API calls
4. **Token Expiration**: Access tokens expire (use long-lived or page tokens)

### For Public Reels (Not Your Own)

If you want to fetch metrics for public reels that you don't own:

1. The Graph API won't work (it only works for your own content)
2. The system will automatically fall back to web scraping using `yt-dlp`
3. Metrics will be limited to basic counts (likes, views, comments)

## How It Works in the Agent Flow

### Agent 0: Reel Context Builder

```python
# 1. Check if source URL is Instagram
if source_url and "instagram.com" in source_url:
    
    # 2. Try to fetch metrics from Instagram API
    instagram_data = fetch_instagram_metrics(source_url)
    
    # 3. If API succeeds, use real-time metrics
    if instagram_data.get("success"):
        metrics = {
            "likes": api_metrics.get("likes"),
            "views": api_metrics.get("views"),
            "comments_count": api_metrics.get("comments"),
            "shares": api_metrics.get("shares"),
            "saves": api_metrics.get("saved"),
            "reach": api_metrics.get("reach"),
            "impressions": api_metrics.get("impressions"),
            "source": "instagram_api"
        }
    
    # 4. If API fails, fall back to cached metrics from extraction
    else:
        metrics = {
            "likes": content_data.get("likes", 0),
            "views": content_data.get("views", 0),
            "comments_count": content_data.get("comments_count", 0),
            "source": "extraction_cache"
        }
```

## Metrics Displayed in UI

### Basic Metrics (Always Shown)
- 👍 Likes
- 👁️ Views
- 💬 Comments
- 📈 Engagement Rate (calculated: likes/views * 100)

### Advanced Metrics (If Available from API)
- 🔄 Shares
- 💾 Saves
- 📡 Reach
- 📊 Impressions

## Troubleshooting

### Error: "No access token provided"

**Solution**: Set `INSTAGRAM_ACCESS_TOKEN` in your `.env` file

### Error: "Invalid OAuth access token"

**Solutions**:
1. Token may have expired - generate a new one
2. Token may not have required permissions
3. App may not be in live mode (for production)

### Error: "Unsupported get request"

**Solutions**:
1. Make sure the media ID is correct
2. Verify the media belongs to your account
3. Check that your account is a Business/Creator account

### Metrics Show Zero

**Possible Causes**:
1. The reel is from a different account (not yours)
2. The reel is too new (metrics not yet available)
3. API permissions are insufficient

**Solution**: The system will fall back to scraping method automatically

### Scraping Method Also Fails

**Possible Causes**:
1. Instagram blocked the request (rate limiting)
2. Reel is private or deleted
3. Network issues

**Solution**: Use cached metrics from the original extraction

## Testing Different Scenarios

### Test with Your Own Reel (API)

```bash
# Set your access token
export INSTAGRAM_ACCESS_TOKEN="your_token"

# Test with your reel
python src/services/instagram_api_client.py "https://www.instagram.com/reel/YOUR_REEL/"
```

### Test with Public Reel (Scraping Fallback)

```bash
# Don't set access token (or use invalid one)
unset INSTAGRAM_ACCESS_TOKEN

# Test with any public reel
python src/services/instagram_api_client.py "https://www.instagram.com/reel/PUBLIC_REEL/"
```

### Test in Agent Flow

```bash
# Run Streamlit app
streamlit run streamlit_search.py

# 1. Search for a reel
# 2. Click "View Details"
# 3. Click "Generate Agentic Flow"
# 4. Check the metrics source in the output
```

## Best Practices

1. **Use Long-lived Tokens**: Set up long-lived or page access tokens for production
2. **Cache Metrics**: Store metrics during extraction to avoid repeated API calls
3. **Handle Failures Gracefully**: Always have fallback to cached metrics
4. **Respect Rate Limits**: Don't make too many API calls in short time
5. **Monitor Token Expiration**: Set up alerts for token expiration

## Cost Considerations

- Instagram Graph API is **free** for basic usage
- Rate limits apply (200 calls per hour per user)
- No cost for scraping fallback method
- Consider caching metrics to reduce API calls

## Security

1. **Never commit tokens**: Keep `.env` file in `.gitignore`
2. **Use environment variables**: Don't hardcode tokens in code
3. **Rotate tokens regularly**: Generate new tokens periodically
4. **Limit permissions**: Only request permissions you need
5. **Use HTTPS**: Always use secure connections

## Alternative: Instagram Basic Display API

For personal accounts (not business), you can use Instagram Basic Display API:

- Simpler setup
- Works with personal accounts
- Limited metrics (no insights)
- Good for basic use cases

See: https://developers.facebook.com/docs/instagram-basic-display-api

## Resources

- [Instagram Graph API Documentation](https://developers.facebook.com/docs/instagram-api/)
- [Instagram Insights](https://developers.facebook.com/docs/instagram-api/guides/insights)
- [Access Tokens](https://developers.facebook.com/docs/facebook-login/guides/access-tokens)
- [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)

