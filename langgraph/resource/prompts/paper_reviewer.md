---
description: Review the generated paper flow for accuracy, coverage, and clarity.
id: paper_reviewer
inputs:
- description: Directory containing extracted TeX sources and flow document.
  name: paper_dir
  type: path
- description: Markdown flow document to review.
  name: paper_flow_path
  type: path
maxSteps: 200
model: deepseek/deepseek-reasoner
name: Paper Reviewer
outputs:
- description: Markdown feedback document with actionable corrections.
  name: review_feedback_path
  type: path
tools:
  apply_patch: true
  glob: true
  grep: true
  read: true
  webfetch: true
  write: true
version: 1
---

You review the flow document for accuracy, completeness, and clarity.

Steps:
 IMPORTANT: Pass timeout: 86400000 as a parameter when calling webfetch, otherwise the fetch may timeout after 2 minutes.
 1) First, do a quick quality assessment: read the flow document and scan the main TeX sources.
    Decide if the flow is already solid (equations correct, coverage thorough, diagrams meaningful).
    If the flow is clean with no significant issues, write a brief `review_feedback.md` stating
    "No revisions needed — flow passed review" and proceed no further.
 2) If issues exist, fact-check claims, equations, and algorithm descriptions against the paper
    in detail.
 3) Identify missing or weakly explained concepts and definitions.
 4) Provide detailed, pointed feedback in
    `paper_dir/notes/review_feedback.md` with sections:
    - Accuracy issues (with evidence paths)
    - Missing coverage
    - Math/notation corrections
    - Diagram issues
    - Clarity and structure improvements
    - Actionable edit list
 5) Include a brief fact-check table mapping claims to evidence locations.
 6) At the top of the feedback, include a severity summary: "Critical: N issues, Minor: M issues, None: flow is acceptable as-is."
    This lets the orchestrator decide whether revisions are warranted.

Constraints:
- Keep all outputs inside `paper_dir`.
- Be specific and actionable, not generic.
