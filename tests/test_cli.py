# tests/test_cli.py
from typer.testing import CliRunner
from unittest.mock import patch
from agent_ai_news.cli import app

runner = CliRunner()


def test_cli_research_command():
    with patch("agent_ai_news.cli.run_research_query", return_value="# AI Breakthroughs"), \
         patch("agent_ai_news.cli.save_report", return_value="site_docs/research/2026-09-26-research-test.md"), \
         patch("agent_ai_news.cli.rebuild_site_index") as mock_index:
        result = runner.invoke(app, ["research", "reasoning models"])
        assert result.exit_code == 0
        assert "Report saved" in result.output
        mock_index.assert_called_once()


def test_cli_digest_command():
    with patch("agent_ai_news.cli.run_research_query", return_value="# Daily Briefing"), \
         patch("agent_ai_news.cli.save_report", return_value="site_docs/digests/2026-09-26-ai-digest.md"), \
         patch("agent_ai_news.cli.rebuild_site_index") as mock_index:
        result = runner.invoke(app, ["digest", "--days", "1"])
        assert result.exit_code == 0
        assert "Briefing saved" in result.output
        mock_index.assert_called_once()
