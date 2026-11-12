# Data Model

## Graph node

Current public graph nodes have:

```json
{
  "id": "token",
  "label": "Tokenization",
  "type": "concept",
  "parent": "llm-found",
  "description": "Transforms strings into token IDs.",
  "keywords": ["tokenization"],
  "url": "https://www.notion.so/...",
  "source_pages": [{"title": "Notion source", "url": "https://www.notion.so/..."}],
  "origin": "curated",
  "extraction_method": "manual_pilot",
  "review_status": "needs_review",
  "source_last_edited": "2026-10-29T08:54:14Z"
}
```

The `source_last_edited` field is optional and populated only if the latest scan matches a known source page. `description` and `keywords` are manual pilot data, not LLM-verified statements.

### Types

| Node type | Meaning | Example |
|---|---|---|
| domain | Broad knowledge area | Machine Learning |
| topic | Subfield or category | Reinforcement Learning |
| concept | Atomic knowledge unit | Tokenization |
| source | Course or other reference | CS336 |
| note | A Notion note | Lecture 1: Tokenization |
| tool | Software or implementation system | Neo4j |

### Edges

- Parent hierarchy: `parent` property (rendered as HIERARCHY).
- Candidate semantic edges: `{source, target, type, review_status}`.
- Proposed future types: `PREREQUISITE_OF`, `IS_A`, `RELATED_TO`, `APPLIED_IN`, `EXPLAINS`, `COVERED_IN`.

Semantic links in the current pilot are *candidates*, not verified ontology claims. An extraction run must never silently overwrite a human-approved edge.

## Maintenance manifest

```json
{
  "version": 1,
  "last_successful_sync": "2026-11-12T01:30:00+00:00",
  "pages": {
    "<sha256 of page UUID>": {
      "fingerprint": "<sha256 of selected block content>",
      "edited": "<Notion ISO timestamp>"
    }
  }
}
```

This file contains no page titles, URLs, or bodies. Hashes are not encryption; public hashes and edit timestamps still convey metadata. Full private content is processed in workflow memory and discarded after the run.

## Candidate review lifecycle

`detected → proposed → reviewed → approved/rejected → published`

**Implemented:** detected/proposed from page headings and optional LLM extraction (definitions, proposed graph parents, relationships, and verbatim block evidence). These are reported by private email when configured.  
**Implemented:** persistent private Notion review database and publishing of manually approved or merged concepts. The queue uses Proposed → Approved / Rejected / Merge → Published statuses. See [review queue](review-queue.md).

## Deduplication

Distinct Notion notes may map to one semantic concept. The semantic extractor currently deduplicates within a page only; cross-page resolution is planned. Do not merge based on text similarity alone; preserve source links for each occurrence. New extracted relationships require evidence (Notion page/block location) and review status.
