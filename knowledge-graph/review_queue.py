#!/usr/bin/env python3
"""Private Notion review queue and controlled publication to a curated graph.

Note: queue data is in a private Notion database. Never write raw evidence
or unapproved candidate text into the public repository.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent
GRAPH_PATH = BASE / "index.html"
NOTION_VERSION = "2025-09-03"
QUEUE_ID = os.getenv("NOTION_REVIEW_DATA_SOURCE_ID", "")
TOKEN = os.getenv("NOTION_REVIEW_TOKEN", "")
ALLOWED_TYPES = {"PREREQUISITE_OF", "IS_A", "RELATED_TO", "PART_OF", "APPLIED_IN", "EXPLAINS"}
TOPICS = {"ml", "supervised", "unsupervised", "rl", "llm", "llm-found", "posttrain", "agents", "rag", "kg"}
PROPOSAL_STATES = {"Proposed", "Needs Review"}
MAX_ITEMS = 250


def normalized(s: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", s or "").casefold().split())


def candidate_key(page_id: str, fingerprint: str, kind: str, name: str) -> str:
    source = "|".join([page_id, fingerprint, kind, normalized(name)])
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:40]


def rich(value: str) -> dict:
    return {"rich_text": [{"type": "text", "text": {"content": str(value)[:1900]}}]}


def text_value(value: dict) -> str:
    return "".join(item.get("plain_text", item.get("text", {}).get("content", ""))
                   for item in value.get("rich_text", [])).strip()


def prop(row: dict, name: str) -> str:
    p = row.get("properties", {}).get(name, {})
    kind = p.get("type")
    if kind == "title":
        return "".join(i.get("plain_text", "") for i in p.get("title", []))
    if kind == "rich_text":
        return text_value(p)
    if kind == "select":
        return (p.get("select") or {}).get("name", "")
    if kind == "url":
        return p.get("url") or ""
    return ""


def request(method: str, path: str, body: dict | None = None) -> dict:
    if not TOKEN or not QUEUE_ID:
        raise RuntimeError("NOTION_REVIEW_TOKEN and NOTION_REVIEW_DATA_SOURCE_ID are required")
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    r = Request("https://api.notion.com/v1" + path, data=data, method=method, headers={
        "Authorization": "Bearer " + TOKEN,
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    })
    for attempt in range(4):
        try:
            with urlopen(r, timeout=45) as reply:
                return json.load(reply)
        except HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < 3:
                retry = exc.headers.get("Retry-After", "")
                time.sleep(int(retry) if retry.isdigit() else 2 ** attempt)
                continue
            raise RuntimeError("Notion review queue API HTTP " + str(exc.code)) from None
        except (URLError, TimeoutError):
            if attempt == 3:
                raise RuntimeError("Notion review queue API timeout") from None
            time.sleep(2 ** attempt)
    raise RuntimeError("Request failed")


def list_items() -> list[dict]:
    pages, cursor = [], None
    while True:
        data = {"page_size": 100}
        if cursor:
            data["start_cursor"] = cursor
        result = request("POST", "/data_sources/" + QUEUE_ID + "/query", data)
        pages.extend(result.get("results", []))
        if not result.get("has_more"):
            return pages
        cursor = result.get("next_cursor")


def evidence_summary(items: list[dict]) -> str:
    # Evidence stays in Notion, never the public graph.
    lines = []
    for e in items[:4]:
        lines.append(str(e.get("block_id", "")) + ": " + str(e.get("quote", ""))[:300])
    return "\n".join(lines)[:1900]


def create_properties(entry: dict, page: dict, key: str, kind: str) -> dict:
    relation = kind == "Relation"
    label = (entry["source"] + " " + entry["type"] + " " + entry["target"]
             if relation else entry["name"])
    return {
        "Name": {"title": [{"type": "text", "text": {"content": label[:1900]}}]},
        "Status": {"select": {"name": "Proposed"}},
        "Kind": {"select": {"name": kind}},
        "Candidate Key": rich(key),
        "Parent": rich("" if relation else entry.get("parent_id", "")),
        "Definition": rich("" if relation else entry.get("definition", "")),
        "Source URL": {"url": page.get("url")},
        "Evidence": rich(evidence_summary(entry.get("evidence", []))),
        "Relation Source": rich(entry.get("source", "") if relation else ""),
        "Relation Target": rich(entry.get("target", "") if relation else ""),
        "Relation Type": rich(entry.get("type", "") if relation else ""),
        "Model": rich(page.get("model", "")),
        "Confidence": rich(entry.get("confidence", "low")),
    }


def enqueue(proposals: dict, pages: dict, existing: list[dict] | None = None) -> dict:
    """Idempotently append proposals, preserving all existing review decisions."""
    existing = list_items() if existing is None else existing
    keys = {prop(row, "Candidate Key") for row in existing}
    totals = {"created": 0, "duplicates": 0}
    for page_key, extraction in proposals.items():
        page = pages[page_key]
        candidates = (
            [("Concept", c, c["name"]) for c in extraction.get("concepts", [])]
            + [("Relation", r, r["source"] + "|" + r["type"] + "|" + r["target"])
               for r in extraction.get("relations", [])]
        )
        for kind, entry, name in candidates[:MAX_ITEMS]:
            key = candidate_key(page["id"], page["fingerprint"], kind, name)
            if key in keys:
                totals["duplicates"] += 1
                continue
            properties = create_properties(entry, {**page, "model": extraction.get("model", "")}, key, kind)
            request("POST", "/pages", {
                "parent": {"type": "data_source_id", "data_source_id": QUEUE_ID},
                "properties": properties,
            })
            keys.add(key)
            totals["created"] += 1
    return totals


def graph_from_html(source: str) -> tuple[dict, re.Match]:
    match = re.search(r'<script id="data" type="application/json">(.*?)</script>', source, re.S)
    if not match:
        raise ValueError("Graph JSON marker not found")
    return json.loads(match.group(1)), match


def public_node_id(key: str) -> str:
    return "reviewed-" + key[:24]


def unique_match(nodes: list[dict], name_or_id: str) -> dict | None:
    matches = [n for n in nodes if n["id"] == name_or_id or normalized(n["label"]) == normalized(name_or_id)]
    unique = {x["id"]: x for x in matches}
    return next(iter(unique.values())) if len(unique) == 1 else None


def source_pages(node: dict, url: str) -> None:
    if not url:
        return
    pages = node.setdefault("source_pages", [])
    if not any(p.get("url") == url for p in pages):
        pages.append({"title": "Reviewed Notion source", "url": url})


def apply_reviews(graph: dict, rows: list[dict]) -> tuple[dict, dict, list[str], list[str]]:
    """Pure transformation; 'Published' means already applied.

    Approving a candidate explicitly permits publication of its description,
    name and source URL to GitHub Pages. Raw evidence is NEVER included.
    """
    nodes, edges = graph["nodes"], graph["edges"]
    counts = {"concepts": 0, "relations": 0, "merges": 0, "rejected": 0}
    applied, warnings = [], []
    ordered = sorted(rows, key=lambda r: r.get("id", ""))
    for row in ordered:
        status, kind, label = prop(row, "Status"), prop(row, "Kind"), prop(row, "Name")
        if status == "Rejected":
            counts["rejected"] += 1
            continue
        if status not in ("Approved", "Merge"):
            continue
        key = prop(row, "Candidate Key")
        if not re.fullmatch("[0-9a-f]{40}", key):
            warnings.append("Review row with invalid candidate key was skipped")
            continue
        url, parent = prop(row, "Source URL"), prop(row, "Parent")
        if status == "Merge":
            if kind != "Concept":
                warnings.append("Merge is supported for concept rows only")
                continue
            into = prop(row, "Merge Into")
            target = unique_match(nodes, into)
            if not target:
                warnings.append("Merge target missing or ambiguous")
                continue
            source_pages(target, url)
            counts["merges"] += 1
            applied.append(row["id"])
            continue
        if kind == "Concept":
            if parent not in TOPICS or not any(n["id"] == parent for n in nodes):
                warnings.append("Approved concept has missing or invalid parent")
                continue
            current = unique_match(nodes, label)
            node_id = public_node_id(key)
            prior_by_id = next((n for n in nodes if n["id"] == node_id), None)
            if current and current["id"] != node_id:
                warnings.append("Concept name exists: use Merge instead of Approved")
                continue
            if not prior_by_id:
                node = {
                    "id": node_id, "label": label[:100], "type": "concept",
                    "parent": parent, "description": prop(row, "Definition")[:600],
                    "keywords": label.lower().split()[:8], "url": url or None,
                    "source_pages": [], "origin": "notion_review",
                    "extraction_method": "llm_reviewed", "review_status": "approved",
                }
                source_pages(node, url)
                nodes.append(node)
                counts["concepts"] += 1
            applied.append(row["id"])
        elif kind == "Relation":
            source, target, relation = (prop(row, "Relation Source"), prop(row, "Relation Target"),
                                        prop(row, "Relation Type"))
            start, end = unique_match(nodes, source), unique_match(nodes, target)
            if not start or not end or start["id"] == end["id"] or relation not in ALLOWED_TYPES:
                warnings.append("Approved relation has unresolved endpoints or invalid type")
                continue
            exists = any(e["source"] == start["id"] and e["target"] == end["id"]
                         and e["type"] == relation for e in edges)
            if not exists:
                edges.append({"source": start["id"], "target": end["id"],
                              "type": relation, "review_status": "approved"})
                counts["relations"] += 1
            applied.append(row["id"])
    return graph, counts, applied, warnings


def update_graph_file(rows: list[dict]) -> tuple[dict, list[str], list[str]]:
    source = GRAPH_PATH.read_text(encoding="utf-8")
    graph, match = graph_from_html(source)
    updated, counts, applied, warnings = apply_reviews(graph, rows)
    if counts["concepts"] or counts["relations"] or counts["merges"]:
        rendered = json.dumps(updated, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
        GRAPH_PATH.write_text(source[:match.start(1)] + rendered + source[match.end(1):], encoding="utf-8")
    return counts, applied, warnings


def mark_published(page_ids: list[str]) -> None:
    for page_id in page_ids:
        request("PATCH", "/pages/" + page_id, {"properties": {"Status": {"select": {"name": "Published"}}}})


def main() -> None:
    if not TOKEN or not QUEUE_ID:
        raise SystemExit("Review queue integration is not configured")
    rows = list_items()
    counts, applied, warnings = update_graph_file(rows)
    print(json.dumps({"counts": counts, "applied": len(applied),
                      "warnings": len(warnings)}, sort_keys=True))
    # Post-commit finalization is handled by workflow (see finalize_published.py).
    destination = os.getenv("GITHUB_OUTPUT")
    if destination and applied:
        with open(destination, "a", encoding="utf-8") as file:
            file.write("applied=" + ",".join(applied) + "\n")


if __name__ == "__main__":
    main()
