"""Blog monitoring utility for the Telegram bot.

Watches the yirmibir.org blog RSS feed (generated at build time from the site's
posts) and announces new posts to the tracked Telegram chats.

The feed has no dates; the post URL (guid) is the identity. Dedup state lives in
memory, so on the first successful fetch after startup every post currently in
the feed is recorded as already posted and nothing is sent.
"""

import html
import logging
from typing import Any, Dict, List, Optional

import feedparser
from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_USERNAME, BLOG_FEED_URL

logger = logging.getLogger(__name__)

# Safety valve: never announce more than this many posts in one check.
MAX_POSTS_PER_CHECK = 3
SUMMARY_MAX_CHARS = 280


def fetch_blog_feed() -> Optional[List[Dict[str, Any]]]:
    """Fetch the blog feed. Returns posts newest-first, or None on failure/empty."""
    try:
        logger.info(f"Fetching blog feed from {BLOG_FEED_URL}")
        feed = feedparser.parse(BLOG_FEED_URL)
        status = getattr(feed, "status", None)
        if status is not None and status >= 400:
            logger.warning(f"Blog feed returned HTTP {status}")
            return None
        posts = []
        for entry in feed.entries:
            link = entry.get("link") or entry.get("id")
            title = (entry.get("title") or "").strip()
            if not link or not title:
                continue
            posts.append({
                "id": entry.get("id") or link,
                "link": link,
                "title": title,
                "summary": (entry.get("summary") or "").strip(),
                # <yirmibir:x> in the feed = URL of the X announcement post
                "x_url": (entry.get("yirmibir_x") or "").strip(),
            })
        if not posts:
            logger.warning("Blog feed has no entries")
            return None
        logger.info(f"Successfully parsed {len(posts)} posts from blog feed")
        return posts
    except Exception as e:
        logger.error(f"Error fetching blog feed: {e}")
        return None


def format_blog_message(post: Dict[str, Any]) -> str:
    """HTML message (titles often contain apostrophes/colons; avoid Markdown pitfalls)."""
    summary = post["summary"]
    if len(summary) > SUMMARY_MAX_CHARS:
        summary = summary[:SUMMARY_MAX_CHARS].rsplit(" ", 1)[0] + "…"
    parts = [f"📝 <b>Yeni Yazı:</b> {html.escape(post['title'], quote=False)}"]
    if summary:
        parts.append(html.escape(summary, quote=False))
    parts.append(html.escape(post['link'], quote=False))
    if post.get("x_url"):
        parts.append(f"𝕏 Duyuru: {html.escape(post['x_url'], quote=False)}")
    return "\n\n".join(parts)


async def check_for_new_blog_post(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check the blog feed and announce posts not seen before."""
    try:
        posts = fetch_blog_feed()
        if not posts:
            # Do not prime on a failed/empty fetch, otherwise the first real
            # fetch later would announce the whole archive.
            return

        posted = context.bot_data.setdefault("posted_blog_ids", set())

        if not context.bot_data.get("blog_monitor_primed") and not posted:
            posted.update(p["id"] for p in posts)
            context.bot_data["blog_monitor_primed"] = True
            logger.info(f"Startup: marked {len(posts)} existing blog posts as already posted")
            return
        context.bot_data["blog_monitor_primed"] = True

        new_posts = [p for p in posts if p["id"] not in posted]
        if not new_posts:
            logger.info(f"No new blog posts (latest: {posts[0]['title']})")
            return

        if len(new_posts) > MAX_POSTS_PER_CHECK:
            logger.warning(
                f"{len(new_posts)} unseen blog posts; announcing only the newest {MAX_POSTS_PER_CHECK}"
            )
            for p in new_posts[MAX_POSTS_PER_CHECK:]:
                posted.add(p["id"])
            new_posts = new_posts[:MAX_POSTS_PER_CHECK]

        if not context.bot_data.get("quote_chats"):
            logger.warning("No tracked chats found for blog posting")
            return

        # Oldest first so the group sees them in publication order.
        for post in reversed(new_posts):
            logger.info(f"New blog post detected: {post['title']}")
            await announce_blog_post(context, post)
    except Exception as e:
        logger.error(f"Error in check_for_new_blog_post: {e}")


async def announce_blog_post(context: ContextTypes.DEFAULT_TYPE, post: Dict[str, Any]) -> int:
    """Send one post to every tracked chat. Returns the number of chats reached."""
    sent = 0
    message = format_blog_message(post)
    for chat_id in context.bot_data.get("quote_chats", set()):
        try:
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
            sent += 1
            logger.info(f"Successfully posted blog post '{post['title']}' to chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to post blog notification to chat {chat_id}: {e}")
    context.bot_data.setdefault("posted_blog_ids", set()).add(post["id"])
    return sent


async def post_latest_blog_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/sonyazi (admin only, private chat): post the newest blog post to the group now.

    Posts even if it was already marked as posted (e.g. it went live before
    the monitor existed). Use in a private chat with the bot.
    """
    user = update.effective_user
    if not user or user.username != ADMIN_USERNAME:
        return
    if update.effective_chat.type != "private":
        await update.message.reply_text("Bu komutu bota özel mesajla gönderin.")
        return
    posts = fetch_blog_feed()
    if not posts:
        await update.message.reply_text("❌ Blog akışı okunamadı.")
        return
    latest = posts[0]
    sent = await announce_blog_post(context, latest)
    await update.message.reply_text(
        f"✅ \"{latest['title']}\" {sent} gruba gönderildi."
        + ("" if latest.get("x_url") else "\n(Uyarı: bu yazıda X duyuru bağlantısı yok.)")
    )
