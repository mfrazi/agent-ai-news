"""Domain-specific scout subagents for news and academic literature."""

from typing import Any, Dict
from deepagents import SubAgent
from agent.tools.web_search import search_web
from agent.tools.rss import fetch_ai_rss
from agent.tools.arxiv import query_arxiv
from agent.tools.huggingface import query_hf_papers


def create_news_scout_subagent(model: Any = None) -> SubAgent:
    """Create the News & Web Scout subagent profile."""
    prompt = (
        "You are an AI News & Web Scout. Your role is to discover the latest breaking announcements, "
        "model launches, benchmarks, and industry news from major AI labs (OpenAI, Google DeepMind, "
        "Anthropic, Meta AI, Mistral) and the web. Use web_search and fetch_ai_rss to find fresh information."
    )
    subagent: SubAgent = {
        "name": "news_scout",
        "description": "Scouts breaking AI lab releases, benchmarks, industry news, and web articles.",
        "tools": [search_web, fetch_ai_rss],
        "system_prompt": prompt,
        "mode": "isolated",
    }
    if model is not None:
        subagent["model"] = model
    return subagent


def create_paper_scout_subagent(model: Any = None) -> SubAgent:
    """Create the Academic & Technical Paper Scout subagent profile."""
    prompt = (
        "You are an Academic Paper Scout specialized in frontier AI research. Your job is to search "
        "arXiv and Hugging Face Daily Papers for breakthroughs in model architectures, reasoning techniques, "
        "multimodal systems, and open-weights releases. Use query_arxiv and query_hf_papers to gather paper details."
    )
    subagent: SubAgent = {
        "name": "academic_paper_scout",
        "description": "Searches arXiv and Hugging Face for the latest AI papers, technical contributions, and code.",
        "tools": [query_arxiv, query_hf_papers],
        "system_prompt": prompt,
        "mode": "isolated",
    }
    if model is not None:
        subagent["model"] = model
    return subagent
