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

 3.1) Equation rendering — technical requirements for reliable rendering:

     **Absolute rules (follow these or equations WILL break):**
     - NEVER escape LaTeX backslashes as HTML entities. `\frac` must stay `\frac`, NOT `\frac` or `&#92;frac`.
     - NEVER wrap math delimiters in HTML tags. `<p>\(x^2\)</p>` is fine; `<span>\(</span>x^2<span>\)</span>` is broken.
     - ALWAYS use raw string output when generating HTML via scripts. In Python, use triple-quoted strings or `repr()`. In JS, use template literals (backticks) not concatenation.
     - ALWAYS write math blocks on their own lines for display equations; inline math stays inline.

     **KaTeX configuration script — exact copy-paste:**
     ```html
     <link rel="stylesheet" href="katex/katex.min.css">
     <script defer src="katex/katex.min.js"></script>
     <script defer src="katex/contrib/auto-render.min.js"></script>
     <script>
       document.addEventListener("DOMContentLoaded", function() {
         renderMathInElement(document.body, {
           delimiters: [
             {left: "\\(", right: "\\)", display: false},
             {left: "\\[", right: "\\]", display: true},
             {left: "$$", right: "$$", display: true},
             {left: "\\begin{equation}", right: "\\end{equation}", display: true},
             {left: "\\begin{align}", right: "\\end{align}", display: true},
             {left: "\\begin{align*}", right: "\\end{align*}", display: true},
             {left: "\\begin{aligned}", right: "\\end{aligned}", display: true}
           ],
           throwOnError: false,
           strict: false,
           trust: true,
           macros: {
             "\\R": "\\mathbb{R}",
             "\\N": "\\mathbb{N}",
             "\\E": "\\mathbb{E}",
             "\\indep": "\\perp\\!\\!\\!\\perp"
           }
         });
       });
     </script>
     ```

     **CSS for equations — prevents overflow/truncation:**
     ```css
     .katex-display { overflow-x: auto; overflow-y: hidden; padding: 0.5em 0; }
     .katex { font-size: 1.1em; }
     .katex-display > .katex { max-width: 100%; }
     .katex-html { white-space: normal; }
     ```

     **Common broken-equation patterns to catch before serving:**
     | Broken | Fixed |
     |--------|-------|
     | `\\frac{1}{2` (missing closing brace) | `\\frac{1}{2}` |
     | `$x^2$` (dollar delimiters — KaTeX won't see them) | `\\(x^2\\)` |
     | `\\(...\\)` appearing as literal text (KaTeX failed to render) | Check console for KaTeX parse errors |
     | `&` inside align environment not escaped | Keep `&` as-is inside math, use `&amp;` outside |
     | `_` outside math interpreted as markdown italics | Ensure `_` is always inside `\\(...\\)` or `\\[...\\]` |
     | `\\text{...}` with nested braces | Count braces: `\\text{some \\textit{text}}` needs balanced `{}` |
     | `\\begin{array}` without `\\end{array}` | Always pair `\\begin`/`\\end` |

     **Post-generation debugging:**
     1. Open any section HTML directly in a browser and open DevTools Console.
     2. KaTeX logs parse errors with location hints — grep for "KaTeX" in console output.
     3. View page source and search for `\(` — every occurrence must have a matching `\)`.
     4. Search source for single `\` that isn't part of `\\` — lone backslashes before non-command chars break rendering.
     5. If an equation renders as raw text, the delimiter pattern didn't match — verify exact delimiter string in renderMathInElement config matches what appears in HTML source.

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

 9) Validate and test (math equations — thorough check):
      - **Delimiter balance:** For every `\(` confirm a matching `\)`, for every `\[` confirm a matching `\]`. Scan each HTML file to catch mismatched pairs.
      - **Truncation check:** Look for incomplete LaTeX — unbalanced `{`/`}` braces, missing closing `}`, `\frac` without both arguments, `\sum`/`\int`/`\prod` without limits or body, any command cut off before its arguments.
      - **Common escape errors:** Check that `_` inside math is not interpreted as markdown italics, that `\\` is preserved as `\\\\` where needed in HTML, and that `&` is escaped as `&amp;` outside math blocks.
      - **Source cross-check:** Compare the 5-10 most important equations against the original TeX source. Verify no symbols, subscripts, or superscripts were lost.
      - **Notation/Intuition completeness:** Verify every Notation and Intuition block is fully present — not truncated mid-sentence. Check all variables in Notation blocks actually appear in the corresponding equation.
      - **Rendering test:** Flag any equation whose raw LaTeX looks malformed (unbalanced parentheses, missing operators, orphaned braces).
      - Check all links work
      - Verify glossary terms are properly linked
      - Verify glossary coverage is high across technical terms in each section
      - Ensure images load correctly
      - Fix every issue found. Record issues found and fixes applied in `paper_dir/website/validation_report.md`.

Constraints:
- Keep all outputs inside `paper_dir/website/`
- Use semantic HTML5
- Ensure accessibility (alt text for images, ARIA labels)
- Minimize external dependencies (use local CSS/JS)
- The website should work offline once generated
