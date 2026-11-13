# Operations Runbook

## Daily schedule

GitHub Actions: [Maintain AI ML Knowledge Graph](https://github.com/ianchen0316/ianchen0316.github.io/actions/workflows/sync-ai-ml-graph.yml)  
Cron: `30 1 * * *` = 09:30 Asia/Taipei (UTC+8). GitHub's scheduled runs can be delayed.

## 1. Create a Notion integration

1. In Notion integrations, create an integration with **Read content** capability.
2. Grant the integration explicit access to both top-level **Machine Learning** and **LLM Finetuning** source roots, along with other enabled AI & ML roots and relevant descendants.
3. Copy its token. **Never commit the token.**
4. In GitHub repository **Settings → Secrets and variables → Actions**, create the secret `NOTION_TOKEN`.
5. Trigger the workflow manually using **Run workflow** and review its summary.

The Notion source integration is read-only; this pipeline does not create, move, delete or edit source Notion pages. The separate project hub is now at the top-level Private sidebar, while the private review database is maintained separately. Do not give it write permission just for this workflow.

## 2. Optional private daily email

Set these GitHub Actions repository secrets:

| Secret | Meaning |
|---|---|
| `SMTP_HOST` | Your mail server host |
| `SMTP_USERNAME` | Sender login |
| `SMTP_PASSWORD` | SMTP app password or credential |
| `REPORT_EMAIL_TO` | Recipient address |

Optional repository variables:

| Variable | Default |
|---|---|
| `SMTP_PORT` | `465` (TLS) |
| `REPORT_EMAIL_FROM` | SMTP_USERNAME |

The report contains page titles, Notion links and suggested heading classifications, plus optional LLM concept/relation proposals with verbatim block quotes. Use a trusted email destination. No email is sent if SMTP settings are missing; the workflow summary then shows only aggregate counts.

## 2a. Enable opt-in LLM semantic extraction

Add the repository secret `OPENAI_API_KEY`. When this is configured, changed notes are sent to the OpenAI Responses API for strict structured concept and relationship extraction. The model defaults to `gpt-4o-mini`, configurable via repository variable `OPENAI_MODEL`. Other variables: `SEMANTIC_MAX_PAGES_PER_RUN` (default 5) and `SEMANTIC_BACKFILL_BASELINE` (default false). **Private SMTP delivery must be fully configured** or the pipeline rejects LLM extraction without transmitting page content.

See [LLM semantic extraction](semantic-extraction.md) for evidence validation, privacy, costs, model limits, and failures.

## 2b. Configure the private concept review queue

The private database **AI & ML — Concept Review Queue** has been created in Notion. In GitHub Actions add the secret `NOTION_REVIEW_TOKEN` (a separate Notion integration with read, insert and update access only to that database) and variable `NOTION_REVIEW_DATA_SOURCE_ID` (from the Notion database's data-source settings). New LLM proposals are enqueued automatically when configured. Changing a row to Approved or Merge publishes approved metadata to the public graph during the next run; Rejected stays private. See [review queue](review-queue.md).

## 2c. Enable the Node Registry synchronization

A [Node Registry database](https://app.notion.com/p/0a30f98a97504d46ac38645b24f7ac1f) now lives under the top-level project hub. It contains canonical graph nodes, tags, multiple linked source pages, and explicit breakdown review status. Add GitHub secret `NOTION_NODE_REGISTRY_TOKEN` and variable `NOTION_NODE_REGISTRY_DATA_SOURCE_ID` = `c38207ac-27b1-4e42-a938-c26da54d6613`. The corresponding Notion integration needs read, insert and update access to this database only. The workflow will add missing approved nodes and synchronize graph-owned name/type/parent/summary fields, without overwriting hand-curated tags, source links, or breakdown decisions. See [Node Registry](node-registry.md).

## 3. Review a run

- Open the Actions run summary for pages scanned and counts added/modified/potentially missing.
- Inspect the private email for concept suggestions and their original source pages.
- The first successful run establishes a **baseline** and does not count all existing notes as new.
- If you approve a new graph node, add it through a reviewed content change. Automatic publication of unreviewed extracted concepts is disabled by design.

## 4. Manual development

```bash
python3 -m unittest discover -s knowledge-graph -p 'test_*.py' -v
NOTION_TOKEN=... DRY_RUN=true python3 knowledge-graph/maintain.py
NOTION_TOKEN=... python3 knowledge-graph/maintain.py
python3 knowledge-graph/refresh_curated.py
```

The state manifest is committed only by the workflow after a successful non-dry-run scan. Do not run a real local sync and commit its public state from a laptop unless you have checked the result for sensitive metadata. The crawler reads all accessible blocks on each scan, so API usage may grow with workspace size.

## 5. Privacy and limitations

- GitHub Pages is public; anything committed to the graph JSON is public.
- Current curated node names, summaries and Notion links are already public.
- Never commit a detailed change report or raw Notion content.
- The review digest is optional when the private Notion review queue is configured; GitHub logs expose only aggregate counts.
- Heading-based classification is heuristic; optional LLM extraction proposes richer concepts and relations but still requires human review.
- The current graph does not yet edit Notion or support bidirectional synchronization.

## 6. Troubleshooting

| Symptom | Action |
|---|---|
| Workflow says NOTION_TOKEN not configured | Add the repository secret |
| 403/404 reading a Notion page | Share the root/descendant page with the integration |
| Scan incomplete | Increase `NOTION_MAX_PAGES` or fix permissions; rerun |
| No email report | Configure SMTP secrets, recipient and port |
| Website outdated | Inspect GitHub Pages build and confirm latest commit |
| Unexpected new concepts | Review only; the crawler will not publish them automatically |

## Adding another section

See [Workspace taxonomy](workspace-taxonomy.md). New source roots should be explicitly registered with a semantic domain rather than assumed to be new public domain nodes. The current LLM Finetuning source is already present in the crawler and now represented explicitly in the curated graph.

## 7. Next engineering tasks

Implement private approval storage, evidence-backed LLM extraction, semantic clustering and duplicate resolution, then approved publication. A Notion change-log page may be maintained via a separate narrowly scoped integration in the future.
