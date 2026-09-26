# tests/test_scouts.py
from unittest.mock import MagicMock, patch
from langchain_core.language_models.chat_models import BaseChatModel
from agent_ai_news.core.scouts import create_news_scout_subagent, create_paper_scout_subagent
from agent_ai_news.core.orchestrator import create_lead_research_agent, run_research_query


def test_scout_agents_creation():
    mock_model = MagicMock(spec=BaseChatModel)
    mock_model.profile = None
    mock_model.bind_tools = MagicMock(return_value=mock_model)

    news_scout = create_news_scout_subagent(mock_model)
    paper_scout = create_paper_scout_subagent(mock_model)
    lead_agent = create_lead_research_agent(mock_model)

    assert news_scout is not None
    assert news_scout["name"] == "news_scout"
    assert len(news_scout["tools"]) == 2

    assert paper_scout is not None
    assert paper_scout["name"] == "academic_paper_scout"
    assert [t.__name__ for t in paper_scout["tools"]] == ["query_hf_papers", "search_web"]

    assert lead_agent is not None


def test_run_research_query_mock():
    mock_graph = MagicMock()
    mock_message = MagicMock(content="# AI Research Report\nKey findings...")
    mock_graph.invoke.return_value = {"messages": [mock_message]}

    with patch("agent_ai_news.core.orchestrator.create_lead_research_agent", return_value=mock_graph):
        result = run_research_query("reasoning models")
        assert "# AI Research Report" in result
        assert "Key findings..." in result


def test_run_research_query_content_blocks():
    """Anthropic/Gemini models return content as a list of blocks, not a string."""
    mock_graph = MagicMock()
    mock_message = MagicMock(
        content=[
            {"type": "text", "text": "Block one findings."},
            {"type": "tool_use", "id": "t1", "name": "task", "input": {}},
            {"type": "text", "text": "Block two findings."},
        ]
    )
    mock_graph.invoke.return_value = {"messages": [mock_message]}

    with patch("agent_ai_news.core.orchestrator.create_lead_research_agent", return_value=mock_graph):
        result = run_research_query("reasoning models", report_type="digest")
        assert "Block one findings." in result
        assert "Block two findings." in result
        assert "tool_use" not in result
        assert "type: digest" in result


def test_prompts_name_real_tools_and_distrust_tool_output():
    from agent_ai_news.core.orchestrator import LEAD_AGENT_SYSTEM_PROMPT
    from agent_ai_news.core.scouts import UNTRUSTED_CONTENT_RULE

    assert UNTRUSTED_CONTENT_RULE in LEAD_AGENT_SYSTEM_PROMPT
    for scout in (create_news_scout_subagent(), create_paper_scout_subagent()):
        assert UNTRUSTED_CONTENT_RULE in scout["system_prompt"]
        # every tool the prompt tells the model to use must exist under that name
        tool_names = {t.__name__ for t in scout["tools"]}
        for name in ("search_web", "fetch_ai_rss", "query_hf_papers", "web_search"):
            if name in scout["system_prompt"]:
                assert name in tool_names, f"{scout['name']} prompt mentions missing tool {name}"


def test_build_digest_query():
    from agent_ai_news.core.orchestrator import DEFAULT_DIGEST_TOPIC, build_digest_query

    assert build_digest_query(1, "Robotics") == "Compile an AI intelligence digest for the past day covering: Robotics"
    assert build_digest_query(7, "") == f"Compile an AI intelligence digest for the past 7 days covering: {DEFAULT_DIGEST_TOPIC}"


def test_lead_prompt_names_real_planning_tool():
    from agent_ai_news.core.orchestrator import LEAD_AGENT_SYSTEM_PROMPT

    assert "write_todos" in LEAD_AGENT_SYSTEM_PROMPT
