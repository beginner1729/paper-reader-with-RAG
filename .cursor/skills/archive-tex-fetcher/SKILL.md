---
name: archive-tex-fetcher
description: Fetch TeX sources from an archive/arXiv link and create detailed per-file notes. Use when TeX sources need to be downloaded and analyzed.
---

# Archive TeX Fetcher

You download TeX sources and write detailed notes per .tex file.

## Steps

1) Run the downloader from the repo root:
   ```
   .venv/bin/python download_tex_source.py <archive_url>
   ```
   IMPORTANT: Pass timeout: 86400000 for all bash commands.

2) Find all `.tex` files under `paper_dir` using a glob like `**/*.tex`.

3) Create `paper_dir/notes/tex/` and mirror the TeX folder structure for notes.
   Example note path for `sections/intro.tex`:
   `paper_dir/notes/tex/sections/intro.tex.md`

4) For each `.tex` file, write a detailed Markdown note including:
   - Purpose and role in the build (root file, included fragment, appendix, etc.)
   - Structural outline (sections/subsections/environment blocks)
   - Key macros/commands defined and where used
   - Key equations (copy the LaTeX math where present)
   - Figures/tables referenced and their labels
   - Dependencies (`\input`, `\include`, `\bibliography`, `\usepackage`)
   - Open TODOs or missing references if any

5) Write `paper_dir/notes/tex_manifest.md` summarizing all TeX files with
   1-2 sentence summaries and a short include/dependency map.

## Constraints

- Keep all outputs inside `paper_dir`.
- Notes should be concise but detailed enough to follow the structure.
- Do not modify TeX sources.
