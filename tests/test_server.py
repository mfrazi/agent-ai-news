# tests/test_server.py
import logging
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from agent_ai_news import server
from agent_ai_news.server import app

TEST_KEY = "test-api-key"
REAL_API_KEY = server._api_key
client = TestClient(app, headers={"X-API-Key": TEST_KEY})
anonymous = TestClient(app)


@pytest.fixture(autouse=True)
def fixed_api_key(monkeypatch):
    monkeypatch.setattr(server, "_api_key", lambda: TEST_KEY)
    yield
    REAL_API_KEY.cache_clear()


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_research_endpoint():
    with patch("agent_ai_news.server.run_research_query", return_value="Sample research findings"), \
         patch("agent_ai_news.server.save_report", return_value="site_docs/research/x.md"), \
         patch("agent_ai_news.server.rebuild_site_index") as mock_index:
        response = client.post("/api/research", json={"query": "Test AI"})
        assert response.status_code == 200
        data = response.json()
        assert data["report_path"] == "site_docs/research/x.md"
        assert "content" in data
        mock_index.assert_called_once()


def test_api_digest_endpoint():
    with patch("agent_ai_news.server.run_research_query", return_value="Daily AI Digest content"), \
         patch("agent_ai_news.server.save_report", return_value="site_docs/digests/x.md"), \
         patch("agent_ai_news.server.rebuild_site_index") as mock_index:
        response = client.post("/api/digest", json={"days": 1, "topics": ["AI"]})
        assert response.status_code == 200
        assert "report_path" in response.json()
        mock_index.assert_called_once()


def _site_docs_settings(monkeypatch, site_docs):
    monkeypatch.setattr(
        "agent_ai_news.server.get_settings",
        lambda: type("Dummy", (), {"site_docs_dir": str(site_docs)})(),
    )


def test_list_and_get_reports_from_site_docs(tmp_path, monkeypatch):
    site_docs = tmp_path / "site_docs"
    (site_docs / "research").mkdir(parents=True)
    (site_docs / "digests").mkdir()
    (site_docs / "research" / "2026-09-26-research-a.md").write_text("# A", encoding="utf-8")
    (site_docs / "digests" / "2026-09-26-ai-digest.md").write_text("# D", encoding="utf-8")
    _site_docs_settings(monkeypatch, site_docs)

    listed = client.get("/api/reports").json()["reports"]
    assert {(r["filename"], r["type"]) for r in listed} == {
        ("2026-09-26-research-a.md", "research"),
        ("2026-09-26-ai-digest.md", "digest"),
    }
    assert client.get("/api/reports/2026-09-26-ai-digest.md").json()["content"] == "# D"


def test_get_report_rejects_path_traversal(tmp_path, monkeypatch):
    site_docs = tmp_path / "site_docs"
    (site_docs / "research").mkdir(parents=True)
    (site_docs / "research" / "ok.md").write_text("# OK", encoding="utf-8")
    (site_docs / "index.md").write_text("index", encoding="utf-8")
    _site_docs_settings(monkeypatch, site_docs)

    assert client.get("/api/reports/ok.md").status_code == 200
    assert client.get("/api/reports/..%2Findex.md").status_code == 404
    assert client.get("/api/reports/..").status_code == 404


def test_api_digest_rejects_non_positive_days():
    # Patch the agent so a validation regression never triggers real LLM calls
    with patch("agent_ai_news.server.run_research_query") as mock_run, \
         patch("agent_ai_news.server.save_report"), \
         patch("agent_ai_news.server.rebuild_site_index"):
        response = client.post("/api/digest", json={"days": 0})
        assert response.status_code == 422
        mock_run.assert_not_called()


def test_health_does_not_need_api_key():
    assert anonymous.get("/health").status_code == 200


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "wrong"}, {"X-API-Key": ""}])
def test_api_rejects_missing_or_wrong_key(headers):
    with patch("agent_ai_news.server.run_research_query") as mock_run:
        assert anonymous.get("/api/reports", headers=headers).status_code == 401
        assert anonymous.post("/api/research", json={"query": "Test AI"}, headers=headers).status_code == 401
        assert anonymous.post("/api/digest", json={}, headers=headers).status_code == 401
        mock_run.assert_not_called()


def test_configured_api_key_is_used(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "configured-key")
    REAL_API_KEY.cache_clear()
    assert REAL_API_KEY() == "configured-key"


def test_temporary_api_key_generated_and_logged_when_unset(caplog):
    REAL_API_KEY.cache_clear()
    with caplog.at_level(logging.WARNING, logger="agent_ai_news.server"):
        key = REAL_API_KEY()
    assert len(key) >= 32
    assert REAL_API_KEY() == key  # stable for the lifetime of the process
    assert key in caplog.text


@pytest.mark.parametrize(
    "path, body",
    [
        ("/api/research", {"query": "x" * 501}),
        ("/api/research", {"query": "ab"}),
        ("/api/digest", {"days": 366}),
        ("/api/digest", {"topics": ["AI"] * 11}),
        ("/api/digest", {"topics": ["x" * 101]}),
    ],
)
def test_api_rejects_oversized_requests(path, body):
    with patch("agent_ai_news.server.run_research_query") as mock_run:
        assert client.post(path, json=body).status_code == 422
        mock_run.assert_not_called()
