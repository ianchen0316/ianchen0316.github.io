"""Pure offline tests for private queue decisions and safe graph publication."""
import copy
import unittest
from unittest.mock import patch
import review_queue as q


def field(value):
    return {"type": "rich_text", "rich_text": [{"plain_text": value}]}


def row(status="Approved", kind="Concept", title="LoRA", key="a"*40,
        parent="posttrain", definition="Low-rank adaptation", url="https://www.notion.so/source",
        source="", target="", relation="RELATED_TO", merge_into="", row_id="row-1"):
    return {
        "id": row_id,
        "properties": {
            "Name": {"type": "title", "title": [{"plain_text": title}]},
            "Status": {"type": "select", "select": {"name": status}},
            "Kind": {"type": "select", "select": {"name": kind}},
            "Candidate Key": field(key),
            "Parent": field(parent), "Definition": field(definition),
            "Source URL": {"type": "url", "url": url},
            "Relation Source": field(source), "Relation Target": field(target),
            "Relation Type": field(relation), "Merge Into": field(merge_into),
        }
    }


def graph():
    return {"metadata": {}, "nodes": [
        {"id": "ml", "label": "Machine Learning", "type": "domain"},
        {"id": "posttrain", "label": "Post-Training", "type": "topic"},
        {"id": "sft", "label": "Supervised Fine-Tuning", "type": "concept", "source_pages": []}
    ], "edges": []}


class ReviewQueueTests(unittest.TestCase):
    def test_candidate_keys_are_deterministic_and_versioned(self):
        a = q.candidate_key("page", "hashA", "Concept", "LoRA")
        self.assertEqual(a, q.candidate_key("page", "hashA", "Concept", "lora"))
        self.assertNotEqual(a, q.candidate_key("page", "hashB", "Concept", "LoRA"))

    def test_approved_concept_is_published_without_private_evidence(self):
        g, counts, ids, warnings = q.apply_reviews(graph(), [row()])
        self.assertEqual(counts["concepts"], 1)
        self.assertEqual(ids, ["row-1"])
        published = next(n for n in g["nodes"] if n["label"] == "LoRA")
        self.assertEqual(published["review_status"], "approved")
        self.assertNotIn("evidence", published)
        self.assertEqual(published["parent"], "posttrain")

    def test_repeated_publication_is_idempotent(self):
        g, _, _, _ = q.apply_reviews(graph(), [row()])
        g2, counts, ids, warnings = q.apply_reviews(g, [row()])
        self.assertEqual(counts["concepts"], 0)
        self.assertEqual(len([n for n in g2["nodes"] if n["label"] == "LoRA"]), 1)
        self.assertEqual(ids, ["row-1"])

    def test_rejected_and_proposed_do_not_publish(self):
        g, counts, ids, warnings = q.apply_reviews(graph(), [
            row(status="Rejected"), row(status="Proposed", row_id="row-2")
        ])
        self.assertEqual(counts["concepts"], 0)
        self.assertFalse(ids)
        self.assertEqual(len(g["nodes"]), 3)

    def test_duplicate_name_requires_merge(self):
        g, counts, ids, warnings = q.apply_reviews(graph(), [
            row(title="Supervised Fine-Tuning")
        ])
        self.assertEqual(counts["concepts"], 0)
        self.assertFalse(ids)
        self.assertTrue(warnings)

    def test_merge_adds_source_without_duplicate_node(self):
        r = row(status="Merge", merge_into="sft", title="SFT")
        g, counts, ids, warnings = q.apply_reviews(graph(), [r])
        self.assertEqual(counts["merges"], 1)
        self.assertEqual(len(g["nodes"]), 3)
        self.assertEqual(len(next(n for n in g["nodes"] if n["id"] == "sft")["source_pages"]), 1)
        g, _, ids, _ = q.apply_reviews(g, [r])
        self.assertEqual(len(next(n for n in g["nodes"] if n["id"] == "sft")["source_pages"]), 1)

    def test_unknown_merge_target_is_skipped(self):
        g, counts, ids, warnings = q.apply_reviews(graph(), [
            row(status="Merge", merge_into="does-not-exist")
        ])
        self.assertFalse(ids)
        self.assertTrue(warnings)

    def test_approved_relation_must_resolve_both_endpoints(self):
        valid = row(kind="Relation", title="Relation", source="sft",
                    target="posttrain", relation="RELATED_TO")
        g, counts, ids, warnings = q.apply_reviews(graph(), [valid])
        self.assertEqual(counts["relations"], 1)
        self.assertEqual(g["edges"][0]["review_status"], "approved")
        invalid = row(kind="Relation", source="unknown", target="sft",
                      row_id="row-2")
        g, counts, ids, warnings = q.apply_reviews(g, [invalid])
        self.assertEqual(counts["relations"], 0)
        self.assertFalse(ids)
        self.assertTrue(warnings)

    def test_invalid_candidate_key_is_skipped(self):
        g, counts, ids, warnings = q.apply_reviews(graph(), [
            row(key="bad-key")
        ])
        self.assertFalse(ids)
        self.assertTrue(warnings)

    def test_enqueue_skips_existing_candidate_preserving_decision(self):
        page = {"id":"p","fingerprint":"f","url":"https://www.notion.so/p"}
        key = q.candidate_key("p","f","Concept","LoRA")
        old = row(status="Rejected", key=key)
        proposals = {"p": {"model":"test","concepts":[
            {"name":"LoRA","definition":"Low-rank adaptation","parent_id":"posttrain",
             "confidence":"medium","evidence": []}], "relations":[]}}
        with patch.object(q, "request") as make:
            counts = q.enqueue(proposals, {"p":page}, existing=[old])
        make.assert_not_called()
        self.assertEqual(counts["duplicates"],1)

if __name__ == "__main__":
    unittest.main()
