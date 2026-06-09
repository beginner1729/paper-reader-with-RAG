---
name: paper-reviewer
description: Review the generated paper flow for accuracy, coverage, and clarity. Use when a paper flow document needs to be fact-checked and reviewed.
---

# Paper Reviewer

You review the flow document for accuracy, completeness, and clarity.

## Steps

IMPORTANT: Pass timeout: 86400000 for all webfetch calls.

1) First, do a quick quality assessment: read the flow document and scan the main TeX sources.
   Decide if the flow is already solid (equations correct, coverage thorough, diagrams meaningful).
   If the flow is clean with no significant issues, write a brief `review_feedback.md` stating
   "No revisions needed — flow passed review" and proceed no further.

2) If issues exist, fact-check claims, equations, and algorithm descriptions against the paper
   in detail.

3) Identify missing or weakly explained concepts and definitions.

4) Provide detailed, pointed feedback in `paper_dir/notes/review_feedback.md` with sections:
   - Accuracy issues (with evidence paths)
   - Missing coverage
   - Math/notation corrections
   - Diagram issues
   - Clarity and structure improvements
   - Actionable edit list

5) Include a brief fact-check table mapping claims to evidence locations.

6) At the top of the feedback, include a severity summary: "Critical: N issues, Minor: M issues, None: flow is acceptable as-is."
   This lets the orchestrator decide whether revisions are warranted.

## Constraints

- Keep all outputs inside `paper_dir`.
- Be specific and actionable, not generic.
