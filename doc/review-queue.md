# Concept Review Queue & Controlled Publication

**Status:** Review database and publisher implemented. Integration with a live token and end-to-end GitHub Actions run still needs verification.

## Private Notion review queue

The review queue is a separate Notion database named **AI & ML — Concept Review Queue**, created in the user's private workspace. Its database and data source IDs are **not committed** in the public GitHub repository. The workflow requires a separately permissioned Notion integration.

Suggested columns:

| Property | Role |
|---|---|
| Name | Concept title or relationship summary |
| Kind | Concept / Relation |
| Status | Proposed, Needs Review, Approved, Rejected, Merge, Published |
| Candidate Key | Stable hash of page, fingerprint, type and concept/relation |
| Parent | Suggested graph topic ID |
| Definition | Proposed concept definition |
| Source URL | Original Notion note link |
| Evidence | Source block IDs + verbatim quotations, private only |
| Relation Source / Target / Type | Relationship proposal |
| Merge Into | Canonical existing graph node ID or unambiguous label |
| Model / Confidence | Audit metadata |

The review database is separate from the public graph's Notion hub, so it does **not** inherit the hub's sharing permissions. Check the database sharing settings before enabling ingestion.

## Review lifecycle

\`\`\`mermaid
flowchart LR
  A[LLM extraction] --> B[Notion Proposed]
  B -->|review| C{Decision}
  C -->|Approved| D[Publish candidate]
  C -->|Merge + Merge Into| E[Attach source to existing node]
  C -->|Rejected| F[Keep review history]
  D --> G[GitHub commit and push]
  E --> G
  G --> H[Mark Published in Notion]
\`\`\`

### Approve a concept

1. Open the review queue and inspect the source note, definition, parent topic, and private evidence.
2. Verify that the concept is distinct from existing graph nodes. Edit its Name, Definition, and Parent if needed.
3. Set **Status = Approved**.
4. The next GitHub Actions run adds an approved concept to the public graph. Evidence quotes stay private, but **the approved Name, Definition, Parent and Source URL become public**.
5. After a successful push, the workflow sets **Status = Published**.

### Reject a candidate

Set **Status = Rejected**. This prevents publication and preserves the historical decision. Regeneration of the same page version and candidate will not reopen the existing decision.

### Merge into an existing concept

Set **Status = Merge**, then fill **Merge Into** with the destination node's ID (preferred) or a uniquely matching label. The pipeline will add the reviewed Notion Source URL to that node's public \`source_pages\` and leave its canonical name and definition unchanged. After a successful push, the row is marked **Published**.

### Approve a relationship

Change its status to **Approved**. The graph publisher requires:
- an allowed relation type;
- both endpoint names/IDs resolved **unambiguously** in the curated graph;
- two distinct endpoints.

If an endpoint is not yet present, publish its approved concept first (or in the same run). Invalid or ambiguous relationships stay Approved and are retried when corrected.

## Configure GitHub Actions

In **Settings → Secrets and variables → Actions**:

| Kind | Key | Purpose |
|---|---|---|
| Secret | \`NOTION_REVIEW_TOKEN\` | Notion integration token with **Read content, Insert content, Update content** capabilities and explicit access to the private review database |
| Variable | \`NOTION_REVIEW_DATA_SOURCE_ID\` | Data source ID from Notion database settings |
| Secret | \`OPENAI_API_KEY\` | Optional extraction; without it you can still publish manually approved queue items |
| Secret | \`NOTION_TOKEN\` | Read-only access to source AI/ML Notion pages |

Give the review integration access **only to the review database**; use a separate token for the source notes where possible. Full review reports by email remain optional.

The workflow invokes \`knowledge-graph/maintain.py\` (optional new proposals), \`knowledge-graph/review_queue.py\` (approved graph modifications), commits/pushes the curated website, then \`knowledge-graph/finalize_published.py\` (sets review rows to Published). All writes to Notion by this feature target **review queue rows only**; original source notes are never edited.

## Idempotence & failure recovery

- Candidate keys are versioned hashes of source page UUID, page fingerprint, kind, and normalized candidate name or relation. Reprocessing the same page version does not duplicate queue rows.
- Existing queue decisions are never reset by extraction.
- Publicly published graph nodes use stable \`reviewed-<candidate-hash>\` IDs.
- A second publication pass recognizes previously published nodes and edges.
- **Publishing order:** concepts before relationships, so same-run approvals can resolve endpoints.
- A failed Git push prevents rows from being marked Published; retry remains safe.
- If Git succeeds but Notion status update fails, retry republishes idempotently and attempts status finalization.
- If email fails after successful queue ingestion, the next run skips duplicate candidates.

## Boundaries and limitations

- Review rows contain private Notion titles, source URLs and evidence; avoid sharing the database publicly.
- Approval is treated as authorization to publish the listed fields on a public website.
- No automatic semantic duplicate resolution across different Notion pages; choose **Merge** when appropriate.
- Reviews are executed during scheduled/manual GitHub Actions jobs, not instantly when a status changes.
- No standalone custom review web UI; the Notion database is the approval interface.
- Merges **attach provenance**; they do not overwrite existing concept descriptions or rewire relationship endpoints.
- Schema changes require updates to both this documentation and \`review_queue.py\`.
- Automated tests mock API requests and cover basic validation and idempotence; production Notion API integration has not yet been tested.

## Offline tests

\`\`\`bash
python3 -m unittest discover -s knowledge-graph -p 'test_*.py' -v
\`\`\`

## Source code

- \`knowledge-graph/review_queue.py\`: create candidates, fetch decisions, publish approved graph metadata
- \`knowledge-graph/finalize_published.py\`: set successful rows to Published after Git push
- \`knowledge-graph/test_review_queue.py\`: offline review decision tests
