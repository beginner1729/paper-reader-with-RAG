# LangGraph Paper Explainer

This directory mirrors the `.opencode` agent/workflow setup with LangGraph.

Agent resources now live in `langgraph/resource/`:

- Prompts: `langgraph/resource/prompts/<agent_id>.md`
- Per-agent model/config: `langgraph/resource/agents/<agent_id>.yaml`

## Included agents

- `archive_tex_fetcher`
- `paper_resource_gatherer`
- `paper_flow_creator`
- `paper_reviewer`
- `website_maker`

The workflow order matches `.opencode/workflows/paper_explain.md`:

1. `fetch_tex`
2. `gather_resources`
3. `create_flow`
4. `review_flow`
5. `revise_flow`
6. `create_website`

## Authentication

The runner loads environment variables from both:

- `<repo>/.env`
- `<repo>/langgraph/.env`

Use `langgraph/.env.example` as a template.

Required keys by model/provider:

- `deepseek/*` models -> `DEEPSEEK_API_KEY`
- `openai/*` models -> `OPENAI_API_KEY`

Optional base URL overrides:

- `DEEPSEEK_BASE_URL` (default: `https://api.deepseek.com`)
- `OPENAI_BASE_URL`

If a required key is missing, startup fails with a clear error.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r langgraph/requirements.txt
```

## Run

```bash
python langgraph/run_workflow.py "https://arxiv.org/abs/2602.05400"
```

Optional existing paper directory:

```bash
python langgraph/run_workflow.py "https://arxiv.org/abs/2602.05400" --paper-dir "./my-paper-dir"
```

The runner prints a progress bar and logs per-step status to `workflow_run_current.log` by default.

It also creates an intermediate handoff summary between agents only when context is large
(controlled by `handoff.min_total_chars` in `langgraph/config.yaml`).

It supports checkpointing by `archive_url` so completed steps are skipped on reruns.
Checkpoint files are stored under `langgraph/.checkpoints/` by default.
Use `--rerun-website-only` to keep prior steps cached and rerun only website generation.

Custom log file:

```bash
python langgraph/run_workflow.py "https://arxiv.org/abs/2602.05400" --log-file "logs/paper_workflow.log"
```

Disable handoff summaries:

```bash
python langgraph/run_workflow.py "https://arxiv.org/abs/2602.05400" --disable-handoff-summary
```

Set threshold for when summaries are generated:

```bash
python langgraph/run_workflow.py "https://arxiv.org/abs/2602.05400" --handoff-min-total-chars 25000
```

Disable checkpointing for a run:

```bash
python langgraph/run_workflow.py "https://arxiv.org/abs/2602.05400" --disable-checkpoint
```

Reset checkpoint for this archive URL and rerun from scratch:

```bash
python langgraph/run_workflow.py "https://arxiv.org/abs/2602.05400" --reset-checkpoint
```

Rerun only website generation for this archive URL:

```bash
python langgraph/run_workflow.py "https://arxiv.org/abs/2602.05400" --rerun-website-only
```

Website output expectations (from prompts):

- Keep section-wise presentation fixed (one page per major section with section navigation)
- Link most technical terms to glossary entries with high coverage
- For each key equation, include nearby notation and intuition snippets
