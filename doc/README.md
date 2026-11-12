# AI & ML Knowledge Graph — Project Documentation

**Project:** [Public knowledge atlas](https://ianchen0316.github.io/knowledge-graph/)  
**Notion hub:** [AI & ML Knowledge Graph](https://app.notion.com/p/41675fdeb6eb81649a8df5feaa898774)  
**Scope:** Read-only incremental maintenance of the AI/ML section of Notion, curated graph metadata, and private review reports.

## Documents

- [Architecture](architecture.md) — components, data flow, graph publishing boundary, sync strategy
- [Operations](operations.md) — setup, daily operation, security, reporting, troubleshooting
- [Data model](data-model.md) — node types, edge types, provenance, manifest, review lifecycle
- [LLM semantic extraction](semantic-extraction.md) — OpenAI structured outputs, evidence validation, private delivery

## Implementation status (November 2026)

| Feature | Status |
|---|---|
| Interactive graph with node inspector | Implemented |
| 41 curated nodes and 16 candidate links | Implemented |
| Read-only Notion crawling including nested blocks | Implemented |
| Content fingerprinting and incremental page diff | Implemented |
| Candidate classification from headings | Implemented (keyword heuristic only) |
| Source freshness metadata updates on curated nodes | Implemented |
| Public-safe workflow summary | Implemented |
| Private digest email | Implemented, needs SMTP secrets |
| Daily GitHub Actions schedule | Configured, needs NOTION_TOKEN |
| LLM-based concept and relationship extraction | Implemented, opt-in with OPENAI_API_KEY and private SMTP delivery |
| Semantic entity resolution and automatic merges | Planned, NOT implemented |
| Notion page moves / writes | Not permitted by this pipeline |
| Notion change-log database writes | Planned, not implemented |

## Safety principle

This repository is public. The maintenance pipeline **never commits fetched Notion page bodies or raw private recommendations**. The site displays the currently curated graph. Newly discovered notes and heading proposals are sent only through explicitly configured private email. Optional LLM semantic proposals include quoted source evidence and also require private email delivery. Even document titles and URLs can be sensitive; enable Notion access and email only after reviewing the publication policy.
