"""Provider-agnostic LLM Factory for agent-ai-news."""

from typing import List, Optional, Union
from langchain_core.language_models.chat_models import BaseChatModel
from agent_ai_news.config import PROJECT_ENV_FILE, get_settings


class MissingCredentialsError(ValueError):
    """Raised when the selected LLM provider has no API key configured."""


def _require_api_key(api_key: Optional[str], provider: str, env_var: str) -> str:
    """Fail fast with an actionable message instead of the provider SDK's generic error."""
    if not api_key:
        raise MissingCredentialsError(
            f"No API key found for LLM provider '{provider}'. Set {env_var} in the environment, "
            f"in {PROJECT_ENV_FILE}, or in a .env file in the current directory."
        )
    return api_key


def get_chat_model(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.2,
    openrouter_providers: Optional[Union[str, List[str]]] = None,
    openrouter_allow_fallbacks: Optional[bool] = None,
) -> BaseChatModel:
    """Instantiate and return a BaseChatModel according to provider and configuration."""
    settings = get_settings()
    active_provider = (provider or settings.resolve_provider()).lower().strip()

    if active_provider == "openrouter":
        from langchain_openai import ChatOpenAI

        chosen_model = model_name or settings.agent_model_name or "anthropic/claude-sonnet-5"
        api_key = _require_api_key(settings.openrouter_api_key, "openrouter", "OPENROUTER_API_KEY")
        kwargs = {
            "model": chosen_model,
            "api_key": api_key,
            "base_url": "https://openrouter.ai/api/v1",
            # OpenRouter app attribution
            "default_headers": {
                "HTTP-Referer": "https://github.com/mfrazi/agent-ai-news",
                "X-Title": "agent-ai-news",
            },
            "temperature": temperature,
            "timeout": settings.llm_timeout_seconds,
            "max_retries": settings.llm_max_retries,
        }

        # Resolve OpenRouter provider routing preferences
        raw_providers = openrouter_providers or settings.openrouter_providers
        provider_order: List[str] = []
        if isinstance(raw_providers, str):
            provider_order = [p.strip() for p in raw_providers.split(",") if p.strip()]
        elif isinstance(raw_providers, list):
            provider_order = [str(p).strip() for p in raw_providers if str(p).strip()]

        allow_fallbacks = (
            openrouter_allow_fallbacks
            if openrouter_allow_fallbacks is not None
            else settings.openrouter_allow_fallbacks
        )

        provider_payload = {}
        if provider_order:
            provider_payload["order"] = provider_order
        if allow_fallbacks is not None:
            provider_payload["allow_fallbacks"] = allow_fallbacks

        if provider_payload:
            kwargs["extra_body"] = {"provider": provider_payload}

        return ChatOpenAI(**kwargs)

    elif active_provider in ("gemini", "google_genai", "google"):
        from langchain_google_genai import ChatGoogleGenerativeAI

        chosen_model = model_name or settings.agent_model_name or "gemini-3.6-flash"
        api_key = _require_api_key(settings.google_api_key, "gemini", "GOOGLE_API_KEY")
        kwargs = {
            "model": chosen_model,
            "temperature": temperature,
            "google_api_key": api_key,
            "timeout": settings.llm_timeout_seconds,
            "max_retries": settings.llm_max_retries,
        }
        return ChatGoogleGenerativeAI(**kwargs)

    elif active_provider == "openai":
        from langchain_openai import ChatOpenAI

        chosen_model = model_name or settings.agent_model_name or "gpt-4o"
        api_key = _require_api_key(settings.openai_api_key, "openai", "OPENAI_API_KEY")
        kwargs = {
            "model": chosen_model,
            "temperature": temperature,
            "api_key": api_key,
            "timeout": settings.llm_timeout_seconds,
            "max_retries": settings.llm_max_retries,
        }
        return ChatOpenAI(**kwargs)

    elif active_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        chosen_model = model_name or settings.agent_model_name or "claude-sonnet-5"
        api_key = _require_api_key(settings.anthropic_api_key, "anthropic", "ANTHROPIC_API_KEY")
        kwargs = {
            "model_name": chosen_model,
            "temperature": temperature,
            "api_key": api_key,
            "timeout": settings.llm_timeout_seconds,
            "max_retries": settings.llm_max_retries,
        }
        return ChatAnthropic(**kwargs)

    else:
        raise ValueError(
            f"Unsupported LLM provider: '{active_provider}'. Supported: openrouter, gemini, openai, anthropic"
        )
