# tests/test_tools.py
from unittest.mock import patch, MagicMock
from agent_ai_news.tools.web_search import search_web
from agent_ai_news.tools.rss import fetch_ai_rss
from agent_ai_news.tools.arxiv import query_arxiv
from agent_ai_news.tools.huggingface import query_hf_papers


def test_web_search_fallback_to_ddg(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    with patch("duckduckgo_search.DDGS.text") as mock_ddg:
        mock_ddg.return_value = [
            {"title": "AI Release", "href": "https://example.com/ai", "body": "Summary of AI release"}
        ]
        result = search_web("reasoning models")
        assert "AI Release" in result
        assert "https://example.com/ai" in result


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
         patch("duckduckgo_search.DDGS.text") as mock_ddg:
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


def test_arxiv_query_mock():
    mock_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Deep Reasoning in LLMs</title>
        <summary>Novel test-time compute scaling.</summary>
        <id>http://arxiv.org/abs/2609.99999</id>
        <author><name>Alice Smith</name></author>
      </entry>
    </feed>"""
    with patch("httpx.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, content=mock_xml)
        result = query_arxiv("reasoning models")
        assert "Deep Reasoning in LLMs" in result
        assert "Alice Smith" in result


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
