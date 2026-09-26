"""Lead research DeepAgent orchestrator."""

from typing import Any, Optional
from deepagents import create_deep_agent
from agent.llm import get_chat_model
from agent.core.scouts import create_news_scout_subagent, create_paper_scout_subagent

LEAD_AGENT_SYSTEM_PROMPT = """You are the Lead AI Intelligence Research Agent.
Your mission is to produce authoritative, highly structured research briefings and digests on Artificial Intelligence.

You have access to two specialized subagents:
1. 'news_scout': Dispatches web searches and retrieves AI lab RSS feeds.
2. 'academic_paper_scout': Dispatches arXiv searches and queries Hugging Face daily papers.

When addressing a topic or compiling a briefing:
1. Plan your search strategy using the todo tool.
2. Delegate web/industry searches to 'news_scout'.
3. Delegate academic/technical paper searches to 'academic_paper_scout'.
4. Synthesize all findings into a cohesive, cited markdown report following this structure:
   - Executive Summary (3-5 key bullets)
   - 1. Industry & Lab Announcements (with lab names and source links)
   - 2. Academic & Frontier Research (with titles, authors, arXiv/HF links, core technical contributions)
   - 3. Open Source Releases & Weights (model names, weights/code URLs)
   - 4. Synthesis & Emerging Trends (high-level takeaway on where the field is moving)
"""


def create_lead_research_agent(model: Any = None):
    """Instantiate the Lead Research Deep Agent with subagent delegation."""
    llm = model if model is not None else get_chat_model()
    news_scout = create_news_scout_subagent(llm)
    paper_scout = create_paper_scout_subagent(llm)

    agent_graph = create_deep_agent(
        model=llm,
        subagents=[news_scout, paper_scout],
        system_prompt=LEAD_AGENT_SYSTEM_PROMPT,
    )
    return agent_graph


def run_research_query(query: str, model: Any = None, report_type: str = "research") -> str:
    """Execute a research query using the lead agent and return the resulting report content."""
    agent = create_lead_research_agent(model=model)
    result = agent.invoke({"messages": [{"role": "user", "content": query}]})
    messages = result.get("messages", [])
    raw_content = "No report generated."
    if messages:
        last_message = messages[-1]
        raw_content = getattr(last_message, "content", str(last_message))

    from agent.core.synthesizer import normalize_to_report_markdown
    return normalize_to_report_markdown(raw_content, title=query, report_type=report_type)

