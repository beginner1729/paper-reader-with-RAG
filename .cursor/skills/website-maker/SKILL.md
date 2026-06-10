---
name: website-maker
description: Create an interactive website from paper explanations with glossary links and local hosting. Use when a paper flow document needs to be converted into an interactive website.
---

# Website Maker

You create an interactive website that presents the paper explanation with glossary links and local hosting.

## Steps

IMPORTANT: Pass timeout: 86400000 for bash and webfetch calls.

1) Read all existing resources in `paper_dir`:
   - `paper_dir/notes/paper_flow.md` (main explanation)
   - `paper_dir/notes/paper_outline.md` (outline)
   - `paper_dir/notes/bibliography_summary.md` (bibliography)
   - `paper_dir/notes/tex_manifest.md` (TeX file summaries)
   - `paper_dir/diagrams/` (Mermaid sources and PNGs)

2) Extract glossary terms and definitions:
   - Identify technical terms, jargon, acronyms, and key concepts
   - Create definitions based on the paper content and external references
   - Save glossary as `paper_dir/website/glossary.json`

3) Generate HTML website structure in `paper_dir/website/`:
   - `index.html`: Main page with paper overview and navigation
   - `sections/`: One HTML file per major section
   - `glossary.html`: Interactive glossary page
   - `css/styles.css`: Custom styling
   - `js/script.js`: Interactive features
   - Include KaTeX for LaTeX math rendering (download locally)
   - Preserve LaTeX math delimiters exactly as they appear — do NOT escape backslashes as HTML entities
   - When generating HTML from scripts, use raw strings. NEVER wrap math delimiters in HTML tags.

   **Equation rendering rules:**
   - NEVER escape LaTeX backslashes as HTML entities. Keep them literal.
   - KaTeX config: delimiters for inline (backslash-paren), display (backslash-bracket), $$, and begin/end{equation/align/aligned}.
   - renderMathInElement options: throwOnError: false, strict: false, trust: true.
   - CSS: .katex-display { overflow-x: auto; overflow-y: hidden; } .katex { font-size: 1.1em; }
   - Common fixes: every frac needs two brace groups; every begin needs matching end; dollar delimiters replaced with backslash-paren; underscores inside math only.
   - Post-generation: open HTML in browser, check DevTools Console for KaTeX parse errors. View source — every inline opener must have matching closer. Search for lone backslashes.

4) Implement glossary linking:
   - Wrap glossary terms with `<span class="glossary-term" data-term="term_name">term</span>`
   - Implement tooltips and click navigation to glossary entries

5) Enrich mathematical sections:
   - Add "Notation" snippets for each key equation
   - Add "Intuition" snippets (2-4 lines) for each key equation

6) Create responsive design with modern CSS (Flexbox/Grid)
   - Include dark/light mode toggle if possible

7) Embed diagrams with captions

8) Set up local hosting:
   - Create `paper_dir/website/serve.py`
   - Write `paper_dir/website/README.md`

9) Generate navigation: table of contents, breadcrumbs, previous/next buttons

10) Validate and test (math equations — thorough check):
    - **Delimiter balance:** For every `\(` confirm a matching `\)`, for every `\[` confirm a matching `\]`. Scan each HTML file to catch mismatched pairs.
    - **Truncation check:** Look for incomplete LaTeX — unbalanced `{`/`}` braces, missing closing `}`, `\frac` without both arguments, `\sum`/`\int`/`\prod` without limits or body.
    - **Common escape errors:** Check that `_` inside math is not interpreted as markdown italics, that `\\` is preserved as `\\\\` where needed, and that `&` is escaped as `&amp;` outside math blocks.
    - **Source cross-check:** Compare the 5-10 most important equations against the original TeX source.
    - **Notation/Intuition completeness:** Verify every Notation and Intuition block is fully present — not truncated mid-sentence.
    - **Rendering test:** Flag any equation whose raw LaTeX looks malformed.
    - Check all links, glossary terms, images.
    - Fix every issue found. Record issues and fixes in `paper_dir/website/validation_report.md`.

## Constraints

- Keep all outputs inside `paper_dir/website/`
- Use semantic HTML5 with accessibility attributes
- Minimize external dependencies
- The website should work offline once generated
