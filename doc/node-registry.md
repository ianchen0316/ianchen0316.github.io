# Notion Node Registry

The **Knowledge Atlas — Node Registry** is a Notion database nested under the top-level [Personal Knowledge Atlas — Project Hub](https://app.notion.com/p/41675fdeb6eb81649a8df5feaa898774).

- [Open Node Registry](https://app.notion.com/p/0a30f98a97504d46ac38645b24f7ac1f)
- Private Notion data source: \`collection://c38207ac-27b1-4e42-a938-c26da54d6613\`
- Initial AI & ML population: **50 nodes** (existing curated public graph)
- Five initially have **more than one Notion source**; three are flagged as **breakdown candidates**.
- All values were seeded from the curated public graph, with additional course-note associations grounded in the reviewed Notion source structure. This is not a completed workspace-wide semantic audit.

## Purpose

A **canonical concept** may be described by many independent Notion pages. Do not create duplicate concept rows simply because another note covers it. Keep the registry node ID stable and attach multiple source pages to the existing canonical node.

\`\`\`mermaid
flowchart LR
   A["Tokenization (canonical node)"] --> B["Tokenization concept page"]
   A --> C["CS336: Lecture 1"]
   D["Transformers (canonical node)"] --> E["Transformer concept page"]
   D --> F["CME295 Lecture 1"]
   D --> G["CME295 Lecture 2"]
   D --> H["CS336 Architectures"]
\`\`\`

## Database properties

| Property | Type | Source of truth |
|---|---|---|
| Name | Title | Graph-owned |
| Node ID | Text | Immutable key from graph |
| Node Type | Select | Graph-owned: Domain/Topic/Concept/Source/Note/Tool |
| Domain | Select | Currently AI & ML |
| Parent ID | Text | Graph-owned hierarchy |
| Summary | Text | Curated graph description |
| Tags | Multi-select | Human-maintained |
| Primary Source | URL | Human-maintained after initialization |
| Source Pages | Rich text with newline-separated URLs | Human-maintained; multiple pages allowed |
| Source Count | Number | Initially seeded; should be maintained when manually adding links |
| Review Status | Select | Curated/Needs Review/Approved |
| Breakdown | Select | Not assessed/Candidate/Priority/Not needed/Completed |
| Breakdown Reason | Text | Reviewer explanation |
| Breakdown Targets | Text | Suggested child concepts |

Each database row also has a body with clickable Notion mentions to its original source notes. You can open these immediately from the registry. For now, the free-text URL list and row body are an indexed convenience, not an automatically maintained bidirectional relation to arbitrary Notion pages.

## Breakdown candidates

| Row | Status | Reason |
|---|---|---|
| Lecture 1: Tokenization (CS336) | Priority | Mixes tokenization details with broader course topics and training/architecture notes |
| Agentic AI course notes | Priority | Many distinct multi-week topics, including reflection, tool use and evaluation |
| GraphRAG | Candidate | Distinct KG construction, simplification and retrieval concepts |

These flags were chosen after inspecting the actual content and headings. They do not mean the notes are incorrect or that they will be automatically split. The remaining nodes default to **Not assessed**, not **Not needed**.

For review, filter the Notion database by \`Breakdown\` = \`Candidate\` or \`Priority\`. Check the notes first, create or link canonical concepts, and mark \`Completed\` only after a manual reorganization or concept extraction review.

## Synchronization

GitHub source: \`knowledge-graph/sync_node_registry.py\`. It is included in the daily workflow **after successful graph publication** when configured.

For a new graph node, the script creates a matching registry row with its ID, type, parent, description and source URLs. For an existing row, it updates only these **graph-owned fields** if changed: Name, Node Type, Domain, Parent ID, Summary.

**The script deliberately never overwrites:** Tags, Breakdown, Breakdown Reason, Breakdown Targets, Source Pages, Source Count, Primary Source, Review Status, or custom text in the row body.

Changes you make directly in the registry are **not yet synchronized back to the webpage**, and manual Source Count values are not recalculated by this version. This prevents unexpected clobbering but means the registry is not a fully bidirectional source-of-truth system.

### Enable daily sync

1. Create a dedicated Notion integration with Read/Insert/Update content permission **only for the Node Registry database**. Keep source-note access with its separate read-only integration.
2. Share the Node Registry database with that integration.
3. Add GitHub Actions secret \`NOTION_NODE_REGISTRY_TOKEN\`.
4. Add GitHub Actions variable \`NOTION_NODE_REGISTRY_DATA_SOURCE_ID\` = \`c38207ac-27b1-4e42-a938-c26da54d6613\`.
5. Run the GitHub Actions maintenance workflow manually. Inspect counts in the job logs.
6. Once verified, daily runs will maintain graph-owned metadata and add newly approved nodes to the private registry.

The registry is a Notion database under the project hub, but its records may contain sensitive note titles/links. Verify the hub and database permissions before sharing them publicly.

## Future improvements

- Add a dedicated **Source Registry** database with one row per original Notion page, and a two-way Notion Relation between canonical Node Registry records and source records. This would allow proper relational filtering and source-level breakdown review.
- Update source associations, tags and breakdown decisions through controlled, conflict-aware reconciliation.
- Detect split candidates from page structure/content and propose them into a review queue instead of automatically changing notes.
- Extend beyond AI & ML to the entire Notion workspace, maintaining stable domain IDs and a consistent registry schema.
