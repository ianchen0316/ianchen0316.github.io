#!/usr/bin/env python3
"""Synchronize approved graph node metadata into a private Notion Node Registry.

Only create missing registry rows and update a small set of graph-owned fields
in existing rows. Never overwrite user-edited tags, breakdown decisions,
source associations, or private review comments.
"""
from __future__ import annotations
import json
import os
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
GRAPH = HERE / "index.html"
SOURCE_VERSION = "2025-09-03"
TOKEN = os.getenv("NOTION_NODE_REGISTRY_TOKEN", "")
DATA_SOURCE = os.getenv("NOTION_NODE_REGISTRY_DATA_SOURCE_ID", "")
KNOWN_TAGS = {"LLM", "Training", "Fine-Tuning", "RL", "Foundations",
              "Agents", "Knowledge Graph", "Source Note", "ML", "Course", "GraphRAG"}


def request(method: str, path: str, body: dict | None = None) -> dict:
    if not TOKEN or not DATA_SOURCE:
        raise RuntimeError("Node Registry integration not configured")
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body else None
    req = Request("https://api.notion.com/v1" + path, data=data, method=method, headers={
        "Authorization": "Bearer " + TOKEN,
        "Notion-Version": SOURCE_VERSION,
        "Content-Type": "application/json",
    })
    for attempt in range(5):
        try:
            with urlopen(req, timeout=40) as response:
                return json.load(response)
        except HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 4:
                delay = e.headers.get("Retry-After", "")
                time.sleep(int(delay) if delay.isdigit() else 2 ** attempt)
                continue
            raise RuntimeError("Node Registry API HTTP " + str(e.code)) from None
        except (URLError, TimeoutError):
            if attempt == 4:
                raise RuntimeError("Node Registry API network failure") from None
            time.sleep(2 ** attempt)
    raise RuntimeError("Node Registry API failed")


def graph_nodes() -> list[dict]:
    html = GRAPH.read_text(encoding="utf-8")
    match = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S)
    if not match:
        raise ValueError("Unable to locate public graph JSON")
    return json.loads(match.group(1))["nodes"]


def text_prop(value: str) -> dict:
    return {"rich_text": [{"type": "text", "text": {"content": str(value)[:1900]}}]}


def title_prop(value: str) -> dict:
    return {"title": [{"type": "text", "text": {"content": str(value)[:1900]}}]}


def get_text(row: dict, name: str) -> str:
    p = row.get("properties", {}).get(name, {})
    return "".join(x.get("plain_text", x.get("text", {}).get("content", ""))
                   for x in p.get("rich_text", []))


def source_links(node: dict) -> list[str]:
    values = [p.get("url") for p in (node.get("source_pages") or []) if p.get("url")]
    if node.get("url"):
        values.insert(0, node["url"])
    return list(dict.fromkeys(values))


def owned_fields(node: dict) -> dict:
    return {
        "Name": title_prop(node.get("label", "")),
        "Node ID": text_prop(node["id"]),
        "Node Type": {"select": {"name": node["type"].capitalize()}},
        "Domain": {"select": {"name": "AI & ML"}},
        "Parent ID": text_prop(node.get("parent") or ""),
        "Summary": text_prop(node.get("description") or ""),
    }


def initial_fields(node: dict) -> dict:
    fields = owned_fields(node)
    links = source_links(node)
    fields.update({
        "Primary Source": {"url": links[0]} if links else {"url": None},
        "Source Pages": text_prop("\n".join(links)),
        "Source Count": {"number": len(links)},
        "Review Status": {"select": {"name": "Approved" if node.get("review_status") == "approved" else "Curated"}},
        "Breakdown": {"select": {"name": "Not assessed"}},
    })
    return fields


def list_registry() -> list[dict]:
    cursor, results = None, []
    while True:
        payload = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        data = request("POST", "/data_sources/" + DATA_SOURCE + "/query", payload)
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            return results
        cursor = data["next_cursor"]


def plan_changes(nodes: list[dict], rows: list[dict]) -> tuple[list[dict], list[tuple[str, dict]]]:
    """Validate unique graph/registry identifiers. Preserve manual registry fields."""
    existing = {}
    for row in rows:
        key = get_text(row, "Node ID")
        if not key:
            continue
        if key in existing:
            raise ValueError("Duplicate node ID in Notion registry: " + key)
        existing[key] = row
    seen, creates, updates = set(), [], []
    for node in nodes:
        nid = node["id"]
        if nid in seen:
            raise ValueError("Duplicate graph node ID: " + nid)
        seen.add(nid)
        if nid not in existing:
            creates.append(initial_fields(node))
            continue
        row = existing[nid]
        # User-edited tags, sources, statuses and breakdown decisions are untouched.
        properties = owned_fields(node)
        delta = {}
        for name in ("Name", "Node Type", "Domain", "Parent ID", "Summary"):
            p = row.get("properties", {}).get(name, {})
            if name == "Name":
                value = "".join(x.get("plain_text", "") for x in p.get("title", []))
                target = node.get("label", "")
            elif name in ("Node Type", "Domain"):
                value = (p.get("select") or {}).get("name", "")
                target = node["type"].capitalize() if name == "Node Type" else "AI & ML"
            else:
                value = get_text(row, name)
                target = node.get("parent") or "" if name == "Parent ID" else node.get("description") or ""
            if value != target:
                delta[name] = properties[name]
        if delta:
            updates.append((row["id"], delta))
    return creates, updates


def synchronize(nodes: list[dict] | None = None) -> dict:
    nodes = graph_nodes() if nodes is None else nodes
    rows = list_registry()
    creates, updates = plan_changes(nodes, rows)
    for fields in creates:
        request("POST", "/pages", {
            "parent": {"type": "data_source_id", "data_source_id": DATA_SOURCE},
            "properties": fields,
        })
    for page_id, fields in updates:
        request("PATCH", "/pages/" + page_id, {"properties": fields})
    return {"existing": len(rows), "created": len(creates), "updated": len(updates)}


if __name__ == "__main__":
    counts = synchronize()
    print("Node Registry sync (counts only):", json.dumps(counts))
