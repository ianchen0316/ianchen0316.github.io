#!/usr/bin/env python3
"""Daily AI/ML knowledge graph maintenance.

Read-only for Notion. Only reviewed concepts are published automatically.
Private candidate details are delivered via optional SMTP, not committed.
Standard-library implementation for GitHub Actions.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import html
import json
import os
from pathlib import Path
import re
import smtplib
import ssl
import sys
import time
from email.message import EmailMessage
import semantic_extract
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
STATE = HERE / "state" / "manifest.json"
SITE = HERE / "index.html"
ROOTS = {
    "ml": "963f7995-6cee-49e0-a857-07ca6e3a4853",
    "llm": "3f275fde-b6eb-809c-8ff0-de72173259bb",
    "agents": "28f75fde-b6eb-8048-9783-cf7af2337650",
    "kg": "19e75fde-b6eb-80bc-bb83-f5c1c80a6e09",
}
MAX_PAGES = int(os.getenv("NOTION_MAX_PAGES", "250"))
MAX_BLOCK_DEPTH = int(os.getenv("NOTION_MAX_BLOCK_DEPTH", "5"))
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def rich_text(parts: list) -> str:
    return "".join(item.get("plain_text", item.get("text", {}).get("content", "")) for item in parts)


def notion_request(path: str) -> dict:
    if not NOTION_TOKEN:
        raise RuntimeError("NOTION_TOKEN not set")
    url = "https://api.notion.com/v1" + path
    req = Request(url, headers={
        "Authorization": "Bearer " + NOTION_TOKEN,
        "Notion-Version": "2022-06-28",
        "Accept": "application/json",
    })
    for attempt in range(5):
        try:
            with urlopen(req, timeout=35) as response:
                return json.load(response)
        except HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < 4:
                delay = exc.headers.get("Retry-After", "")
                time.sleep(int(delay) if delay.isdigit() else 2 ** attempt)
                continue
            raise
        except (TimeoutError, URLError):
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("Notion retries exhausted")


def block_children(block_id: str) -> list[dict]:
    results, cursor = [], None
    while True:
        suffix = "?page_size=100" + ("&start_cursor=" + quote(cursor) if cursor else "")
        batch = notion_request("/blocks/" + block_id + "/children" + suffix)
        results.extend(batch.get("results", []))
        if not batch.get("has_more"):
            return results
        cursor = batch["next_cursor"]


def snapshot_page(page_id: str) -> dict:
    """Read a page including nested headings, text blocks and child-page references."""
    page = notion_request("/pages/" + page_id)
    blocks, titles, child_ids = [], [], []
    count = 0

    def descend(parent_id: str, depth: int) -> None:
        nonlocal count
        if depth > MAX_BLOCK_DEPTH:
            return
        for block in block_children(parent_id):
            kind, bid = block["type"], block["id"]
            value = block.get(kind, {})
            content = rich_text(value.get("rich_text", [])) if isinstance(value, dict) else ""
            if kind == "child_page":
                child_ids.append(bid)
                content = value.get("title", "")
            if kind.startswith("heading_") and content:
                titles.append({"block_id": bid, "title": content.strip()})
            # No content leaves the process unless notification is explicitly configured.
            blocks.append({"id": bid, "kind": kind, "content": content})
            count += 1
            if block.get("has_children") and kind not in ("child_page", "child_database"):
                descend(bid, depth + 1)

    descend(page_id, 0)
    serialized = json.dumps(blocks, sort_keys=True, ensure_ascii=False)
    title = rich_text(next((v.get("title", []) for v in page.get("properties", {}).values()
                            if v.get("type") == "title"), []))
    return {
        "id": page_id,
        "title": title or "Untitled",
        "edited": page.get("last_edited_time"),
        "fingerprint": digest(title + "\n" + serialized),
        "headings": titles,
        "children": child_ids,
        "text": "\n".join(x["content"] for x in blocks if x["content"])[:18000],
        "block_count": count,
        "evidence_blocks": blocks,
        "url": page.get("url") or "https://www.notion.so/" + page_id.replace("-", ""),
    }


def load_manifest() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"version": 1, "pages": {}, "last_successful_sync": None}


def safe_public_state(page: dict) -> dict:
    """Do not commit page titles, URLs, content, or internal Notion block IDs."""
    return {"fingerprint": page["fingerprint"], "edited": page["edited"]}


def page_key(page_id: str) -> str:
    return digest(page_id)


def collect_pages() -> tuple[dict, list[str]]:
    result, warnings, pending = {}, [], list(ROOTS.values())
    seen = set()
    while pending and len(seen) < MAX_PAGES:
        pid = pending.pop(0)
        if pid in seen:
            continue
        seen.add(pid)
        try:
            page = snapshot_page(pid)
            result[page_key(pid)] = page
            pending.extend(page["children"])
        except Exception as exc:
            warnings.append("Some pages could not be read (" + type(exc).__name__ + ").")
    if pending:
        warnings.append("Page cap reached: scan is incomplete.")
    return result, warnings


def classify(title: str, text: str) -> dict:
    """Conservative heuristic. Suggestions are NOT verified semantic facts."""
    haystack = (title + " " + text[:2000]).lower()
    rules = [
        ("posttrain", ["lora", "qlora", "peft", "sft", "fine-tun", "dpo", "alignment"]),
        ("rl", ["policy gradient", "actor critic", "actor-critic", "reinforcement", "ppo", "reward shaping"]),
        ("llm-found", ["tokeniz", "bpe", "embedding", "self-attention", "transformer"]),
        ("rag", ["graphrag", "retrieval augmented", "retrieval-augmented", "rag"]),
        ("agents", ["agentic", "agent", "tool call", "memory management"]),
        ("kg", ["neo4j", "knowledge graph", "cypher", "graph neural"]),
        ("supervised", ["regression", "classification", "supervised"]),
        ("unsupervised", ["clustering", "anomaly detection", "unsupervised"]),
    ]
    matches = [(parent, sum(1 for w in keywords if w in haystack)) for parent, keywords in rules]
    parent, score = max(matches, key=lambda t: t[1])
    return {
        "suggested_parent": parent if score else "ml",
        "confidence": "low" if score <= 1 else "medium",
        "reason": "Keyword-based pilot classification; requires human review.",
    }


def compare(old: dict, pages: dict, warnings: list[str]) -> tuple[dict, list[dict], dict]:
    previous = old.get("pages", {})
    current = {key: safe_public_state(page) for key, page in pages.items()}
    first = old.get("last_successful_sync") is None
    changes = []
    for key, page in pages.items():
        prior = previous.get(key)
        change = ("baseline" if first else "added") if not prior else (
            "modified" if prior["fingerprint"] != page["fingerprint"] else None)
        if change:
            headings = page["headings"][:12]
            changes.append({
                "kind": change, "title": page["title"], "url": page["url"], "page_key": key,
                "headings": [h["title"] for h in headings],
                "suggestions": [
                    {"concept": h["title"], **classify(h["title"], page["text"])}
                    for h in headings
                ],
            })
    # An inaccessible or rate-limited page is never marked deleted.
    # Report missing pages as "potentially missing"; reconciliation requires a clean scan.
    if not first and not warnings:
        missing = set(previous) - set(current)
        for _ in missing:
            changes.append({"kind": "potentially_missing", "title": "Unverified missing page"})
    summary = {
        "generated_at_utc": now(), "baseline": first,
        "pages_scanned": len(pages), "added": sum(c["kind"] == "added" for c in changes),
        "modified": sum(c["kind"] == "modified" for c in changes),
        "potentially_missing": sum(c["kind"] == "potentially_missing" for c in changes),
        "suggestions": sum(len(c.get("suggestions", [])) for c in changes if c["kind"] != "baseline"),
        "warnings": list(dict.fromkeys(warnings)),
    }
    return {"version": 1, "pages": current, "last_successful_sync": summary["generated_at_utc"]}, changes, summary



def extract_semantic_changes(old: dict, new: dict, changes: list[dict],
                             pages: dict, summary: dict) -> dict:
    """Bounded extraction; defer excess pages by preserving old fingerprints."""
    summary.update(semantic_status="disabled", semantic_pages=0,
                   semantic_concepts=0, semantic_relations=0, semantic_deferred=0)
    if not os.getenv("OPENAI_API_KEY"):
        return {}
    if not all(os.getenv(k) for k in ("SMTP_HOST", "SMTP_USERNAME",
                                     "SMTP_PASSWORD", "REPORT_EMAIL_TO")):
        raise RuntimeError("LLM extraction requires configured private SMTP delivery")
    include_baseline = os.getenv("SEMANTIC_BACKFILL_BASELINE", "false").lower() == "true"
    eligible = [c for c in changes if c["kind"] in ("added", "modified")
                or (include_baseline and c["kind"] == "baseline")]
    eligible.sort(key=lambda c: c["page_key"])
    limit = int(os.getenv("SEMANTIC_MAX_PAGES_PER_RUN", "5"))
    if limit < 1:
        raise ValueError("SEMANTIC_MAX_PAGES_PER_RUN must be positive")
    selected, deferred = eligible[:limit], eligible[limit:]
    for item in deferred:
        key = item["page_key"]
        if key in old.get("pages", {}):
            new["pages"][key] = old["pages"][key]
        else:
            new["pages"].pop(key, None)
    summary["semantic_deferred"] = len(deferred)
    summary["semantic_status"] = "enabled"
    results = {}
    for entry in selected:
        proposal = semantic_extract.extract(pages[entry["page_key"]])
        results[entry["page_key"]] = proposal
        summary["semantic_pages"] += 1
        summary["semantic_concepts"] += len(proposal["concepts"])
        summary["semantic_relations"] += len(proposal["relations"])
    return results


def mail_report(changes: list[dict], summary: dict, semantic: dict | None = None) -> bool:
    required = ["SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "REPORT_EMAIL_TO"]
    if not all(os.getenv(k) for k in required):
        return False
    lines = ["AI & ML Knowledge Maintenance Digest", json.dumps(summary, indent=2), ""]
    for entry in changes[:100]:
        lines.extend([entry["kind"].upper() + " — " + entry["title"], entry.get("url", "")])
        for c in entry.get("suggestions", []):
            lines.append("  • " + c["concept"] + " → " + c["suggested_parent"] + " (" + c["confidence"] + ", review required)")
        lines.append("")
    if semantic:
        lines += ["", "=== LLM SEMANTIC PROPOSALS — REVIEW REQUIRED ==="]
        for entry in changes:
            proposal = semantic.get(entry.get("page_key"))
            if not proposal:
                continue
            lines += ["NOTE: " + entry["title"], entry.get("url", "")]
            for concept in proposal["concepts"]:
                lines.append("  CONCEPT: " + concept["name"] +
                             " → " + concept["parent_id"] +
                             " (" + concept["confidence"] + ")")
                lines.append("    " + concept["definition"])
                for evidence in concept["evidence"]:
                    lines.append("    Evidence block " + evidence["block_id"] +
                                 ": " + evidence["quote"])
            for relation in proposal["relations"]:
                lines.append("  RELATION: " + relation["source"] + " " +
                             relation["type"] + " " + relation["target"])
                for evidence in relation["evidence"]:
                    lines.append("    Evidence block " + evidence["block_id"] +
                                 ": " + evidence["quote"])
            lines.append("")
    msg = EmailMessage()
    msg["Subject"] = "AI & ML Knowledge Digest — " + dt.date.today().isoformat()
    msg["From"] = os.getenv("REPORT_EMAIL_FROM") or os.environ["SMTP_USERNAME"]
    msg["To"] = os.environ["REPORT_EMAIL_TO"]
    msg.set_content("\n".join(lines))
    host = os.environ["SMTP_HOST"]
    port = int(os.getenv("SMTP_PORT") or "465")
    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=30) as smtp:
            smtp.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"])
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"])
            smtp.send_message(msg)
    return True


def write_github_summary(summary: dict, emailed: bool) -> None:
    # GitHub Actions logs and summaries may be public: only publish aggregate counts.
    lines = [
        "## AI & ML daily knowledge maintenance",
        "| Item | Count |", "|---|---:|",
        f'| Pages scanned | {summary["pages_scanned"]} |',
        f'| Added | {summary["added"]} |',
        f'| Modified | {summary["modified"]} |',
        f'| Potentially missing | {summary["potentially_missing"]} |',
        f'| Concept suggestions for review | {summary["suggestions"]} |',
        f'| Private email delivery | {"sent" if emailed else "not configured"} |',
    ]
    target = os.getenv("GITHUB_STEP_SUMMARY")
    if target:
        with open(target, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    print("; ".join(x.strip("| ") for x in lines[3:]))


def main() -> None:
    if not NOTION_TOKEN:
        raise SystemExit("NOTION_TOKEN is required; see doc/operations.md")
    old = load_manifest()
    pages, warnings = collect_pages()
    if not pages:
        raise SystemExit("No pages found: refusing to replace the prior state")
    new, changes, summary = compare(old, pages, warnings)
    if warnings:
        # Keep the old state when the scan is incomplete: no false deletions or resets.
        raise SystemExit("Incomplete Notion scan: manifest unchanged; " + "; ".join(warnings))
    # Do not transmit private content to the model or email in DRY_RUN.
    semantic = {} if DRY_RUN else extract_semantic_changes(old, new, changes, pages, summary)
    if not DRY_RUN:
        # Deliver private review proposals before advancing the manifest.
        emailed = mail_report(changes, summary, semantic)
        STATE.parent.mkdir(exist_ok=True, parents=True)
        STATE.write_text(json.dumps(new, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        emailed = False
    write_github_summary(summary, emailed)


if __name__ == "__main__":
    main()
