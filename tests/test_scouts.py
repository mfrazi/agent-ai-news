# tests/test_scouts.py
from unittest.mock import MagicMock, patch
from langchain_core.language_models.chat_models import BaseChatModel
from agent.core.scouts import create_news_scout_subagent, create_paper_scout_subagent
from agent.core.orchestrator import create_lead_research_agent, run_research_query


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
    assert len(paper_scout["tools"]) == 2

    assert lead_agent is not None


def test_run_research_query_mock():
    mock_graph = MagicMock()
    mock_message = MagicMock(content="# AI Research Report\nKey findings...")
    mock_graph.invoke.return_value = {"messages": [mock_message]}

    with patch("agent.core.orchestrator.create_lead_research_agent", return_value=mock_graph):
        result = run_research_query("reasoning models")
        assert "# AI Research Report" in result
        assert "Key findings..." in result
