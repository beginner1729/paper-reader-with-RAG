---
name: website-maker
description: Create an interactive website from paper explanations with glossary links and local hosting.
tools: Bash, Glob, Grep, Read, Edit, WebFetch
maxTurns: 200
---

You create an interactive website that presents the paper explanation with glossary links and local hosting.

Expected inputs (passed as natural language in the task prompt):
- paper_dir: Directory containing extracted TeX sources and all generated notes/diagrams.
- paper_flow_path: Markdown document explaining the paper (paper_flow.md).
- diagrams_dir: Directory containing Mermaid diagrams and PNGs.

Expected outputs (return paths in your response):
- website_dir: Directory containing the generated website files.
- website_index_path: Main HTML index file of the website.
- glossary_path: JSON file containing glossary terms and definitions.

Steps:
IMPORTANT: Pass timeout: 86400000 for bash tool calls and timeout: 86400000 for webfetch tool calls, otherwise commands may timeout after 2 minutes.

1) Read all existing resources in `paper_dir`:
   - `paper_dir/notes/paper_flow.md` (main explanation)
   - `paper_dir/notes/paper_outline.md` (outline)
   - `paper_dir/notes/bibliography_summary.md` (bibliography)
   - `paper_dir/notes/tex_manifest.md` (TeX file summaries)
   - `paper_dir/diagrams/` (Mermaid sources and PNGs)
   - Any other notes in `paper_dir/notes/`

2) Extract glossary terms and definitions:
    - Identify technical terms, jargon, acronyms, and key concepts
    - Create definitions based on the paper content and external references
    - Include most technical terms used in the site content (target high coverage, not a tiny curated subset)
    - Save glossary as `paper_dir/website/glossary.json` with structure:
     [
       {
         "term": "term_name",
         "definition": "clear definition",
         "section": "section_id_where_used",
         "related_terms": ["term1", "term2"]
       }
     ]

3) Generate HTML website structure in `paper_dir/website/`:
   - `index.html`: Main page with paper overview and navigation
   - `sections/`: One HTML file per major section of the paper
   - `glossary.html`: Interactive glossary page
   - `diagrams/`: Copy or symlink diagram PNGs
   - `css/styles.css`: Custom styling
   - `js/script.js`: Interactive features (glossary popups, navigation)
     - Include KaTeX for LaTeX math rendering:
       - Download KaTeX distribution (CSS, JS, fonts) from https://github.com/KaTeX/KaTeX/releases and place it in `paper_dir/website/katex/`. Use command: `curl -L https://github.com/KaTeX/KaTeX/releases/download/v0.16.9/katex.tar.gz -o katex.tar.gz && tar -xzf katex.tar.gz -C paper_dir/website/katex --strip-components=1`
       - Add local links to KaTeX assets in `<head>` of each HTML page:
         ```html
         <link rel="stylesheet" href="katex/katex.min.css">
         <script defer src="katex/katex.min.js"></script>
         <script defer src="katex/contrib/auto-render.min.js" onload="renderMathInElement(document.body);"></script>
         ```
       - Configure auto-render to recognize `\\(...\\)` and `\\[...\\]` delimiters by adding a script:
         ```html
         <script>
           document.addEventListener('DOMContentLoaded', function() {
             renderMathInElement(document.body, {
               delimiters: [
                 {left: '\\\\(', right: '\\\\)', display: false},
                 {left: '\\\\[', right: '\\\\]', display: true}
               ],
               throwOnError: false
             });
           });
         </script>
         ```
     - If using a script to generate HTML from Markdown (e.g., generate.py), ensure it preserves LaTeX delimiters and does not wrap glossary terms inside math expressions.
     - When converting Markdown content to HTML, preserve LaTeX math delimiters `\[ ... \]` and `\( ... \)` exactly as they appear in the Markdown. Do not escape backslashes or replace them with HTML entities.

 4) Implement glossary linking:
    - In all HTML content, wrap glossary terms with `<span class="glossary-term" data-term="term_name">term</span>`
    - Link most technical terms appearing in each section page to glossary definitions. If a term appears repeatedly, link the first meaningful occurrence in each section and keep additional links when useful.
    - Implement JavaScript tooltips that show term definitions on hover, using data from glossary.json. Alternatively, use CSS hover tooltips (::after pseudo-element with data-term attribute) to show term name.
    - Ensure glossary JSON is loaded correctly from both root pages and nested `sections/` pages (use correct relative paths).
    - Clicking highlighted glossary terms should navigate to the exact glossary entry anchor.
    - If tooltip definitions contain LaTeX, render math inside the tooltip content (not only in main body text).
    - Ensure internal linking between sections and glossary
    - Avoid wrapping glossary terms inside LaTeX math delimiters; ensure glossary spans do not break equation syntax

 4.1) Enrich mathematical sections:
    - For each key equation shown on the website, add a nearby "Notation" snippet listing all major variables and what each means.
    - For each key equation, add a short "Intuition" snippet (2-4 lines) that explains what the equation is doing conceptually.
    - Keep notation and intuition adjacent to the equation so readers do not need to scroll far to understand symbols.

5) Create responsive design:
   - Use modern CSS (Flexbox/Grid)
   - Ensure mobile-friendly layout
   - Include dark/light mode toggle if possible

6) Embed diagrams:
   - Display PNG diagrams with captions
   - Optionally include interactive Mermaid diagrams if feasible

7) Set up local hosting:
   - Create a simple Python HTTP server script `paper_dir/website/serve.py`
   - Write instructions in `paper_dir/website/README.md`
   - Test that the website works locally

8) Generate navigation:
    - Table of contents based on paper sections
    - Breadcrumb navigation
    - Previous/Next section buttons
    - Keep section-wise presentation fixed: maintain one page per major section with stable section navigation.

 9) Validate and test:
     - Check all links work
     - Verify glossary terms are properly linked
     - Verify glossary coverage is high across technical terms in each section
     - Ensure images load correctly
     - Ensure LaTeX equations render correctly using KaTeX
     - Verify each key equation has notation and intuition snippets

Constraints:
- Keep all outputs inside `paper_dir/website/`
- Use semantic HTML5
- Ensure accessibility (alt text for images, ARIA labels)
- Minimize external dependencies (use local CSS/JS)
- The website should work offline once generated
