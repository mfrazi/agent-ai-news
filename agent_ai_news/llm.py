"""Provider-agnostic LLM Factory for agent-ai-news."""

import os
from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from agent_ai_news.config import get_settings


def get_chat_model(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.2,
) -> BaseChatModel:
    """Instantiate and return a BaseChatModel according to provider and configuration."""
    settings = get_settings()
    active_provider = (provider or settings.resolve_provider()).lower().strip()

    if active_provider == "openrouter":
        from langchain_openai import ChatOpenAI

        chosen_model = model_name or settings.agent_model_name or "anthropic/claude-3.5-sonnet"
        api_key = settings.openrouter_api_key or os.environ.get("OPENROUTER_API_KEY")
        kwargs = {
            "model": chosen_model,
            "base_url": "https://openrouter.ai/api/v1",
            "default_headers": {
                "HTTP-Referer": "https://github.com/langchain-ai/deepagents",
                "X-Title": "AI Intelligence Agent",
            },
            "temperature": temperature,
        }
        if api_key:
            kwargs["api_key"] = api_key
        return ChatOpenAI(**kwargs)

    elif active_provider in ("gemini", "google_genai", "google"):
        from langchain_google_genai import ChatGoogleGenerativeAI

        chosen_model = model_name or settings.agent_model_name or "gemini-2.0-flash"
        api_key = settings.google_api_key or os.environ.get("GOOGLE_API_KEY")
        kwargs = {
            "model": chosen_model,
            "temperature": temperature,
        }
        if api_key:
            kwargs["google_api_key"] = api_key
        return ChatGoogleGenerativeAI(**kwargs)

    elif active_provider == "openai":
        from langchain_openai import ChatOpenAI

        chosen_model = model_name or settings.agent_model_name or "gpt-4o"
        api_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
        kwargs = {
            "model": chosen_model,
            "temperature": temperature,
        }
        if api_key:
            kwargs["api_key"] = api_key
        return ChatOpenAI(**kwargs)

    elif active_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        chosen_model = model_name or settings.agent_model_name or "claude-3-5-sonnet-latest"
        api_key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        kwargs = {
            "model_name": chosen_model,
            "temperature": temperature,
        }
        if api_key:
            kwargs["api_key"] = api_key
        return ChatAnthropic(**kwargs)

    else:
        raise ValueError(
            f"Unsupported LLM provider: '{active_provider}'. Supported: openrouter, gemini, openai, anthropic"
        )
