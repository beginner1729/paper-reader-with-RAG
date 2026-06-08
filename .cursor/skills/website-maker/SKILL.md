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

10) Validate all links, glossary terms, images, and LaTeX equations

## Constraints

- Keep all outputs inside `paper_dir/website/`
- Use semantic HTML5 with accessibility attributes
- Minimize external dependencies
- The website should work offline once generated
