"""RSS feed fetcher for major AI labs and publications."""

import logging
from typing import List, Dict
import feedparser

logger = logging.getLogger(__name__)

DEFAULT_AI_FEEDS: Dict[str, str] = {
    "OpenAI News": "https://openai.com/news/rss.xml",
    "Google DeepMind": "https://deepmind.google/blog/rss.xml",
    "Anthropic News": "https://www.anthropic.com/news/feed",
    "Hugging Face Blog": "https://huggingface.co/blog/feed.xml",
}


def fetch_ai_rss(days: int = 3, max_entries_per_feed: int = 5) -> str:
    """Fetch and parse recent announcements from curated AI lab RSS feeds."""
    all_articles: List[str] = []

    for source_name, feed_url in DEFAULT_AI_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            entries = getattr(feed, "entries", [])
            if not entries:
                continue

            for entry in entries[:max_entries_per_feed]:
                if isinstance(entry, dict):
                    title = entry.get("title") or "Untitled"
                    link = entry.get("link") or ""
                    summary = entry.get("summary") or ""
                else:
                    title = getattr(entry, "title", None) or (entry.get("title") if hasattr(entry, "get") else "Untitled")
                    link = getattr(entry, "link", None) or (entry.get("link") if hasattr(entry, "get") else "")
                    summary = getattr(entry, "summary", None) or (entry.get("summary") if hasattr(entry, "get") else "")

                summary = str(summary).strip()
                if len(summary) > 250:
                    summary = summary[:247] + "..."

                all_articles.append(f"- **[{title}]({link})** (*{source_name}*)\n  {summary}")
        except Exception as exc:
            logger.warning(f"Error fetching RSS feed '{source_name}' ({feed_url}): {exc}")
            continue

    if not all_articles:
        return "No recent RSS updates retrieved from AI lab feeds."

    return "\n\n".join(all_articles)
