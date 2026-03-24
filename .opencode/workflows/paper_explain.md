---
description: End-to-end pipeline from archive URL to interactive website with paper
  explanation.
id: paper_explain
inputs:
- description: URL to arXiv abs/pdf/e-print or a source archive.
  name: archive_url
  type: string
name: Paper Explain
steps:
- agent: archive_tex_fetcher
  id: fetch_tex
  inputs:
    archive_url: ${inputs.archive_url}
- agent: paper_resource_gatherer
  id: gather_resources
  inputs:
    archive_url: ${inputs.archive_url}
    paper_dir: ${steps.fetch_tex.outputs.paper_dir}
- agent: paper_flow_creator
  id: create_flow
  inputs:
    paper_dir: ${steps.gather_resources.outputs.paper_dir}
- agent: paper_reviewer
  id: review_flow
  inputs:
    paper_dir: ${steps.gather_resources.outputs.paper_dir}
    paper_flow_path: ${steps.create_flow.outputs.paper_flow_path}
- agent: paper_flow_creator
  id: revise_flow
  inputs:
    paper_dir: ${steps.gather_resources.outputs.paper_dir}
    paper_flow_path: ${steps.review_flow.outputs.paper_flow_path}
    review_feedback_path: ${steps.review_flow.outputs.review_feedback_path}
- agent: website_maker
  id: create_website
  inputs:
    diagrams_dir: ${steps.revise_flow.outputs.diagrams_dir}
    paper_dir: ${steps.fetch_tex.outputs.paper_dir}
    paper_flow_path: ${steps.revise_flow.outputs.paper_flow_path}
version: 1
---
