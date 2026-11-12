#!/usr/bin/env python3
"""Update source freshness metadata for EXISTING curated nodes only."""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
manifest = json.loads((HERE / "state" / "manifest.json").read_text())
file = HERE / "index.html"
source = file.read_text(encoding="utf-8")
match = re.search(r'<script id="data" type="application/json">(.*?)</script>', source, re.S)
if not match:
    raise SystemExit("Graph data marker missing")
graph = json.loads(match.group(1))
changed = 0
for node in graph["nodes"]:
    url = node.get("url") or ""
    # Only the last 32 hex characters constitute a Notion page UUID.
    tail = urlparse(url).path.rstrip("/").split("/")[-1].split("-")[-1]
    compact = re.search(r"([0-9a-fA-F]{32})$", tail)
    if not compact:
        continue
    canonical = compact.group(1).lower()
    pageid = "-".join([canonical[:8],canonical[8:12],canonical[12:16],canonical[16:20],canonical[20:]])
    key = hashlib.sha256(pageid.encode()).hexdigest()
    entry = manifest.get("pages", {}).get(key)
    if not entry:
        continue
    if node.get("source_last_edited") != entry.get("edited"):
        node["source_last_edited"] = entry.get("edited")
        changed += 1
# Avoid changing public HTML on no-op runs.
if changed:
    graph["metadata"]["source_refresh_at_utc"] = manifest.get("last_successful_sync")
    replacement = json.dumps(graph, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    file.write_text(source[:match.start(1)] + replacement + source[match.end(1):], encoding="utf-8")
print(f"Updated source freshness on {changed} curated nodes; no new nodes published.")
