"""Pure, offline unit tests for maintenance logic (no Notion token needed)."""
import importlib.util
from pathlib import Path
import unittest
spec = importlib.util.spec_from_file_location("maintain", Path(__file__).resolve().parent / "maintain.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class MaintenanceTests(unittest.TestCase):
    def test_classification(self):
        self.assertEqual(m.classify("LoRA parameter efficient fine tuning", "")["suggested_parent"], "posttrain")
        self.assertEqual(m.classify("PPO and policy gradient", "")["suggested_parent"], "rl")
    def test_baseline_no_change_count(self):
        page = {"id": "abc", "title": "Test", "fingerprint": "hash", "edited": "2026-11-12",
                "headings": [{"title": "LoRA"}], "text": "lora", "url": "https://www.notion.so/test"}
        k = m.page_key(page["id"])
        new, changes, summary = m.compare({"version":1,"pages":{}, "last_successful_sync":None}, {k:page}, [])
        self.assertTrue(summary["baseline"])
        self.assertEqual(summary["added"], 0)
        self.assertEqual(changes[0]["kind"], "baseline")
        again, new_changes, counts = m.compare(new,{k:page}, [])
        self.assertEqual(new_changes, [])
        self.assertEqual(counts["modified"], 0)
    def test_changed_page(self):
        base = {"id":"abc","title":"T","fingerprint":"after","edited":"now","headings":[{"title":"QLoRA"}],"text":"qlora","url":"https://www.notion.so/test"}
        k=m.page_key("abc")
        _, changes, counts = m.compare({"version":1,"pages":{k:{"fingerprint":"before","edited":"then"}},"last_successful_sync":"then"},{k:base},[])
        self.assertEqual(counts["modified"],1)
        self.assertEqual(changes[0]["suggestions"][0]["suggested_parent"],"posttrain")
    def test_manifest_hides_content(self):
        page = {"fingerprint": "a", "edited": "now", "text": "confidential"}
        self.assertEqual(m.safe_public_state(page),{"fingerprint":"a","edited":"now"})

if __name__ == "__main__":
    unittest.main()
