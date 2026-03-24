from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, TypedDict, cast

from langgraph.graph import END, START, StateGraph  # type: ignore[reportMissingImports]

from .agents import AgentRuntime, run_agent


class WorkflowState(TypedDict, total=False):
    archive_url: str
    paper_dir: str
    tex_notes_dir: str
    tex_manifest_path: str
    outline_path: str
    bibliography_summary_path: str
    resource_index_path: str
    paper_flow_path: str
    review_feedback_path: str
    diagrams_dir: str
    website_dir: str
    website_index_path: str
    glossary_path: str
    handoff_summary_path: str


def _required(state: WorkflowState, key: str) -> str:
    value = state.get(key)
    if not value:
        raise ValueError(f"Missing required workflow state: {key}")
    return value


def _add_handoff_if_present(payload: dict[str, Any], state: WorkflowState) -> dict[str, Any]:
    handoff = state.get("handoff_summary_path")
    if handoff:
        payload["handoff_summary_path"] = handoff
    return payload


def _archive_inputs(state: WorkflowState) -> dict[str, Any]:
    return _add_handoff_if_present({"archive_url": _required(state, "archive_url")}, state)


def _gather_inputs(state: WorkflowState) -> dict[str, Any]:
    payload: dict[str, Any] = {"archive_url": _required(state, "archive_url")}
    if state.get("paper_dir"):
        payload["paper_dir"] = _required(state, "paper_dir")
    return _add_handoff_if_present(payload, state)


def _flow_inputs(state: WorkflowState) -> dict[str, Any]:
    return _add_handoff_if_present({"paper_dir": _required(state, "paper_dir")}, state)


def _review_inputs(state: WorkflowState) -> dict[str, Any]:
    return _add_handoff_if_present({
        "paper_dir": _required(state, "paper_dir"),
        "paper_flow_path": _required(state, "paper_flow_path"),
    }, state)


def _revise_inputs(state: WorkflowState) -> dict[str, Any]:
    return _add_handoff_if_present({
        "paper_dir": _required(state, "paper_dir"),
        "paper_flow_path": _required(state, "paper_flow_path"),
        "review_feedback_path": _required(state, "review_feedback_path"),
    }, state)


def _website_inputs(state: WorkflowState) -> dict[str, Any]:
    return _add_handoff_if_present({
        "paper_dir": _required(state, "paper_dir"),
        "paper_flow_path": _required(state, "paper_flow_path"),
        "diagrams_dir": _required(state, "diagrams_dir"),
    }, state)


