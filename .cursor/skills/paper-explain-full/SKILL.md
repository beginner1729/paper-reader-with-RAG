---
name: paper-explain-full
description: Full end-to-end pipeline — downloads TeX sources from arXiv, analyzes them, creates a detailed paper explanation with diagrams, self-reviews, and generates an interactive website. Single-agent pipeline.
---

# Paper Explain (Full)

Given an arXiv or archive URL, run the complete pipeline from TeX source download to an interactive website — all in one session.

## Pipeline

Execute all phases in order. Every bash/webfetch call must use timeout: 86400000.

### Phase 1: Download & Analyze TeX Sources
1. Run `.venv/bin/python download_tex_source.py <archive_url>`
2. Capture the `Extracted into:` path as `paper_dir`
3. Glob `**/*.tex` under `paper_dir` to find all TeX files
4. Create `paper_dir/notes/tex/` mirroring the TeX folder structure
5. For each `.tex` file, write a detailed note (`<filename>.md`) covering:
   - Purpose and role, structural outline, key macros, key equations, figures/tables
   - Dependencies (`\input`, `\include`, `\bibliography`, `\usepackage`)
6. Write `paper_dir/notes/tex_manifest.md`

### Phase 2: Gather Resources
1. Determine the main TeX file (`\documentclass` + `\begin{document}`)
2. Webfetch the arXiv abstract page; capture title, authors, abstract
3. Build `paper_dir/notes/paper_outline.md` with title, contributions, section outline, key definitions
4. Extract bibliography; webfetch top 5-10 citations; write `paper_dir/notes/bibliography_summary.md`
5. Write `paper_dir/notes/resource_index.md`

### Phase 3: Create Paper Flow
Write `paper_dir/notes/paper_flow.md`:
- Overview, mindmap, detailed walkthrough per section
- Math: LaTeX equations + "Notation" block + "Intuition" block (2-4 lines each)
- Algorithms: Mermaid diagrams and pseudocode
- Glossary and assumptions

Save Mermaid as `.mmd`, render PNGs via `render_mermaid_png.py` in `paper_dir/diagrams/`.

### Phase 4: Self-Review & Revise
1. Fact-check `paper_flow.md` against TeX sources
2. Write `paper_dir/notes/review_feedback.md` (accuracy, coverage, math, diagrams, clarity)
3. Revise `paper_flow.md`; add "Revision Notes" section

### Phase 5: Generate Website
1. Extract glossary → `paper_dir/website/glossary.json`
2. Download KaTeX locally into `paper_dir/website/katex/`
3. Generate: `index.html`, `sections/*.html`, `glossary.html`, `css/styles.css`, `js/script.js`
4. Responsive design, dark/light mode, glossary tooltips, KaTeX rendering
5. Create `serve.py` and `README.md`
6. Validate links, glossary coverage, images, equations

## Outputs
- `paper_dir/notes/paper_flow.md` — main explanation with diagrams
- `paper_dir/notes/review_feedback.md` — self-review
- `paper_dir/website/index.html` — interactive website

Serve: `cd <paper_dir>/website && python3 -m http.server 8000`
