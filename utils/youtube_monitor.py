"""YouTube channel monitoring utility for the Telegram bot.

This module monitors the Yirmibir Bitcoin YouTube channel for new videos
and posts notifications to tracked Telegram chats.
"""

import logging
import time
from typing import Dict, Any, Optional, List
import re

import feedparser
from telegram.ext import ContextTypes

# Set up logging
logger = logging.getLogger(__name__)

# YouTube channel RSS feed URL
# Format: https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
# For @yirmibirbitcoin, we need to get the channel ID first
# Alternative: Use the channel handle with yt-dlp or fetch from the channel page

YOUTUBE_CHANNEL_HANDLE = "@yirmibirbitcoin"
YOUTUBE_CHANNEL_URL = "https://www.youtube.com/@yirmibirbitcoin"

def get_channel_id_from_handle() -> Optional[str]:
    """Extract YouTube channel ID from the channel handle.
    
    Returns:
        Channel ID string, or None if not found
    """
    try:
        import httpx
        from bs4 import BeautifulSoup
        
        # Fetch the channel page
        response = httpx.get(YOUTUBE_CHANNEL_URL, timeout=10, follow_redirects=True)
        response.raise_for_status()
        
        # Look for channel ID in the page source
        # YouTube embeds it in various meta tags and JSON-LD
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find channel ID in meta tags
        meta_tag = soup.find('meta', property='og:url')
        if meta_tag and 'content' in meta_tag.attrs:
            url = meta_tag['content']
            # Extract channel ID from URL like https://www.youtube.com/channel/UC...
            match = re.search(r'channel/(UC[\w-]+)', url)
            if match:
                return match.group(1)
        
        # Try to find in link tags
        link_tag = soup.find('link', rel='canonical')
        if link_tag and 'href' in link_tag.attrs:
            url = link_tag['href']
            match = re.search(r'channel/(UC[\w-]+)', url)
            if match:
                return match.group(1)
        
        # Try to find in the page source directly
        page_text = response.text
        match = re.search(r'"channelId":"(UC[\w-]+)"', page_text)
        if match:
            return match.group(1)
        
        # Try another pattern
        match = re.search(r'"externalId":"(UC[\w-]+)"', page_text)
        if match:
            return match.group(1)
            
        logger.error("Could not find channel ID in page source")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting channel ID: {e}")
        return None

def fetch_youtube_rss(channel_id: str) -> Optional[List[Dict[str, Any]]]:
    """Fetch and parse YouTube RSS feed.
    
    Args:
        channel_id: YouTube channel ID
        
    Returns:
        List of video dictionaries, or None if fetch failed
    """
    try:
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        logger.info(f"Fetching YouTube RSS feed from {rss_url}")
        
        feed = feedparser.parse(rss_url)
        
        if feed.bozo:
            logger.warning(f"YouTube RSS feed parsing warning: {feed.bozo_exception}")
        
        videos = []
        for entry in feed.entries:
            video_data = {
                'title': entry.title.strip(),
                'link': entry.link,
                'video_id': entry.yt_videoid if hasattr(entry, 'yt_videoid') else entry.link.split('=')[-1],
                'published': entry.published if hasattr(entry, 'published') else '',
                'author': entry.author if hasattr(entry, 'author') else ''
            }
            
            # Add published timestamp for sorting
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                video_data['published_timestamp'] = time.mktime(entry.published_parsed)
            
            videos.append(video_data)
            
        logger.info(f"Successfully parsed {len(videos)} videos from YouTube RSS feed")
        return videos
        
    except Exception as e:
        logger.error(f"Error fetching YouTube RSS feed: {e}")
        return None

def get_latest_video(videos: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Get the latest video by publication date.
    
    Args:
        videos: List of video dictionaries
        
    Returns:
        Latest video dictionary, or None if not found
    """
    if not videos:
        return None
    
    # Sort by publication timestamp (descending) to get the most recent
    videos.sort(key=lambda x: x.get('published_timestamp', 0), reverse=True)
    return videos[0]

async def check_for_new_video(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check for new YouTube videos and post notifications.
    
    Args:
        context: The context object for the bot
    """
    try:
        # Get or fetch channel ID
        if 'youtube_channel_id' not in context.bot_data:
            logger.info("Fetching YouTube channel ID...")
            channel_id = get_channel_id_from_handle()
            if channel_id:
                context.bot_data['youtube_channel_id'] = channel_id
                logger.info(f"Found YouTube channel ID: {channel_id}")
            else:
                logger.error("Failed to get YouTube channel ID")
                return
        else:
            channel_id = context.bot_data['youtube_channel_id']
        
        # Fetch RSS feed
        videos = fetch_youtube_rss(channel_id)
        if not videos:
            logger.error("Failed to fetch YouTube RSS feed")
            return
        
        # Get latest video
        latest_video = get_latest_video(videos)
        if not latest_video:
            logger.info("No videos found")
            return
        
        video_link = latest_video.get('link')
        if not video_link:
            logger.info("Latest video has no link")
            return
        
        # Check if we've already posted about this video (using link as unique identifier)
        if 'posted_video_links' not in context.bot_data:
            context.bot_data['posted_video_links'] = set()
        
        posted_videos = context.bot_data['posted_video_links']
        if video_link in posted_videos:
            logger.info(f"Video already posted: {latest_video['title']}")
            return
        
        # This is a new video we should post about
        logger.info(f"New video detected: {latest_video['title']}")
        
        # Get tracked chats (same as quote chats)
        tracked_chats = context.bot_data.get('quote_chats', set())
        if not tracked_chats:
            logger.warning("No tracked chats found for video posting")
            return
        
        # Format the message
        title = latest_video['title']
        link = latest_video['link']
        
        message = f"🎬 *Yeni Video:* {title}\n\n{link}"
        
        # Post to each tracked chat
        for chat_id in tracked_chats:
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
                logger.info(f"Successfully posted new video notification to chat {chat_id}")
            except Exception as e:
                logger.error(f"Failed to post video notification to chat {chat_id}: {e}")
        
        # Mark this video as posted
        context.bot_data['posted_video_links'].add(video_link)
        logger.info(f"Marked video as posted: {latest_video['title']}")
        
    except Exception as e:
        logger.error(f"Error in check_for_new_video: {e}")

async def youtube_monitor_scheduler(application) -> None:
    """Schedule YouTube monitoring using asyncio.
    
    Args:
        application: The bot application object
    """
    import asyncio
    from config import YOUTUBE_CHECK_INTERVAL
    
    while True:
        try:
            await check_for_new_video(application)
        except Exception as e:
            logger.error(f"Error in YouTube monitor scheduler: {e}")
        
        # Wait for the next check interval
        await asyncio.sleep(YOUTUBE_CHECK_INTERVAL)

