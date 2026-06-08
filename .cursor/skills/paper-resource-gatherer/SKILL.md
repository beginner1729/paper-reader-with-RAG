---
name: paper-resource-gatherer
description: Build a paper outline and gather external references for key citations. Use when resources like outline, bibliography, or external references are needed for a paper.
---

# Paper Resource Gatherer

You gather core resources needed to understand the paper and keep everything
inside the paper folder.

## Steps

IMPORTANT: Pass timeout: 86400000 for all bash and webfetch calls.

1) If `paper_dir` is missing, spawn the archive-tex-fetcher skill with `archive_url` and
   continue with remote resource gathering while it runs.

2) Use webfetch to read the arXiv abstract page (if the URL is arXiv) and
   capture title, authors, abstract, and the main problem statement.

3) Once `paper_dir` is available, locate the main TeX file (look for
   `\documentclass` and `\begin{document}`) and build a section outline.
   Save it to `paper_dir/notes/paper_outline.md` with:
   - Title/author/abstract (if available)
   - Main contributions and claims
   - Section-by-section outline
   - Key definitions, theorems, and datasets

4) Extract bibliography sources from `.bib` files, `\bibliography{}` calls,
   and inline `\bibitem` entries. Select the most important citations
   (intro/related work/core method). For each, use webfetch to gather
   a short abstract or definition. Save to
   `paper_dir/notes/bibliography_summary.md` with source URLs.

5) Create `paper_dir/notes/resource_index.md` listing all gathered assets:
   tex notes, outline, bibliography summary, and any external URLs used.

## Constraints

- Store everything inside `paper_dir`.
- If external sources cannot be fetched, note the missing items explicitly.
