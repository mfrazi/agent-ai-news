# tests/test_config.py
from pathlib import Path
from agent_ai_news.config import ENV_FILES, PROJECT_ENV_FILE, Settings

def test_settings_default_values():
    settings = Settings(_env_file=None)
    project_root = Path(__file__).resolve().parent.parent
    assert settings.site_docs_dir == str(project_root / "site_docs")
    assert settings.agent_llm_provider is None
    assert settings.agent_api_key is None

def test_settings_auto_detect_provider(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test12345")
    settings = Settings(_env_file=None)
    assert settings.resolve_provider() == "openrouter"

def test_settings_explicit_provider(monkeypatch):
    monkeypatch.setenv("AGENT_LLM_PROVIDER", "gemini")
    settings = Settings(_env_file=None)
    assert settings.resolve_provider() == "gemini"


def test_settings_openrouter_provider_settings(monkeypatch):
    monkeypatch.setenv("OPENROUTER_PROVIDERS", "Together, DeepInfra")
    monkeypatch.setenv("OPENROUTER_ALLOW_FALLBACKS", "false")
    settings = Settings(_env_file=None)
    assert settings.openrouter_providers == "Together, DeepInfra"
    assert settings.openrouter_allow_fallbacks is False


def test_settings_reads_project_env_file_from_any_directory():
    project_root = Path(__file__).resolve().parent.parent
    assert PROJECT_ENV_FILE == project_root / ".env"
    # Project .env is loaded first; a .env in the working directory overrides it
    assert ENV_FILES == (PROJECT_ENV_FILE, ".env")


def test_output_dirs_do_not_depend_on_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    settings = Settings(_env_file=None)
    project_root = Path(__file__).resolve().parent.parent
    assert settings.site_docs_dir == str(project_root / "site_docs")


def test_absolute_output_dir_is_kept(tmp_path, monkeypatch):
    monkeypatch.setenv("SITE_DOCS_DIR", str(tmp_path / "out"))
    settings = Settings(_env_file=None)
    assert settings.site_docs_dir == str(tmp_path / "out")


def test_gemini_api_key_is_alias_for_google_api_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    assert Settings(_env_file=None).google_api_key == "gemini-key"
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    assert Settings(_env_file=None).google_api_key == "google-key"
