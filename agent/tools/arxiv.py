"""arXiv research paper query tool."""

import logging
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List
import httpx

logger = logging.getLogger(__name__)

ARXIV_API_BASE = "http://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def query_arxiv(topic: str, max_results: int = 5, categories: List[str] = None) -> str:
    """Query the arXiv API for recent machine learning and AI papers on a topic."""
    if categories is None:
        categories = ["cs.AI", "cs.LG", "cs.CL"]

    cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
    search_query = f"({cat_query}) AND all:{topic}"
    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    try:
        response = httpx.get(ARXIV_API_BASE, params=params, timeout=15.0)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        entries = root.findall("atom:entry", ATOM_NS)
        if not entries:
            return f"No arXiv papers found matching topic: '{topic}'."

        formatted_papers = []
        for entry in entries:
            title_elem = entry.find("atom:title", ATOM_NS)
            title = title_elem.text.strip().replace("\n", " ") if title_elem is not None else "Untitled"

            id_elem = entry.find("atom:id", ATOM_NS)
            link = id_elem.text.strip() if id_elem is not None else ""

            summary_elem = entry.find("atom:summary", ATOM_NS)
            summary = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None else ""
            if len(summary) > 300:
                summary = summary[:297] + "..."

            authors = [
                author.find("atom:name", ATOM_NS).text
                for author in entry.findall("atom:author", ATOM_NS)
                if author.find("atom:name", ATOM_NS) is not None
            ]
            authors_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")

            formatted_papers.append(
                f"- **[{title}]({link})**\n  *Authors:* {authors_str}\n  *Summary:* {summary}"
            )

        return "\n\n".join(formatted_papers)
    except Exception as exc:
        logger.error(f"Error querying arXiv for '{topic}': {exc}")
        return f"Error retrieving arXiv papers for '{topic}': {exc}"
