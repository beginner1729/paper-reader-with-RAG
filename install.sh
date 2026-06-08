#!/usr/bin/env bash
set -euo pipefail

BASE_URL="https://raw.githubusercontent.com/beginner1729/paper-reader-with-RAG/main"

OPECODE_DIR="${OPENCODE_CONFIG:-$HOME/.config/opencode}"
CLAUDE_DIR="$HOME/.claude"
CODEX_DIR="$HOME/.codex"
CURSOR_DIR="$HOME/.cursor"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    Paper Reader with RAG — Agent Installer          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Installing paper-reader agents (individual + all-in-one) for OpenCode, Claude Code, Codex, and Cursor...${NC}"
echo ""

# ── OpenCode ──────────────────────────────────────────
echo -e "${YELLOW}[OpenCode] Installing agents...${NC}"
mkdir -p "$OPECODE_DIR/agents"

OCO_AGENTS=(
  archive_tex_fetcher
  paper_resource_gatherer
  paper_flow_creator
  paper_reviewer
  website_maker
  paper_explain
  paper_explain_full
)

for agent in "${OCO_AGENTS[@]}"; do
  echo "  → $agent"
  curl -sSL "$BASE_URL/.opencode/agents/${agent}.md" -o "$OPECODE_DIR/agents/${agent}.md"
done

echo -e "${GREEN}  OpenCode: $OPECODE_DIR/agents/{${OCO_AGENTS[*]}}.md${NC}"

# ── Claude Code ──────────────────────────────────────────
echo ""
echo -e "${YELLOW}[Claude Code] Installing agents...${NC}"
mkdir -p "$CLAUDE_DIR/agents"

CLAUDE_AGENTS=(
  archive-tex-fetcher
  paper-resource-gatherer
  paper-flow-creator
  paper-reviewer
  website-maker
  paper-explain
  paper-explain-full
)

for agent in "${CLAUDE_AGENTS[@]}"; do
  echo "  → $agent"
  curl -sSL "$BASE_URL/.claude/agents/${agent}.md" -o "$CLAUDE_DIR/agents/${agent}.md"
done

echo -e "${GREEN}  Claude Code: $CLAUDE_DIR/agents/{${CLAUDE_AGENTS[*]}}.md${NC}"

# ── Codex CLI ──────────────────────────────────────────
echo ""
echo -e "${YELLOW}[Codex CLI] Installing agents...${NC}"
mkdir -p "$CODEX_DIR/agents"

CODEX_AGENTS=(
  archive_tex_fetcher
  paper_resource_gatherer
  paper_flow_creator
  paper_reviewer
  website_maker
  paper_explain_full
)

for agent in "${CODEX_AGENTS[@]}"; do
  echo "  → $agent"
  curl -sSL "$BASE_URL/.codex/agents/${agent}.toml" -o "$CODEX_DIR/agents/${agent}.toml"
done

echo -e "${GREEN}  Codex CLI: $CODEX_DIR/agents/{${CODEX_AGENTS[*]}}.toml${NC}"

# ── Cursor ──────────────────────────────────────────
echo ""
echo -e "${YELLOW}[Cursor] Installing skills and DAG pipeline...${NC}"

CURSOR_SKILLS=(
  archive-tex-fetcher
  paper-resource-gatherer
  paper-flow-creator
  paper-reviewer
  website-maker
  paper-explain-full
)

for skill in "${CURSOR_SKILLS[@]}"; do
  echo "  → skill: $skill"
  mkdir -p "$CURSOR_DIR/skills/${skill}"
  curl -sSL "$BASE_URL/.cursor/skills/${skill}/SKILL.md" -o "$CURSOR_DIR/skills/${skill}/SKILL.md"
done

echo "  → dag: paper_explain_dag.json"
curl -sSL "$BASE_URL/.cursor/paper_explain_dag.json" -o "$CURSOR_DIR/paper_explain_dag.json"
echo "  → runner: run_paper_explain.ts"
curl -sSL "$BASE_URL/.cursor/run_paper_explain.ts" -o "$CURSOR_DIR/run_paper_explain.ts"

echo -e "${GREEN}  Cursor: $CURSOR_DIR/skills/ + paper_explain_dag.json + run_paper_explain.ts${NC}"

# ── Done ──────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Installation complete!                             ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Usage:${NC}"
echo ""
echo "  OpenCode:"
echo "    opencode run agent archive_tex_fetcher  -- archive_url=\"<URL>\""
echo "    opencode run agent paper_explain       -- archive_url=\"<URL>\""
echo "    opencode run agent paper_explain_full  -- archive_url=\"<URL>\"  (all-in-one)"
echo ""
echo "  Claude Code:"
echo "    claude --agent archive-tex-fetcher"
echo "    claude --agent paper-explain"
echo "    claude --agent paper-explain-full      (all-in-one)"
echo ""
echo "  Codex CLI:"
echo '    codex exec "Use the paper_explain_full agent: <URL>"'
echo ""
echo "  Cursor:"
echo "    @paper-explain-full <URL>              (all-in-one)"
echo "    npx tsx ~/.cursor/run_paper_explain.ts \"<URL>\""
echo ""
echo -e "${YELLOW}See agents available in the repo README for details.${NC}"
