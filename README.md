# Paper Reader Utilities

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Quick install

```bash
curl -sSL https://raw.githubusercontent.com/beginner1729/paper-reader-with-RAG/main/install.sh | bash
```

Installs all paper-reader agents to OpenCode, Claude Code, Codex CLI, and Cursor.

## TeX source downloader

`download_tex_source.py` downloads a source archive (or arXiv abs/pdf link) and
extracts it into a folder named after the paper title when available, then
prints any `.tex` files it finds.

### Usage

```bash
.venv/bin/python download_tex_source.py <URL> [--out OUTPUT_DIR] [--keep-archive]
```

### Notes

- Uses only the Python standard library.
- Supports `.zip`, `.tar`, `.tar.gz`, and `.tgz` archives.
- For arXiv links, `/abs/` and `/pdf/` URLs are converted to the source archive.

## Mermaid PNG renderer

`render_mermaid_png.py` renders Mermaid code to PNG files using the
mermaid.ink service.

### Usage

```bash
.venv/bin/python render_mermaid_png.py diagram.mmd
.venv/bin/python render_mermaid_png.py notes.md --out-dir diagrams
```

### Notes

- Works with `.mmd` files or Markdown files containing mermaid fenced code blocks.
- Requires internet access to reach mermaid.ink.

## OpenCode agents

Agent definitions live in `.opencode/agents/`. The `paper_explain` agent is a
primary agent that orchestrates all subagents in sequence.

### Run the full pipeline

```bash
opencode run agent paper_explain -- archive_url="<URL>"
```

Or with the explicit file path:

```bash
opencode run agent .opencode/agents/paper_explain.md -- archive_url="<URL>"
```

Outputs are written inside the paper folder created by `download_tex_source.py`:

- `<paper_dir>/notes/tex/` per-TeX file notes
- `<paper_dir>/notes/paper_outline.md`
- `<paper_dir>/notes/bibliography_summary.md`
- `<paper_dir>/notes/paper_flow.md`
- `<paper_dir>/notes/review_feedback.md`
- `<paper_dir>/diagrams/` Mermaid sources and PNGs
- `<paper_dir>/website/` interactive website with glossary and local hosting

### Agent descriptions

1. **Archive Tex Fetcher**: Downloads TeX sources from archive/arXiv links and creates detailed per-file notes.
2. **Paper Resource Gatherer**: Builds paper outline and gathers external references for key citations.
3. **Paper Flow Creator**: Creates overview and detailed explanation with diagrams and mathematical equations.
4. **Paper Reviewer**: Reviews the flow document for accuracy, completeness, and clarity.
5. **Website Maker**: Generates interactive website with glossary links and local hosting from paper explanations.

### Run individual agents

```bash
opencode run agent archive_tex_fetcher -- archive_url="<URL>"
opencode run agent paper_resource_gatherer -- archive_url="<URL>"
opencode run agent paper_flow_creator -- paper_dir="<paper_dir>"
opencode run agent paper_reviewer -- paper_dir="<paper_dir>" paper_flow_path="<paper_dir>/notes/paper_flow.md"
opencode run agent website_maker -- paper_dir="<paper_dir>" paper_flow_path="<paper_dir>/notes/paper_flow.md" diagrams_dir="<paper_dir>/diagrams"
```

### Serve the generated website

After running the full workflow or the Website Maker agent, you can serve the website locally:

```bash
cd "<paper_dir>/website"
python3 -m http.server 8000
```

Then open `http://localhost:8000` in your browser.

The website includes:
- Interactive glossary with term definitions
- Navigation between paper sections
- Embedded diagrams and mathematical equations
- Responsive design for mobile and desktop
- Local hosting capability

## Claude Code

Agent definitions live in `.claude/agents/`. The `paper-explain` agent
orchestrates all subagents in sequence.

### Run the full pipeline

```bash
claude --agent paper-explain
```

Then provide `archive_url` in the conversation:
```
Process this paper: https://arxiv.org/abs/2602.05400
```

Or run it non-interactively:
```bash
claude -p "Run the paper explain pipeline for https://arxiv.org/abs/2602.05400" --agent paper-explain
```

### Run individual subagents

```bash
claude --agent archive-tex-fetcher     # Fetch TeX sources
claude --agent paper-resource-gatherer # Build outline and bibliography
claude --agent paper-flow-creator      # Create paper explanation
claude --agent paper-reviewer          # Review the flow document
claude --agent website-maker           # Generate interactive website
```

## Codex CLI

Agent definitions live in `.codex/agents/*.toml`.

### Run the full pipeline

Codex uses natural-language orchestration rather than declarative pipelines.
Invoke the pipeline by describing the sequence:

```bash
codex exec "Download TeX from https://arxiv.org/abs/2602.05400, then gather
resources, create a paper flow explanation, review it, revise based on
feedback, and generate an interactive website. Use the archive_tex_fetcher,
paper_resource_gatherer, paper_flow_creator, paper_reviewer, and website_maker
agents where appropriate."
```

### Run individual agents

```bash
codex exec "Use the archive_tex_fetcher agent to download and analyze
https://arxiv.org/abs/2602.05400"
```

## Cursor

Skill definitions live in `.cursor/skills/`. The DAG pipeline is defined in
`.cursor/paper_explain_dag.json` with a TypeScript runner.

### Run the full pipeline

```bash
npx tsx .cursor/run_paper_explain.ts "https://arxiv.org/abs/2602.05400"
```

### Run individual skills

Mention skills by name in any Cursor chat:
```
@archive-tex-fetcher Download and analyze https://arxiv.org/abs/2602.05400
```

## LangGraph equivalent workflow

LangGraph versions of the same agents and workflow are available in
`langgraph/`.

- Config parity file: `langgraph/config.yaml`
- Runner: `langgraph/run_workflow.py`
- Setup and auth details: `langgraph/README.md`

Quick run:

```bash
python langgraph/run_workflow.py "https://arxiv.org/abs/2602.05400"
```
