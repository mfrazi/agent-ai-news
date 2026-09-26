# tests/test_llm.py
import pytest
from unittest.mock import patch
from agent.config import get_settings
from agent.llm import get_chat_model

@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()

def test_get_chat_model_openrouter(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-dummy")
    with patch("langchain_openai.ChatOpenAI") as mock_chat:
        model = get_chat_model(provider="openrouter", model_name="anthropic/claude-3.5-sonnet")
        mock_chat.assert_called_once()
        kwargs = mock_chat.call_args.kwargs
        assert str(kwargs.get("base_url")).rstrip("/") == "https://openrouter.ai/api/v1"
        assert kwargs.get("model") == "anthropic/claude-3.5-sonnet"
        assert "HTTP-Referer" in kwargs.get("default_headers", {})
        assert kwargs.get("api_key") == "sk-or-dummy"

def test_get_chat_model_gemini(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-gemini-key")
    with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_chat:
        model = get_chat_model(provider="gemini", model_name="gemini-2.0-flash")
        mock_chat.assert_called_once()
        kwargs = mock_chat.call_args.kwargs
        assert kwargs.get("model") == "gemini-2.0-flash"
        assert kwargs.get("google_api_key") == "fake-gemini-key"

def test_get_chat_model_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-openai")
    with patch("langchain_openai.ChatOpenAI") as mock_chat:
        model = get_chat_model(provider="openai", model_name="gpt-4o")
        mock_chat.assert_called_once()
        kwargs = mock_chat.call_args.kwargs
        assert kwargs.get("model") == "gpt-4o"
        assert kwargs.get("api_key") == "sk-fake-openai"

def test_get_chat_model_anthropic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
    with patch("langchain_anthropic.ChatAnthropic") as mock_chat:
        model = get_chat_model(provider="anthropic", model_name="claude-3-5-sonnet-20241022")
        mock_chat.assert_called_once()
        kwargs = mock_chat.call_args.kwargs
        assert kwargs.get("model_name") == "claude-3-5-sonnet-20241022"
        assert kwargs.get("api_key") == "sk-ant-fake"

def test_get_chat_model_unsupported():
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        get_chat_model(provider="unknown_provider")
