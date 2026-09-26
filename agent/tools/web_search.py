"""Web search tool with Tavily and DuckDuckGo fallback."""

import os
import logging
from typing import Optional
from agent.config import get_settings

logger = logging.getLogger(__name__)


def search_web(query: str, days: int = 7, max_results: int = 5) -> str:
    """Search the web for recent AI news and information.

    Uses Tavily Search API if TAVILY_API_KEY is available; falls back to DuckDuckGo search.
    """
    settings = get_settings()
    tavily_key = settings.tavily_api_key or os.environ.get("TAVILY_API_KEY")

    if tavily_key:
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=tavily_key)
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
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
        from duckduckgo_search import DDGS

        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=max_results))
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
