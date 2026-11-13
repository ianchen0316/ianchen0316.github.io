"""Ensure two Notion roots feed one semantic taxonomy without duplication."""
import unittest
import maintain
import semantic_extract

class WorkspaceTaxonomyTests(unittest.TestCase):
    def test_both_notions_are_registered_under_ml(self):
        self.assertEqual(maintain.SOURCE_ROOTS["machine-learning"]["domain_id"], "ml")
        self.assertEqual(maintain.SOURCE_ROOTS["llm-finetuning"]["domain_id"], "ml")
        self.assertNotEqual(maintain.ROOTS["machine-learning"], maintain.ROOTS["llm-finetuning"])

    def test_llm_topics_stay_reusable_for_all_sources(self):
        for node in ("llm", "llm-found", "posttrain"):
            self.assertIn(node, semantic_extract.PARENT_IDS)

    def test_root_registry_has_unique_page_ids(self):
        self.assertEqual(len(maintain.ROOTS), len(set(maintain.ROOTS.values())))

if __name__ == "__main__":
    unittest.main()
