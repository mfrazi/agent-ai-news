"""RSS feed fetcher for major AI labs and publications."""

import calendar
import logging
import time
from typing import Any, Dict, List, Optional
import feedparser
import httpx

logger = logging.getLogger(__name__)

DEFAULT_AI_FEEDS: Dict[str, str] = {
    "OpenAI News": "https://openai.com/news/rss.xml",
    "Google DeepMind": "https://deepmind.google/blog/rss.xml",
    "Hugging Face Blog": "https://huggingface.co/blog/feed.xml",
}


FEED_TIMEOUT_SECONDS = 15.0
FEED_HEADERS = {"User-Agent": "agent-ai-news/0.1"}


def _fetch_feed(feed_url: str) -> bytes:
    """Download a feed with a timeout; feedparser.parse(url) has none and can hang indefinitely."""
    response = httpx.get(feed_url, headers=FEED_HEADERS, timeout=FEED_TIMEOUT_SECONDS, follow_redirects=True)
    response.raise_for_status()
    return response.content


def _entry_timestamp(entry: Dict[str, Any]) -> Optional[float]:
    """Return the entry's published/updated time as a UTC epoch, or None if unknown."""
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if isinstance(parsed, time.struct_time):
            return calendar.timegm(parsed)
    return None


def fetch_ai_rss(days: int = 3, max_entries_per_feed: int = 5) -> str:
    """Fetch and parse recent announcements from curated AI lab RSS feeds."""
    all_articles: List[str] = []
    cutoff = time.time() - days * 86400

    for source_name, feed_url in DEFAULT_AI_FEEDS.items():
        try:
            feed = feedparser.parse(_fetch_feed(feed_url))
            entries = getattr(feed, "entries", [])
            if not entries:
                continue

            # Entries without a parseable date are kept rather than silently dropped
            recent_entries = [
                e for e in entries
                if (ts := _entry_timestamp(e)) is None or ts >= cutoff
            ]
            # feedparser entries are FeedParserDict (a dict subclass)
            for entry in recent_entries[:max_entries_per_feed]:
                title = entry.get("title") or "Untitled"
                link = entry.get("link") or ""
                summary = str(entry.get("summary") or "").strip()
                if len(summary) > 250:
                    summary = summary[:247] + "..."

                all_articles.append(f"- **[{title}]({link})** (*{source_name}*)\n  {summary}")
        except Exception as exc:
            logger.warning(f"Error fetching RSS feed '{source_name}' ({feed_url}): {exc}")
            continue

    if not all_articles:
        return "No recent RSS updates retrieved from AI lab feeds."

    return "\n\n".join(all_articles)
