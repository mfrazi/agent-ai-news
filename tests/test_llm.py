# tests/test_llm.py
import pytest
from unittest.mock import patch
from agent_ai_news.llm import MissingCredentialsError, get_chat_model

def test_get_chat_model_openrouter(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-dummy")
    with patch("langchain_openai.ChatOpenAI") as mock_chat:
        get_chat_model(provider="openrouter", model_name="anthropic/claude-sonnet-5")
        mock_chat.assert_called_once()
        kwargs = mock_chat.call_args.kwargs
        assert str(kwargs.get("base_url")).rstrip("/") == "https://openrouter.ai/api/v1"
        assert kwargs.get("model") == "anthropic/claude-sonnet-5"
        assert "HTTP-Referer" in kwargs.get("default_headers", {})
        assert kwargs.get("api_key") == "sk-or-dummy"
        assert "extra_body" not in kwargs


def test_get_chat_model_openrouter_with_providers_args(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-dummy")
    with patch("langchain_openai.ChatOpenAI") as mock_chat:
        get_chat_model(
            provider="openrouter",
            model_name="meta-llama/llama-3.3-70b-instruct",
            openrouter_providers=["Together", "DeepInfra"],
            openrouter_allow_fallbacks=False,
        )
        mock_chat.assert_called_once()
        kwargs = mock_chat.call_args.kwargs
        assert "extra_body" in kwargs
        assert kwargs["extra_body"] == {
            "provider": {
                "order": ["Together", "DeepInfra"],
                "allow_fallbacks": False,
            }
        }


def test_get_chat_model_openrouter_with_providers_env(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-dummy")
    monkeypatch.setenv("OPENROUTER_PROVIDERS", "Together, DeepInfra")
    monkeypatch.setenv("OPENROUTER_ALLOW_FALLBACKS", "true")
    with patch("langchain_openai.ChatOpenAI") as mock_chat:
        get_chat_model(provider="openrouter")
        mock_chat.assert_called_once()
        kwargs = mock_chat.call_args.kwargs
        assert "extra_body" in kwargs
        assert kwargs["extra_body"] == {
            "provider": {
                "order": ["Together", "DeepInfra"],
                "allow_fallbacks": True,
            }
        }

def test_get_chat_model_gemini(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-gemini-key")
    with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_chat:
        get_chat_model(provider="gemini", model_name="gemini-2.0-flash")
        mock_chat.assert_called_once()
        kwargs = mock_chat.call_args.kwargs
        assert kwargs.get("model") == "gemini-2.0-flash"
        assert kwargs.get("google_api_key") == "fake-gemini-key"

def test_get_chat_model_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-openai")
    with patch("langchain_openai.ChatOpenAI") as mock_chat:
        get_chat_model(provider="openai", model_name="gpt-4o")
        mock_chat.assert_called_once()
        kwargs = mock_chat.call_args.kwargs
        assert kwargs.get("model") == "gpt-4o"
        assert kwargs.get("api_key") == "sk-fake-openai"

def test_get_chat_model_anthropic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
    with patch("langchain_anthropic.ChatAnthropic") as mock_chat:
        get_chat_model(provider="anthropic", model_name="claude-sonnet-5")
        mock_chat.assert_called_once()
        kwargs = mock_chat.call_args.kwargs
        assert kwargs.get("model_name") == "claude-sonnet-5"
        assert kwargs.get("api_key") == "sk-ant-fake"

def test_get_chat_model_unsupported():
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        get_chat_model(provider="unknown_provider")


@pytest.mark.parametrize(
    "provider, env_var",
    [
        ("openrouter", "OPENROUTER_API_KEY"),
        ("gemini", "GOOGLE_API_KEY"),
        ("openai", "OPENAI_API_KEY"),
        ("anthropic", "ANTHROPIC_API_KEY"),
    ],
)
def test_get_chat_model_missing_key_names_env_var(provider, env_var):
    with pytest.raises(MissingCredentialsError, match=env_var):
        get_chat_model(provider=provider)
