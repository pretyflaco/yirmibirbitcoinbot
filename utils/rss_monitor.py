"""RSS feed monitoring utility for the Telegram bot.

This module provides functions to monitor the Yirmibir Bitcoin Podcast RSS feed
and post notifications about new episodes to tracked Telegram chats.
"""

import asyncio
import logging
import time
import re
from typing import Dict, Any, Optional, List, Set
from datetime import datetime

import feedparser
from telegram.ext import ContextTypes

from config import RSS_FEED_URL, RSS_CHECK_INTERVAL

# Set up logging
logger = logging.getLogger(__name__)

def parse_episode_number(title: str) -> Optional[int]:
    """Extract episode number from title.
    
    Args:
        title: The episode title
        
    Returns:
        Episode number as integer, or None if not found
    """
    # Look for patterns like "001", "002", "32", etc. at the beginning of the title
    # Match 1-3 digits followed by a space and dash
    match = re.match(r'^(\d{1,3})(?:\s*-)', title.strip())
    if match:
        return int(match.group(1))
    return None

def fetch_rss_feed() -> Optional[List[Dict[str, Any]]]:
    """Fetch and parse the RSS feed.
    
    Returns:
        List of episode dictionaries, or None if fetch failed
    """
    try:
        logger.info(f"Fetching RSS feed from {RSS_FEED_URL}")
        feed = feedparser.parse(RSS_FEED_URL)
        
        if feed.bozo:
            logger.warning(f"RSS feed parsing warning: {feed.bozo_exception}")
        
        episodes = []
        for entry in feed.entries:
            # Extract title from CDATA if present
            title = entry.title
            if hasattr(entry, 'title_detail') and entry.title_detail.get('type') == 'text/html':
                # Remove CDATA wrapper if present
                title = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', title)
            
            episode_data = {
                'title': title.strip(),
                'link': entry.link,
                'published': entry.published if hasattr(entry, 'published') else '',
                'description': entry.description if hasattr(entry, 'description') else ''
            }
            
            # Add episode number if found
            episode_num = parse_episode_number(title)
            if episode_num:
                episode_data['episode_number'] = episode_num
            
            # Add published timestamp for sorting
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                episode_data['published_timestamp'] = time.mktime(entry.published_parsed)
            
            episodes.append(episode_data)
            
        logger.info(f"Successfully parsed {len(episodes)} episodes from RSS feed")
        return episodes
        
    except Exception as e:
        logger.error(f"Error fetching RSS feed: {e}")
        return None

def get_latest_rehber_episode(episodes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Get the latest episode by publication date.
    
    Args:
        episodes: List of episode dictionaries
        
    Returns:
        Latest episode dictionary (by publication date), or None if not found
    """
    numbered_episodes = []
    
    for episode in episodes:
        episode_num = episode.get('episode_number')
        if episode_num and episode_num >= 1:  # Episodes with numbers
            numbered_episodes.append(episode)
    
    if not numbered_episodes:
        return None
        
    # Sort by publication timestamp (descending) to get the most recent
    numbered_episodes.sort(key=lambda x: x.get('published_timestamp', 0), reverse=True)
    return numbered_episodes[0]

async def check_for_new_episode(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check for new podcast episodes and post notifications.
    
    Args:
        context: The context object for the bot
    """
    try:
        # Fetch RSS feed
        episodes = fetch_rss_feed()
        if not episodes:
            logger.error("Failed to fetch RSS feed")
            return
            
        # Get latest episode by publication date
        latest_episode = get_latest_rehber_episode(episodes)
        if not latest_episode:
            logger.info("No episodes found")
            return
            
        episode_link = latest_episode.get('link')
        if not episode_link:
            logger.info("Latest episode has no link")
            return
            
        # Check if we've already posted about this episode (using link as unique identifier)
        if 'posted_episode_links' not in context.bot_data:
            context.bot_data['posted_episode_links'] = set()
        
        posted_episodes = context.bot_data['posted_episode_links']
        if episode_link in posted_episodes:
            logger.info(f"Episode already posted: {latest_episode['title']}")
            return
            
        # This is a new episode we should post about
        logger.info(f"New episode detected: {latest_episode['title']}")
        
        # Get tracked chats (same as quote chats)
        tracked_chats = context.bot_data.get('quote_chats', set())
        if not tracked_chats:
            logger.warning("No tracked chats found for episode posting")
            return
            
        # Format the message
        title = latest_episode['title']
        link = latest_episode['link']

        # Replace "podcasters" with "creators" in Spotify links for better meta-image support
        if "podcasters.spotify.com" in link:
            link = link.replace("podcasters.spotify.com", "creators.spotify.com")
            logger.info(f"Converted Spotify link to creators URL for better meta-image: {link}")

        message = f"🎙️ *Yeni Bölüm:* {title}\n*Link:* {link}"
        
        # Post to each tracked chat
        for chat_id in tracked_chats:
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
                logger.info(f"Successfully posted new episode notification to chat {chat_id}")
            except Exception as e:
                logger.error(f"Failed to post episode notification to chat {chat_id}: {e}")
                
        # Mark this episode as posted
        context.bot_data['posted_episode_links'].add(episode_link)
        logger.info(f"Marked episode as posted: {latest_episode['title']}")
        
    except Exception as e:
        logger.error(f"Error in check_for_new_episode: {e}")

async def rss_monitor_scheduler(application) -> None:
    """Schedule RSS feed monitoring using asyncio.
    
    Args:
        application: The bot application object
    """
    while True:
        try:
            await check_for_new_episode(application)
        except Exception as e:
            logger.error(f"Error in RSS monitor scheduler: {e}")
        
        # Wait for the next check interval
        await asyncio.sleep(RSS_CHECK_INTERVAL)
