from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from langgraph.prebuilt import create_react_agent  # type: ignore[reportMissingImports]

from .auth import make_model
from .config import load_agent_prompt, load_resource_agent_configs


@dataclass
class AgentRuntime:
    agent_id: str
    max_steps: int
    required_outputs: list[str]
    graph: Any


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Agent response must be a JSON object")
    return data


def build_agent_runtimes(repo_root, config: dict[str, Any], tools) -> dict[str, AgentRuntime]:
    resource_configs = load_resource_agent_configs(repo_root)
    legacy_configs = config.get("agent", {})

    workflow_agents: list[str] = []
    steps = config.get("workflow", {}).get("paper_explain", {}).get("steps", [])
    if isinstance(steps, list):
        for step in steps:
            if isinstance(step, dict) and isinstance(step.get("agent"), str):
                workflow_agents.append(step["agent"])

    ordered_agent_ids: list[str] = []
    for agent_id in workflow_agents + list(resource_configs.keys()) + list(legacy_configs.keys()):
        if agent_id not in ordered_agent_ids:
            ordered_agent_ids.append(agent_id)

    runtimes: dict[str, AgentRuntime] = {}
    for agent_id in ordered_agent_ids:
        resource_cfg = resource_configs.get(agent_id, {})
        legacy_cfg = legacy_configs.get(agent_id, {})
        agent_cfg = {**legacy_cfg, **resource_cfg}
        model_ref = agent_cfg.get("model", "deepseek/deepseek-reasoner")
        model = make_model(model_ref, config)
        prompt = load_agent_prompt(repo_root, agent_id)
        graph = create_react_agent(model=model, tools=tools, prompt=prompt)
        runtimes[agent_id] = AgentRuntime(
            agent_id=agent_id,
            max_steps=int(agent_cfg.get("max_steps", 80)),
            required_outputs=list(agent_cfg.get("outputs", [])),
            graph=graph,
        )
    return runtimes


def run_agent(runtime: AgentRuntime, input_payload: dict[str, Any]) -> dict[str, Any]:
    required = ", ".join(runtime.required_outputs)
    handoff_hint = ""
    if input_payload.get("handoff_summary_path"):
        handoff_hint = (
            "A `handoff_summary_path` is provided. Read it first and use it as primary "
            "context. Open full source files only when necessary. Preserve glossary candidates, "
            "equation notation definitions, and intuitive math explanations in your outputs. "
        )
    message = "".join(
        [
            "Run this task with the provided inputs. ",
            handoff_hint,
            "Perform all required file and web operations. ",
            "Return only JSON with keys `outputs` and `notes`. ",
            f"`outputs` must include: {required}. ",
            f"Inputs: {json.dumps(input_payload, ensure_ascii=True)}",
        ]
    )

    result = runtime.graph.invoke(
        {"messages": [{"role": "user", "content": message}]},
        config={"recursion_limit": runtime.max_steps},
    )

    messages = result.get("messages", [])
    if not messages:
        raise RuntimeError(f"No response produced by {runtime.agent_id}")
    final_content = messages[-1].content
    parsed = _extract_json_object(final_content)
    outputs = parsed.get("outputs", {})
    if not isinstance(outputs, dict):
        raise ValueError(f"Agent {runtime.agent_id} did not return object `outputs`")

    missing = [key for key in runtime.required_outputs if key not in outputs]
    if missing:
        raise ValueError(f"Agent {runtime.agent_id} missing outputs: {', '.join(missing)}")
    return outputs
