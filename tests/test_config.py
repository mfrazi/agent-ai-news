# tests/test_config.py
import os
import pytest
from agent_ai_news.config import Settings, get_settings

def test_settings_default_values(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AGENT_LLM_PROVIDER", raising=False)
    settings = Settings(_env_file=None)
    assert settings.reports_dir == "reports"
    assert settings.site_docs_dir == "site_docs"
    assert settings.default_llm_provider is None

def test_settings_auto_detect_provider(monkeypatch):
    monkeypatch.delenv("AGENT_LLM_PROVIDER", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test12345")
    settings = Settings(_env_file=None)
    assert settings.resolve_provider() == "openrouter"

def test_settings_explicit_provider(monkeypatch):
    monkeypatch.setenv("AGENT_LLM_PROVIDER", "gemini")
    settings = Settings(_env_file=None)
    assert settings.resolve_provider() == "gemini"
