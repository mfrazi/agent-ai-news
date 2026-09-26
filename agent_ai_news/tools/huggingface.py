"""Hugging Face daily trending papers tool."""

import logging
from typing import List, Dict, Any
import httpx

logger = logging.getLogger(__name__)

HF_DAILY_PAPERS_API = "https://huggingface.co/api/daily_papers"


def query_hf_papers(limit: int = 5) -> str:
    """Fetch top community-upvoted papers from Hugging Face Daily Papers."""
    try:
        response = httpx.get(HF_DAILY_PAPERS_API, timeout=15.0)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list) or not data:
            return "No trending papers found on Hugging Face today."

        papers_list = []
        for item in data[:limit]:
            paper = item.get("paper", {})
            paper_id = paper.get("id", "")
            title = paper.get("title", "Untitled")
            summary = paper.get("summary", "").strip().replace("\n", " ")
            if len(summary) > 250:
                summary = summary[:247] + "..."

            upvotes = paper.get("upvotes", 0)
            url = f"https://huggingface.co/papers/{paper_id}" if paper_id else "https://huggingface.co/papers"

            papers_list.append(
                f"- **[{title}]({url})** (Upvotes: {upvotes})\n  *Summary:* {summary}"
            )

        return "\n\n".join(papers_list)
    except Exception as exc:
        logger.error(f"Error fetching Hugging Face daily papers: {exc}")
        return f"Error retrieving Hugging Face daily papers: {exc}"
