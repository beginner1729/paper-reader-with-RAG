#!/Users/koushik.dey/Work/papers/paper-reader/.venv/bin/python
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from paper_graph.agents import build_agent_runtimes
from paper_graph.auth import load_env
from paper_graph.checkpointing import CheckpointStore
from paper_graph.config import load_config
from paper_graph.tools import build_tools
from paper_graph.workflow import WorkflowState, run_workflow_with_progress
from tqdm import tqdm


def _configure_logger(log_file: Path) -> logging.Logger:
    logger = logging.getLogger("paper_workflow")
    logger.setLevel(logging.INFO)
    logger.handlers = []

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def main() -> int:
    parser = argparse.ArgumentParser(description="Run LangGraph paper explain workflow")
    parser.add_argument("archive_url", help="arXiv/source archive URL")
    parser.add_argument("--paper-dir", help="Optional already-downloaded paper directory")
    parser.add_argument(
        "--config",
        default="langgraph/config.yaml",
        help="Path to LangGraph config YAML",
    )
    parser.add_argument(
        "--log-file",
        default="workflow_run_current.log",
        help="Path to status log file",
    )
    parser.add_argument(
        "--disable-handoff-summary",
        action="store_true",
        help="Disable intermediate handoff summaries",
    )
    parser.add_argument(
        "--handoff-min-total-chars",
        type=int,
        help="Only summarize when raw context chars exceed this threshold",
    )
    parser.add_argument(
        "--disable-checkpoint",
        action="store_true",
        help="Disable step checkpointing for this run",
    )
    parser.add_argument(
        "--reset-checkpoint",
        action="store_true",
        help="Delete existing checkpoint for this archive URL before running",
    )
    parser.add_argument(
        "--rerun-website-only",
        action="store_true",
        help="Force rerun of only the website step for this archive URL",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    load_env(repo_root)
    logger = _configure_logger((repo_root / args.log_file).resolve())

    config = load_config((repo_root / args.config).resolve())
    tools = build_tools(repo_root)
    runtimes = build_agent_runtimes(repo_root, config, tools)
    handoff_config = dict(config.get("handoff", {}))
    if args.disable_handoff_summary:
        handoff_config["enabled"] = False
    if args.handoff_min_total_chars is not None:
        handoff_config["min_total_chars"] = args.handoff_min_total_chars

    checkpoint_cfg = dict(config.get("checkpoint", {}))
    checkpoint_enabled = bool(checkpoint_cfg.get("enabled", True)) and not args.disable_checkpoint
    checkpoint_store = None
    checkpoint_data = None
    completed_steps: set[str] = set()
    checkpoint_state: WorkflowState | None = None

    if checkpoint_enabled:
        checkpoint_dir = (repo_root / checkpoint_cfg.get("dir", "langgraph/.checkpoints")).resolve()
        checkpoint_store = CheckpointStore(checkpoint_dir)
        if args.reset_checkpoint:
            checkpoint_store.clear(args.archive_url)
            logger.info("Checkpoint reset for archive URL")
        if args.rerun_website_only:
            cleared = checkpoint_store.clear_step(args.archive_url, "create_website")
            if cleared:
                logger.info("Website step removed from checkpoint for archive URL")
            else:
                logger.info("No checkpoint found while trying to rerun website step")
        checkpoint_data = checkpoint_store.load(args.archive_url)
        if checkpoint_data:
            raw_steps = checkpoint_data.get("completed_steps", [])
            if isinstance(raw_steps, list):
                completed_steps = {step for step in raw_steps if isinstance(step, str)}
            raw_state = checkpoint_data.get("state", {})
            if isinstance(raw_state, dict):
                checkpoint_state = dict(raw_state)  # type: ignore[assignment]
                if args.rerun_website_only:
                    checkpoint_state.pop("website_dir", None)  # type: ignore[union-attr]
                    checkpoint_state.pop("website_index_path", None)  # type: ignore[union-attr]
                    checkpoint_state.pop("glossary_path", None)  # type: ignore[union-attr]
            logger.info("Loaded checkpoint with %s completed step(s)", len(completed_steps))

    def _save_checkpoint(state: WorkflowState, done_steps: set[str]) -> None:
        if not checkpoint_store:
            return
        checkpoint_path = checkpoint_store.save(
            archive_url=args.archive_url,
            state=dict(state),
            completed_steps=sorted(done_steps),
        )
        logger.info("Checkpoint updated: %s", checkpoint_path)

    state: WorkflowState = {"archive_url": args.archive_url}
    if args.paper_dir:
        state["paper_dir"] = args.paper_dir

    logger.info("Workflow started")
    with tqdm(total=6, desc="paper_explain", unit="step") as progress:
        result = run_workflow_with_progress(
            runtimes=runtimes,
            initial_state=state,
            progress=progress,
            logger=logger,
            repo_root=repo_root,
            handoff_config=handoff_config,
            checkpoint_state=checkpoint_state,
            completed_steps=completed_steps,
            on_step_complete=_save_checkpoint if checkpoint_enabled else None,
        )
    logger.info("Workflow completed")

    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
