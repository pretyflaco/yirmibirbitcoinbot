# YouTube Monitoring Feature

## Overview

The bot now automatically monitors the [Yirmibir Bitcoin YouTube channel](https://www.youtube.com/@yirmibirbitcoin) and posts new videos to the Telegram group.

## How It Works

### 1. Channel Monitoring
- **Channel**: @yirmibirbitcoin
- **Channel ID**: UCugsZu41X5nxL_6XJxT5vlg
- **Check Interval**: Every 30 minutes (configurable)

### 2. RSS Feed
The bot uses YouTube's RSS feed system to detect new videos:
```
https://www.youtube.com/feeds/videos.xml?channel_id=UCugsZu41X5nxL_6XJxT5vlg
```

### 3. Notification Format
When a new video is published, the bot posts:
```
🎬 *Yeni Video:* [Video Title]

[Video Link]
```

## Configuration

### Environment Variables
Add to your `.env` file:

```bash
# YouTube monitoring settings
YOUTUBE_CHECK_INTERVAL=1800  # Check every 30 minutes (in seconds)
```

### Default Settings
- **Check Interval**: 1800 seconds (30 minutes)
- **First Check**: 60 seconds after bot starts
- **Target Chats**: All chats in `quote_chats` set

## Files Modified/Created

### New Files
- `utils/youtube_monitor.py` - Main YouTube monitoring logic

### Modified Files
- `config.py` - Added YouTube configuration variables
- `bot.py` - Registered YouTube monitor in job queue
- `requirements.txt` - Added dependencies:
  - `httpx==0.27.0` - Async HTTP client
  - `beautifulsoup4==4.12.3` - HTML parsing for channel ID extraction

## Technical Details

### Channel ID Extraction
The bot automatically extracts the YouTube channel ID from the channel handle by:
1. Fetching the channel page HTML
2. Parsing meta tags (`og:url`, canonical links)
3. Searching page source for `channelId` or `externalId` patterns
4. Caching the ID in `bot_data['youtube_channel_id']`

### Duplicate Prevention
- Posted videos are tracked in `bot_data['posted_video_links']`
- Both short (`youtu.be`) and full (`youtube.com/watch`) URLs are tracked
- The initial video (https://youtu.be/eNw-xsqOlfE) is pre-added to prevent reposting

### Error Handling
- Graceful fallback if channel ID extraction fails
- Continues checking even if individual requests fail
- All errors are logged for debugging

## Testing

To verify the YouTube monitoring is working:

1. Check bot logs for:
   ```
   YouTube monitoring started
   Found YouTube channel ID: UCugsZu41X5nxL_6XJxT5vlg
   ```

2. The bot will check for new videos every 30 minutes

3. When a new video is published, it will be posted to all tracked Telegram chats

## Customization

### Change Check Interval
Edit `config.py` or set environment variable:
```python
YOUTUBE_CHECK_INTERVAL = 600  # Check every 10 minutes
```

### Change Message Format
Edit the message format in `utils/youtube_monitor.py`:
```python
message = f"🎬 *Yeni Video:* {title}\n\n{link}"
```

### Monitor Additional Channels
Create additional monitor instances in `bot.py`:
```python
from utils.youtube_monitor import check_for_new_video

# Add another channel
application.job_queue.run_repeating(
    check_for_new_video_channel2, 
    interval=1800, 
    first=90
)
```

## Troubleshooting

### Channel ID Not Found
If the bot can't extract the channel ID:
1. Check internet connectivity
2. Verify the channel URL is correct
3. Check logs for specific error messages

### No Videos Posted
If new videos aren't being posted:
1. Verify the bot is in the Telegram group
2. Check `bot_data['quote_chats']` contains the group ID
3. Ensure sufficient time has passed (check interval)
4. Verify RSS feed is accessible

### Duplicate Posts
If videos are posted multiple times:
1. Check if `bot_data['posted_video_links']` is persisting
2. Restart the bot to clear the set
3. Manually add video links to the set

## Maintenance

### Updating Dependencies
```bash
pip install -r requirements.txt
```

### Viewing Logs
Monitor the bot logs for YouTube-related messages:
```bash
grep -i "youtube" bot.log
```

## Related Links

- [YouTube Channel](https://www.youtube.com/@yirmibirbitcoin)
- [Latest Video](https://youtu.be/eNw-xsqOlfE) - "Açık Olan Hep Kazanır"
- [YouTube RSS Feed Documentation](https://developers.google.com/youtube/v3/guides/implementation/subscriptions#push-notifications)

