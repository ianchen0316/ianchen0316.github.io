"""Offline tests for safe Notion Node Registry synchronization."""
import unittest
import sync_node_registry as r


def row(id="token", label="Tokenization", summary="Old", breakdown="Priority"):
    def text(v):return {"type":"rich_text","rich_text":[{"plain_text":v}]}
    return {"id":"row-"+id,"properties":{
        "Node ID":text(id),
        "Name":{"type":"title","title":[{"plain_text":label}]},
        "Parent ID":text("llm-found"),
        "Summary":text(summary),
        "Node Type":{"type":"select","select":{"name":"Concept"}},
        "Domain":{"type":"select","select":{"name":"AI & ML"}},
        "Breakdown":{"type":"select","select":{"name":breakdown}},
        "Tags":{"type":"multi_select","multi_select":[{"name":"LLM"}]},
        "Source Pages":text("https://www.notion.so/a\nhttps://www.notion.so/b"),
    }}


class RegistryTests(unittest.TestCase):
    def test_multi_source_links_are_unique(self):
        node={"id":"x","label":"Concept","type":"concept",
              "url":"https://www.notion.so/a",
              "source_pages":[{"url":"https://www.notion.so/a"},{"url":"https://www.notion.so/b"}]}
        self.assertEqual(len(r.source_links(node)), 2)
        p=r.initial_fields(node)
        self.assertEqual(p["Source Count"]["number"],2)
        self.assertIn("https://www.notion.so/b",p["Source Pages"]["rich_text"][0]["text"]["content"])

    def test_preserves_tags_and_breakdown(self):
        n={"id":"token","label":"Tokenization","type":"concept","parent":"llm-found",
           "description":"Transforms text to token IDs."}
        creates,updates=r.plan_changes([n],[row()])
        self.assertEqual(creates,[])
        self.assertEqual(len(updates),1)
        patch=updates[0][1]
        self.assertIn("Summary",patch)
        self.assertNotIn("Breakdown",patch)
        self.assertNotIn("Tags",patch)
        self.assertNotIn("Source Pages",patch)

    def test_repeat_has_no_changes(self):
        n={"id":"token","label":"Tokenization","type":"concept","parent":"llm-found",
           "description":"Old"}
        a,b=r.plan_changes([n],[row()])
        self.assertEqual(a,[])
        self.assertEqual(b,[])

    def test_creates_missing_node_only(self):
        n={"id":"new","label":"LoRA","type":"concept","parent":"posttrain",
           "description":"Low-rank adaptation.","url":"https://www.notion.so/x"}
        creates,updates=r.plan_changes([n],[row()])
        self.assertEqual(len(creates),1)
        self.assertEqual(updates,[])
        self.assertEqual(creates[0]["Breakdown"]["select"]["name"],"Not assessed")

    def test_duplicate_registry_id_rejected(self):
        with self.assertRaises(ValueError):
            r.plan_changes([], [row(),row()])

    def test_duplicate_graph_id_rejected(self):
        with self.assertRaises(ValueError):
            r.plan_changes([{"id":"x","label":"X","type":"topic"},
                            {"id":"x","label":"X","type":"topic"}],[])


if __name__=="__main__":
    unittest.main()
