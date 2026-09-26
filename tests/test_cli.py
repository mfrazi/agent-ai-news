# tests/test_cli.py
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from agent_ai_news.cli import app

runner = CliRunner()


def test_cli_research_command():
    with patch("agent_ai_news.cli.run_research_query", return_value="# AI Breakthroughs"), \
         patch("agent_ai_news.cli.save_report") as mock_save:
        mock_save.return_value = MagicMock(as_posix=lambda: "reports/2026-09-26-research-test.md")
        result = runner.invoke(app, ["research", "reasoning models", "--no-publish"])
        assert result.exit_code == 0
        assert "Report saved" in result.output or "AI Breakthroughs" in result.output


def test_cli_digest_command():
    with patch("agent_ai_news.cli.run_research_query", return_value="# Daily Briefing"), \
         patch("agent_ai_news.cli.save_report") as mock_save:
        mock_save.return_value = MagicMock(as_posix=lambda: "reports/2026-09-26-ai-digest.md")
        result = runner.invoke(app, ["digest", "--days", "1", "--no-publish"])
        assert result.exit_code == 0
        assert "Briefing saved" in result.output or "Daily Briefing" in result.output
