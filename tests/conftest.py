# tests/conftest.py
import pytest
from agent_ai_news.config import Settings, get_settings

# Every variable Settings reads (plus GEMINI_API_KEY, an alias of GOOGLE_API_KEY)
SETTINGS_ENV_VARS = [name.upper() for name in Settings.model_fields] + ["GEMINI_API_KEY"]


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch):
    """Keep the developer's real .env file and shell keys out of every test."""
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    for var in SETTINGS_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
