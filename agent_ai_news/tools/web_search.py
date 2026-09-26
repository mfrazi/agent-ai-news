"""Web search tool with Tavily and DuckDuckGo fallback."""

import logging
from agent_ai_news.config import get_settings

logger = logging.getLogger(__name__)


def _time_range(days: int) -> str:
    """Map a lookback window in days to the coarse Tavily time_range buckets."""
    if days <= 1:
        return "day"
    if days <= 7:
        return "week"
    if days <= 31:
        return "month"
    return "year"


def search_web(query: str, days: int = 7, max_results: int = 5) -> str:
    """Search the web for recent AI news and information.

    Uses Tavily Search API if TAVILY_API_KEY is available; falls back to DuckDuckGo search.
    """
    tavily_key = get_settings().tavily_api_key

    if tavily_key:
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=tavily_key)
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                time_range=_time_range(days),
                include_answer=False,
            )
            results = response.get("results", [])
            if results:
                formatted = []
                for item in results:
                    title = item.get("title", "Untitled")
                    url = item.get("url", "")
                    content = item.get("content", "").strip()
                    formatted.append(f"- **[{title}]({url})**\n  {content}")
                return "\n\n".join(formatted)
        except Exception as exc:
            logger.warning(f"Tavily search failed: {exc}. Falling back to DuckDuckGo.")

    # Fallback: DuckDuckGo Search
    try:
        from ddgs import DDGS

        # DuckDuckGo timelimit takes the first letter of the bucket: d / w / m / y
        results = DDGS().text(query, timelimit=_time_range(days)[0], max_results=max_results)
        if not results:
            return f"No web search results found for query: '{query}'."

        formatted = []
        for item in results:
            title = item.get("title", "Untitled")
            href = item.get("href", "")
            body = item.get("body", "").strip()
            formatted.append(f"- **[{title}]({href})**\n  {body}")
        return "\n\n".join(formatted)
    except Exception as exc:
        logger.error(f"DuckDuckGo search error: {exc}")
        return f"Error executing web search for '{query}': {exc}"
