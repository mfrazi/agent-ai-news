# tests/conftest.py
import pytest
from pydantic import AliasChoices
from agent_ai_news.config import Settings, get_settings


def _settings_env_vars():
    """Every environment variable Settings reads, including aliases such as GEMINI_API_KEY."""
    names = set()
    for field_name, field in Settings.model_fields.items():
        if isinstance(field.validation_alias, AliasChoices):
            names.update(str(choice).upper() for choice in field.validation_alias.choices)
        else:
            names.add(field_name.upper())
    return sorted(names)


SETTINGS_ENV_VARS = _settings_env_vars()


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch):
    """Keep the developer's real .env file and shell keys out of every test."""
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    for var in SETTINGS_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
