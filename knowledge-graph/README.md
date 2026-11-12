# AI & ML Knowledge Atlas
Interactive, publicly hosted pilot graph of curated AI/ML concepts with metadata and links to original Notion notes.

- Webpage: https://ianchen0316.github.io/knowledge-graph/
- Notion hub: https://app.notion.com/p/41675fdeb6eb81649a8df5feaa898774
- 41 curated nodes, 16 candidate semantic links.
- Node inspector shows summary, ID, hierarchy, review status, extraction method, keywords, source count and related nodes.
- No full Notion page body is published. **Labels, node summaries, and original source URLs are public.**
- Notion is the source of truth. The scheduled GitHub Actions workflow uses official Notion REST API and a read-only integration token to append headings and child pages.

## Enable automatic refresh

1. Create a Notion integration with **Read content** permission.
2. Grant the integration access to the relevant AI/ML source pages.
3. In GitHub Settings → Secrets and variables → Actions, create repository secret `NOTION_TOKEN`.
4. Run Actions → **Sync AI ML Knowledge Graph from Notion** → Run workflow.
5. By default, refresh runs daily at 01:30 UTC. If the secret is absent, it skips.
6. Before enabling refresh, review publication risk: discovered page titles and links will be visible publicly.

This is one-way sync (Notion → public site), and the pipeline does not edit Notion. **Opt-in LLM semantic extraction is implemented** for changed notes using `OPENAI_API_KEY`, with strict JSON schema, block-quote evidence verification and private SMTP email for review. LLM proposals are **not** published automatically. See [project documentation](../doc/README.md) and [semantic extraction](../doc/semantic-extraction.md). Notion embeds need the host to allow framing; otherwise use a regular page link.
