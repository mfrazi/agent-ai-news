"""Configuration module for agent-ai-news."""

from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repository root for source/editable installs, so the CLI behaves the same from any directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# .env next to the project root; a .env in the current working directory is listed last and wins.
PROJECT_ENV_FILE = PROJECT_ROOT / ".env"
ENV_FILES = (PROJECT_ENV_FILE, ".env")


def output_base_dir() -> Path:
    """Directory that relative output paths resolve against.

    The project root for a source checkout or editable install. A regular install lives in
    site-packages, where writing reports makes no sense, so fall back to the working directory.
    """
    if (PROJECT_ROOT / "pyproject.toml").is_file():
        return PROJECT_ROOT
    return Path.cwd()


class Settings(BaseSettings):
    """Application settings loaded from environment and .env file."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
        validate_default=True,
    )

    # Provider & Model Settings
    agent_llm_provider: Optional[str] = None
    agent_model_name: Optional[str] = None
    openrouter_providers: Optional[str] = None
    openrouter_provider: Optional[str] = None
    openrouter_allow_fallbacks: Optional[bool] = None

    # API Keys
    openrouter_api_key: Optional[str] = None
    google_api_key: Optional[str] = Field(default=None, validation_alias=AliasChoices("GOOGLE_API_KEY", "GEMINI_API_KEY"))
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None

    # Key clients must send in the X-API-Key header; a temporary one is generated per server process if unset
    agent_api_key: Optional[str] = None

    # Agent runtime limits (a stalled request or runaway loop otherwise looks like a hang)
    llm_timeout_seconds: float = 120.0
    llm_max_retries: int = 2
    agent_recursion_limit: int = 200
    progress_heartbeat_seconds: float = 30.0

    # MkDocs source directory; reports are saved to its research/ and digests/ subfolders
    site_docs_dir: str = "site_docs"

    @field_validator("site_docs_dir")
    @classmethod
    def _anchor_relative_dir(cls, value: str) -> str:
        """Resolve a relative directory against the project, not wherever the command was run."""
        path = Path(value).expanduser()
        return str(path if path.is_absolute() else output_base_dir() / path)

    def resolve_provider(self) -> str:
        """Resolve LLM provider based on explicit config or detected keys.

        Priority order:
        1. agent_llm_provider (if explicitly configured)
        2. openrouter (if OPENROUTER_API_KEY is present)
        3. gemini (if GOOGLE_API_KEY is present)
        4. openai (if OPENAI_API_KEY is present)
        5. anthropic (if ANTHROPIC_API_KEY is present)
        """
        if self.agent_llm_provider:
            return self.agent_llm_provider.lower().strip()

        if self.openrouter_api_key:
            return "openrouter"
        if self.google_api_key:
            return "gemini"
        if self.openai_api_key:
            return "openai"
        if self.anthropic_api_key:
            return "anthropic"

        return "openrouter"


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
