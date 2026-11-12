"""Offline checks for evidence validation; no LLM requests or Notion access."""
import unittest
import semantic_extract as se

BLOCKS = [
    {"block_id": "block-1", "type": "paragraph", "text": "LoRA is a parameter-efficient fine-tuning method."},
    {"block_id": "block-2", "type": "paragraph", "text": "LoRA can be used for supervised fine-tuning of language models."},
]

def item(name="LoRA", evidence=None):
    return {
        "name": name,
        "definition": "Low-rank adaptation for efficient finetuning.",
        "parent_id": "posttrain",
        "synonyms": [],
        "confidence": "medium",
        "evidence": evidence if evidence is not None else [{"block_id": "block-1", "quote": "parameter-efficient fine-tuning"}],
    }

def relation(source="LoRA", target="Fine-Tuning", evidence=None):
    return {
        "source": source, "target": target, "type": "IS_A",
        "confidence": "medium",
        "evidence": evidence if evidence is not None else [
            {"block_id": "block-1", "quote": "parameter-efficient fine-tuning"}
        ],
    }

class ExtractionValidationTests(unittest.TestCase):
    def test_valid_concept_carries_verified_evidence(self):
        result = se.validate_proposals({"concepts": [item()], "relations": []}, BLOCKS)
        self.assertEqual(len(result["concepts"]), 1)
        self.assertEqual(result["concepts"][0]["evidence"][0]["block_id"], "block-1")
        self.assertEqual(result["concepts"][0]["review_status"], "proposed")

    def test_rejects_fabricated_quote(self):
        fake = [{"block_id": "block-1", "quote": "This was not in the note"}]
        result = se.validate_proposals({"concepts": [item(evidence=fake)], "relations": []}, BLOCKS)
        self.assertEqual(result["concepts"], [])

    def test_rejects_fabricated_block_id(self):
        fake = [{"block_id": "missing", "quote": "parameter-efficient fine-tuning"}]
        result = se.validate_proposals({"concepts": [item(evidence=fake)], "relations": []}, BLOCKS)
        self.assertEqual(result["concepts"], [])

    def test_rejects_missing_relation_endpoint(self):
        result = se.validate_proposals(
            {"concepts": [item()], "relations": [relation()]}, BLOCKS
        )
        self.assertEqual(result["relations"], [])

    def test_accepts_evidence_backed_relation(self):
        result = se.validate_proposals(
            {"concepts": [item(), item("Fine-Tuning", [
                {"block_id": "block-2", "quote": "supervised fine-tuning"}
            ])], "relations": [relation()]}, BLOCKS
        )
        self.assertEqual(len(result["relations"]), 1)

    def test_deduplicates_same_concept(self):
        result = se.validate_proposals({"concepts": [item(), item("lora")], "relations": []}, BLOCKS)
        self.assertEqual(len(result["concepts"]), 1)

    def test_input_budget_keeps_source_ids(self):
        data = se.chosen_blocks({"evidence_blocks": [{"id":"block-1", "kind":"paragraph", "content":"LoRA is a technique."}]})
        self.assertEqual(data[0]["block_id"], "block-1")
        self.assertEqual(data[0]["text"], "LoRA is a technique.")

    def test_schema_strict_objects(self):
        s=se.schema()
        self.assertFalse(s["additionalProperties"])
        self.assertEqual(s["required"], ["concepts", "relations"])
        self.assertFalse(s["properties"]["concepts"]["items"]["additionalProperties"])

if __name__ == "__main__":
    unittest.main()
