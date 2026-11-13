# Personal Knowledge Atlas — AI & ML Domain
Interactive, publicly hosted pilot graph of curated AI/ML concepts with metadata and links to original Notion notes.

- Webpage: https://ianchen0316.github.io/knowledge-graph/
- Notion project hub (now in the Private sidebar root): https://app.notion.com/p/41675fdeb6eb81649a8df5feaa898774
- Source collections: [Machine Learning](https://www.notion.so/963f79956cee49e0a85707ca6e3a4853) and [LLM Finetuning](https://www.notion.so/3f275fdeb6eb809c8ff0de72173259bb). Both map to the unified AI & ML domain.
- 50 curated nodes, including 9 source/lecture nodes for the top-level LLM Finetuning collection; 22 candidate or source-mapping semantic links.
- Node inspector shows summary, ID, hierarchy, review status, extraction method, keywords, source count and related nodes.
- No full Notion page body is published. **Labels, node summaries, and original source URLs are public.**
- Notion is the source of truth. The scheduled GitHub Actions workflow uses official Notion REST API and a read-only integration token to scan pages and refresh curated metadata. Newly discovered headings and LLM proposals are not directly published.

## Enable automatic refresh

1. Create a Notion integration with **Read content** permission.
2. Grant the integration access to the relevant AI/ML source pages.
3. In GitHub Settings → Secrets and variables → Actions, create repository secret `NOTION_TOKEN`.
4. Run Actions → **Sync AI ML Knowledge Graph from Notion** → Run workflow.
5. By default, refresh runs daily at 01:30 UTC. If the secret is absent, it skips.
6. Before enabling refresh, review publication risk: discovered page titles and links will be visible publicly.

This is one-way sync (Notion → public site), and the pipeline does not edit Notion. **Opt-in LLM semantic extraction is implemented** for changed notes using `OPENAI_API_KEY`, with strict JSON schema, block-quote evidence verification and private SMTP email for review. LLM proposals are **not** published automatically. See [project documentation](../doc/README.md) and [semantic extraction](../doc/semantic-extraction.md). Notion embeds need the host to allow framing; otherwise use a regular page link.

## Notion Node Registry

The project hub now contains a private [Node Registry](https://app.notion.com/p/0a30f98a97504d46ac38645b24f7ac1f) with 50 canonical graph nodes, tags, links to one or more source Notion pages, and breakdown review flags. The optional daily `sync_node_registry.py` adds future approved graph nodes and updates only graph-owned metadata, preserving manual tags, source associations and breakdown statuses. Configure secret `NOTION_NODE_REGISTRY_TOKEN` and variable `NOTION_NODE_REGISTRY_DATA_SOURCE_ID` to activate it. See [Node Registry docs](../doc/node-registry.md).

## Review and publish LLM proposals

The private [Notion Concept Review Queue](../doc/review-queue.md) now supports Proposed → Approved / Rejected / Merge → Published. The pipeline enqueues new LLM concept and relation proposals when a separate review integration is configured, and only publishes manually approved metadata or reviewed source merges to the public graph. Raw Notion evidence is never published. Configure the GitHub secret `NOTION_REVIEW_TOKEN` and variable `NOTION_REVIEW_DATA_SOURCE_ID`; grant that integration access to the private Notion database. See [operations](../doc/operations.md) for activation.
