"""Lead research DeepAgent orchestrator."""

import logging
from typing import Any, List, Optional, Union
from deepagents import create_deep_agent
from agent_ai_news.config import get_settings
from agent_ai_news.llm import get_chat_model
from agent_ai_news.progress import ProgressCallbackHandler
from agent_ai_news.core.scouts import UNTRUSTED_CONTENT_RULE, create_news_scout_subagent, create_paper_scout_subagent
from agent_ai_news.core.synthesizer import normalize_to_report_markdown

logger = logging.getLogger(__name__)

LEAD_AGENT_SYSTEM_PROMPT = """You are the Lead AI Intelligence Research Agent.
Your mission is to produce authoritative, highly structured research briefings and digests on Artificial Intelligence.

You have access to two specialized subagents:
1. 'news_scout': Dispatches web searches and retrieves AI lab RSS feeds.
2. 'academic_paper_scout': Queries Hugging Face daily papers and searches the web for research papers.

When addressing a topic or compiling a briefing:
1. Plan your search strategy using the write_todos tool.
2. Delegate web/industry searches to 'news_scout'.
3. Delegate academic/technical paper searches to 'academic_paper_scout'.
4. Synthesize all findings into a cohesive, cited markdown report following this structure:
   - Executive Summary (3-5 key bullets)
   - 1. Industry & Lab Announcements (with lab names and source links)
   - 2. Academic & Frontier Research (with titles, authors, paper links, core technical contributions)
   - 3. Open Source Releases & Weights (model names, weights/code URLs)
   - 4. Synthesis & Emerging Trends (high-level takeaway on where the field is moving)

""" + UNTRUSTED_CONTENT_RULE


def create_lead_research_agent(
    model: Any = None,
    openrouter_providers: Optional[Union[str, List[str]]] = None,
):
    """Instantiate the Lead Research Deep Agent with subagent delegation."""
    llm = model if model is not None else get_chat_model(openrouter_providers=openrouter_providers)
    news_scout = create_news_scout_subagent(llm)
    paper_scout = create_paper_scout_subagent(llm)

    return create_deep_agent(
        model=llm,
        subagents=[news_scout, paper_scout],
        system_prompt=LEAD_AGENT_SYSTEM_PROMPT,
    )


DEFAULT_DIGEST_TOPIC = "General AI, Frontier Models, Open Weights"


def build_digest_query(days: int, topic: str = DEFAULT_DIGEST_TOPIC) -> str:
    """Research request sent to the lead agent for a digest (shared by the CLI and the API)."""
    period = "day" if days == 1 else f"{days} days"
    return f"Compile an AI intelligence digest for the past {period} covering: {topic or DEFAULT_DIGEST_TOPIC}"


def _message_text(content: Any) -> str:
    """Flatten message content into plain text.

    Anthropic and Gemini chat models return a list of content blocks instead of a string.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(p for p in parts if p)
    return str(content)


def run_research_query(
    query: str,
    report_type: str = "research",
    openrouter_providers: Optional[Union[str, List[str]]] = None,
) -> str:
    """Execute a research query using the lead agent and return the resulting report content."""
    agent = create_lead_research_agent(openrouter_providers=openrouter_providers)
    settings = get_settings()
    logger.info("Running lead research agent (step limit %d)", settings.agent_recursion_limit)
    with ProgressCallbackHandler(heartbeat_interval=settings.progress_heartbeat_seconds) as progress:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config={"callbacks": [progress], "recursion_limit": settings.agent_recursion_limit},
        )
    messages = result.get("messages", [])
    raw_content = "No report generated."
    if messages:
        last_message = messages[-1]
        raw_content = _message_text(getattr(last_message, "content", str(last_message))) or raw_content

    return normalize_to_report_markdown(raw_content, title=query, report_type=report_type)

