from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as file:
        loaded = yaml.safe_load(file) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Invalid config format in {config_path}")
    return loaded


def load_agent_prompt(repo_root: Path, agent_id: str) -> str:
    resource_path = repo_root / "langgraph" / "resource" / "prompts" / f"{agent_id}.md"
    path = resource_path
    if not path.exists():
        path = repo_root / ".opencode" / "agents" / f"{agent_id}.md"
    if not path.exists():
        raise FileNotFoundError(f"Agent prompt file not found: {path}")

    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return text.strip()

    parts = text.split("---", 2)
    if len(parts) < 3:
        return text.strip()
    return parts[2].strip()


def load_resource_agent_configs(repo_root: Path) -> dict[str, dict[str, Any]]:
    agents_dir = repo_root / "langgraph" / "resource" / "agents"
    if not agents_dir.exists():
        return {}

    configs: dict[str, dict[str, Any]] = {}
    for file_path in sorted(agents_dir.glob("*.yaml")):
        with file_path.open("r", encoding="utf-8") as file:
            loaded = yaml.safe_load(file) or {}
        if not isinstance(loaded, dict):
            continue
        agent_id = loaded.get("id") or file_path.stem
        if not isinstance(agent_id, str):
            continue
        configs[agent_id] = loaded
    return configs
