"""Configuration module for AI Intelligence Agent."""

import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Provider & Model Settings
    agent_llm_provider: Optional[str] = None
    agent_model_name: Optional[str] = None

    # API Keys
    openrouter_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None

    # Workspace & Output Directories
    reports_dir: str = "reports"
    site_docs_dir: str = "site_docs"
    agent_workspace_dir: str = ".agent_workspace"

    @property
    def default_llm_provider(self) -> Optional[str]:
        """Backward compatibility / alias for agent_llm_provider."""
        return self.agent_llm_provider

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
