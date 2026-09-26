import logging
import time
from uuid import uuid4
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult
from agent_ai_news.core.orchestrator import run_research_query
from agent_ai_news.progress import ProgressCallbackHandler


def test_progress_logs_llm_and_tool_steps(caplog):
    caplog.set_level(logging.INFO, logger="agent_ai_news.progress")
    handler = ProgressCallbackHandler(heartbeat_interval=0)
    with handler:
        llm_run = uuid4()
        handler.on_chat_model_start({}, [[]], run_id=llm_run, metadata={"lc_agent_name": "news_scout"})
        message = AIMessage(content="", tool_calls=[{"name": "search_web", "args": {}, "id": "1"}])
        handler.on_llm_end(LLMResult(generations=[[ChatGeneration(message=message)]]), run_id=llm_run)

        task_run = uuid4()
        handler.on_tool_start(
            {"name": "task"},
            "",
            run_id=task_run,
            inputs={"subagent_type": "academic_paper_scout", "description": "Find test-time compute papers"},
        )
        handler.on_tool_end("paper list", run_id=task_run)

    logs = caplog.text
    assert "LLM call #1 (news_scout) started" in logs
    assert "requested tools: search_web" in logs
    assert "subagent 'academic_paper_scout' started: Find test-time compute papers" in logs
    assert "subagent 'academic_paper_scout' finished" in logs
    assert "1 LLM calls, 1 tool calls" in logs


def test_progress_heartbeat_reports_slow_step(caplog):
    caplog.set_level(logging.INFO, logger="agent_ai_news.progress")
    with ProgressCallbackHandler(heartbeat_interval=0.05) as handler:
        handler.on_tool_start({"name": "search_web"}, "query", run_id=uuid4())
        time.sleep(0.2)
    assert "waiting on: tool 'search_web'" in caplog.text


def test_run_research_query_passes_progress_callbacks_and_step_limit():
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {"messages": [MagicMock(content="Findings.")]}
    with patch("agent_ai_news.core.orchestrator.create_lead_research_agent", return_value=mock_graph):
        run_research_query("reasoning models")
    config = mock_graph.invoke.call_args.kwargs["config"]
    assert isinstance(config["callbacks"][0], ProgressCallbackHandler)
    assert config["recursion_limit"] > 0
