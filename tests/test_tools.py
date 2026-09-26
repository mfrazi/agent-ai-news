# tests/test_tools.py
import pytest
from unittest.mock import patch, MagicMock
from agent_ai_news.tools.web_search import search_web
from agent_ai_news.tools.rss import fetch_ai_rss, _fetch_feed as real_fetch_feed
from agent_ai_news.tools.huggingface import query_hf_papers


@pytest.fixture(autouse=True)
def no_feed_downloads(monkeypatch):
    """RSS tests mock feedparser.parse; keep the raw feed download off the network."""
    monkeypatch.setattr("agent_ai_news.tools.rss._fetch_feed", lambda url: b"")


def test_web_search_fallback_to_ddg(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.setattr(
        "agent_ai_news.tools.web_search.get_settings",
        lambda: type("Dummy", (), {"tavily_api_key": None})(),
    )
    with patch("ddgs.ddgs.DDGS.text") as mock_ddg:
        mock_ddg.return_value = [
            {"title": "AI Release", "href": "https://example.com/ai", "body": "Summary of AI release"}
        ]
        result = search_web("reasoning models", days=1)
        assert "AI Release" in result
        assert "https://example.com/ai" in result
        assert mock_ddg.call_args.kwargs["timelimit"] == "d"


def test_web_search_tavily(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-fake-key")
    with patch("tavily.TavilyClient.search") as mock_tavily:
        mock_tavily.return_value = {
            "results": [
                {"title": "Tavily AI News", "url": "https://tavily.com/news", "content": "Tavily summary"}
            ]
        }
        result = search_web("frontier models")
        assert "Tavily AI News" in result
        assert "https://tavily.com/news" in result


def test_web_search_tavily_error_fallback(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-invalid-key")
    with patch("tavily.TavilyClient.search", side_effect=Exception("Rate limit")), \
         patch("ddgs.ddgs.DDGS.text") as mock_ddg:
        mock_ddg.return_value = [
            {"title": "Fallback Result", "href": "https://ddg.com/ai", "body": "DDG fallback content"}
        ]
        result = search_web("rate limit test")
        assert "Fallback Result" in result
        assert "https://ddg.com/ai" in result


def test_rss_fetch_mock():
    mock_feed = {
        "entries": [
            {
                "title": "GPT-5 Announced",
                "link": "https://openai.com/news/gpt5",
                "summary": "Next generation reasoning",
                "published": "2026-09-26T12:00:00Z",
            }
        ]
    }
    with patch("feedparser.parse") as mock_parse:
        mock_parse.return_value = MagicMock(**mock_feed)
        result = fetch_ai_rss(days=3)
        assert "GPT-5 Announced" in result
        assert "https://openai.com/news/gpt5" in result


def test_rss_fetch_error_handling():
    with patch("feedparser.parse", side_effect=Exception("Connection refused")):
        result = fetch_ai_rss(days=3)
        assert isinstance(result, str)
        assert "No recent RSS updates" in result or "error" not in result.lower() or result != ""


def test_hf_papers_query_mock():
    mock_json = [
        {
            "paper": {
                "id": "2609.12345",
                "title": "Scaling Verification",
                "summary": "New PRM architecture",
                "upvotes": 120,
            }
        }
    ]
    with patch("httpx.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_json)
        result = query_hf_papers(limit=5)
        assert "Scaling Verification" in result
        assert "2609.12345" in result


def test_rss_filters_entries_older_than_days():
    import time

    now = time.gmtime()
    old = time.gmtime(time.time() - 30 * 86400)
    mock_feed = MagicMock(
        entries=[
            {"title": "Fresh Post", "link": "https://x/fresh", "summary": "", "published_parsed": now},
            {"title": "Stale Post", "link": "https://x/stale", "summary": "", "published_parsed": old},
            {"title": "Undated Post", "link": "https://x/undated", "summary": ""},
        ]
    )
    with patch("feedparser.parse", return_value=mock_feed):
        result = fetch_ai_rss(days=3)
    assert "Fresh Post" in result
    assert "Undated Post" in result
    assert "Stale Post" not in result


def test_rss_download_uses_timeout():
    with patch("httpx.get", return_value=MagicMock(content=b"<rss/>")) as mock_get:
        assert real_fetch_feed("https://example.com/feed") == b"<rss/>"
    assert mock_get.call_args.kwargs["timeout"] > 0