def _state_files_for_handoff(state: WorkflowState, repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for key, value in state.items():
        if not key.endswith("_path"):
            continue
        if key == "handoff_summary_path":
            continue
        if not isinstance(value, str):
            continue
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = (repo_root / candidate).resolve()
        if candidate.is_file():
            files.append(candidate)

    paper_dir_value = state.get("paper_dir")
    if paper_dir_value:
        paper_dir = Path(paper_dir_value)
        if not paper_dir.is_absolute():
            paper_dir = (repo_root / paper_dir).resolve()
        notes_dir = paper_dir / "notes"
        if notes_dir.is_dir():
            for note in sorted(notes_dir.rglob("*.md")):
                if note.is_file():
                    files.append(note)

    unique: list[Path] = []
    seen: set[str] = set()
    for file_path in files:
        key = str(file_path.resolve())
        if key in seen:
            continue
        seen.add(key)
        unique.append(file_path)
    return unique


def _condense_markdown(text: str, max_lines: int) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return "\n".join(lines)

    important: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("-"):
            important.append(line)
        if len(important) >= max_lines // 2:
            break

    head = lines[: max_lines // 3]
    tail = lines[-(max_lines // 3) :]
    merged = head + ["", "[... truncated ...]", ""] + important + ["", "[... tail ...]", ""] + tail
    return "\n".join(merged[:max_lines])


def _write_handoff_summary(
    state: WorkflowState,
    from_step: str,
    to_step: str,
    repo_root: Path,
    logger: logging.Logger,
    handoff_config: dict[str, Any],
) -> str | None:
    if not handoff_config.get("enabled", True):
        return None

    files = _state_files_for_handoff(state, repo_root)
    max_files = int(handoff_config.get("max_files", 12))
    max_chars_per_file = int(handoff_config.get("max_chars_per_file", 8000))
    min_total_chars = int(handoff_config.get("min_total_chars", 15000))
    max_lines_per_file = int(handoff_config.get("max_lines_per_file", 250))

    selected = files[:max_files]
    chunks: list[str] = []
    total_chars = 0

    for file_path in selected:
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            continue
        if not content.strip():
            continue
        total_chars += len(content)
        trimmed = content[:max_chars_per_file]
        condensed = _condense_markdown(trimmed, max_lines=max_lines_per_file)
        chunks.append(f"## {file_path}\n\n{condensed}\n")

    if total_chars < min_total_chars:
        logger.info(
            "[handoff %s->%s] skipped; context size (%s chars) below threshold (%s chars)",
            from_step,
            to_step,
            total_chars,
            min_total_chars,
        )
        return None

    paper_dir_value = state.get("paper_dir")
    if not paper_dir_value:
        logger.info("[handoff %s->%s] skipped; paper_dir missing", from_step, to_step)
        return None

    paper_dir = Path(paper_dir_value)
    if not paper_dir.is_absolute():
        paper_dir = (repo_root / paper_dir).resolve()
    handoff_dir = paper_dir / "notes" / "handoff"
    handoff_dir.mkdir(parents=True, exist_ok=True)

    out_path = handoff_dir / f"{from_step}_to_{to_step}.md"
    header = [
        f"# Handoff Summary: {from_step} -> {to_step}",
        "",
        "This summary is auto-generated to reduce context size for the next agent.",
        "Use it as the primary context and open full files only when needed.",
        "",
        f"- Source files considered: {len(selected)}",
        f"- Approx raw characters: {total_chars}",
        "",
    ]
    out_path.write_text("\n".join(header) + "\n".join(chunks), encoding="utf-8")
    logger.info("[handoff %s->%s] generated: %s", from_step, to_step, out_path)
    return str(out_path)


def _node(runtime: AgentRuntime, input_builder):
    def run(state: WorkflowState) -> WorkflowState:
        outputs = run_agent(runtime, input_builder(state))
        merged = cast(WorkflowState, dict(state))
        for key, value in outputs.items():
            merged[key] = value
        return merged

    return run


def build_workflow(runtimes: dict[str, AgentRuntime]):
    graph = StateGraph(WorkflowState)
    graph.add_node("fetch_tex", _node(runtimes["archive_tex_fetcher"], _archive_inputs))
    graph.add_node(
        "gather_resources", _node(runtimes["paper_resource_gatherer"], _gather_inputs)
    )
    graph.add_node("create_flow", _node(runtimes["paper_flow_creator"], _flow_inputs))
    graph.add_node("review_flow", _node(runtimes["paper_reviewer"], _review_inputs))
    graph.add_node("revise_flow", _node(runtimes["paper_flow_creator"], _revise_inputs))
    graph.add_node("create_website", _node(runtimes["website_maker"], _website_inputs))

    graph.add_edge(START, "fetch_tex")
    graph.add_edge("fetch_tex", "gather_resources")
    graph.add_edge("gather_resources", "create_flow")
    graph.add_edge("create_flow", "review_flow")
    graph.add_edge("review_flow", "revise_flow")
    graph.add_edge("revise_flow", "create_website")
    graph.add_edge("create_website", END)
    return graph.compile()


def run_workflow_with_progress(
    runtimes: dict[str, AgentRuntime],
    initial_state: WorkflowState,
    progress,
    logger: logging.Logger,
    repo_root: Path,
    handoff_config: dict[str, Any] | None = None,
    checkpoint_state: WorkflowState | None = None,
    completed_steps: set[str] | None = None,
    on_step_complete: Callable[[WorkflowState, set[str]], None] | None = None,
) -> WorkflowState:
    handoff_config = handoff_config or {}
    state = cast(WorkflowState, dict(initial_state))
    if checkpoint_state:
        restored = dict(checkpoint_state)
        restored.update(state)
        state = cast(WorkflowState, restored)
    completed = set(completed_steps or set())
    ordered_steps: list[tuple[str, AgentRuntime, Callable[[WorkflowState], dict[str, Any]]]] = [
        ("fetch_tex", runtimes["archive_tex_fetcher"], _archive_inputs),
        ("gather_resources", runtimes["paper_resource_gatherer"], _gather_inputs),
        ("create_flow", runtimes["paper_flow_creator"], _flow_inputs),
        ("review_flow", runtimes["paper_reviewer"], _review_inputs),
        ("revise_flow", runtimes["paper_flow_creator"], _revise_inputs),
        ("create_website", runtimes["website_maker"], _website_inputs),
    ]

    for idx, (step_id, runtime, build_inputs) in enumerate(ordered_steps):
        if step_id in completed:
            logger.info("[%s] skipped (checkpoint)", step_id)
            progress.update(1)
            continue

        if idx > 0:
            prev_step = ordered_steps[idx - 1][0]
            handoff_summary = _write_handoff_summary(
                state=state,
                from_step=prev_step,
                to_step=step_id,
                repo_root=repo_root,
                logger=logger,
                handoff_config=handoff_config,
            )
            if handoff_summary:
                state["handoff_summary_path"] = handoff_summary
            else:
                state.pop("handoff_summary_path", None)

        logger.info("[%s] started", step_id)
        outputs = run_agent(runtime, build_inputs(state))
        for key, value in outputs.items():
            state[key] = value
        completed.add(step_id)
        if on_step_complete:
            on_step_complete(state, completed)
        logger.info("[%s] completed", step_id)
        progress.update(1)

    return state
