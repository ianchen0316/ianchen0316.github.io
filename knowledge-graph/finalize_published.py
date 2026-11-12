#!/usr/bin/env python3
"""Mark successfully committed/pushed review rows as Published."""
from __future__ import annotations
import os
import review_queue

if __name__ == "__main__":
    applied = [item for item in os.getenv("APPLIED_REVIEW_IDS", "").split(",") if item]
    if applied:
        review_queue.mark_published(applied)
        print("Finalized", len(applied), "Notion review decisions.")
    else:
        print("No review status updates needed.")
