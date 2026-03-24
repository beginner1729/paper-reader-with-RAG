from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


def load_env(repo_root: Path) -> None:
    load_dotenv(repo_root / ".env", override=False)
    load_dotenv(repo_root / "langgraph" / ".env", override=False)


def _provider_from_model(model_ref: str) -> tuple[str, str]:
    if "/" in model_ref:
        provider, model_name = model_ref.split("/", 1)
        return provider.lower(), model_name
    return "openai", model_ref


def _require_env_var(name: str, provider_name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    raise RuntimeError(
        f"Missing API key for {provider_name}. Set environment variable `{name}`."
    )


def make_model(model_ref: str, config: dict[str, Any]) -> ChatOpenAI:
    provider_name, raw_model_name = _provider_from_model(model_ref)
    providers = config.get("provider", {})
    provider_cfg = providers.get(provider_name, {})

    api_key_env = provider_cfg.get("api_key_env")
    if not api_key_env:
        fallback = "OPENAI_API_KEY" if provider_name == "openai" else "DEEPSEEK_API_KEY"
        api_key_env = fallback

    api_key = _require_env_var(api_key_env, provider_name)
    base_url_env = provider_cfg.get("base_url_env")
    timeout_ms = int(provider_cfg.get("options", {}).get("timeout_ms", 120000))

    base_url = None
    if base_url_env:
        base_url = os.getenv(base_url_env)
    if not base_url and provider_cfg.get("default_base_url"):
        base_url = provider_cfg["default_base_url"]

    return ChatOpenAI(
        model=raw_model_name,
        api_key=api_key,
        base_url=base_url,
        timeout=timeout_ms / 1000,
    )
