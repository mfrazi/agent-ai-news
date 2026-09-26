# tests/test_server.py
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from agent_ai_news.server import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_research_endpoint():
    with patch("agent_ai_news.server.run_research_query", return_value="Sample research findings"), \
         patch("agent_ai_news.server.save_report") as mock_save:
        mock_save.return_value = MagicMock(name="reports/2026-09-26-research-test.md", as_posix=lambda: "reports/2026-09-26-research-test.md")
        response = client.post("/api/research", json={"query": "Test AI", "publish": False})
        assert response.status_code == 200
        data = response.json()
        assert "report_path" in data
        assert "content" in data


def test_api_digest_endpoint():
    with patch("agent_ai_news.server.run_research_query", return_value="Daily AI Digest content"), \
         patch("agent_ai_news.server.save_report") as mock_save:
        mock_save.return_value = MagicMock(name="reports/2026-09-26-ai-digest.md", as_posix=lambda: "reports/2026-09-26-ai-digest.md")
        response = client.post("/api/digest", json={"days": 1, "topics": ["AI"], "publish": False})
        assert response.status_code == 200
        data = response.json()
        assert "report_path" in data
