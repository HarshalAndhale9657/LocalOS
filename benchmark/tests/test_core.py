"""Cross-language behaviour tests: the same vectors are run by extension/lib/model/core.test.ts."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pmrgb import core  # noqa: E402

VECTORS = os.path.join(core.SHARED_DIR, "tests", "refusal_cases.json")


class SharedVectors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(VECTORS, encoding="utf-8") as f:
            cls.v = json.load(f)

    def test_refusal(self):
        for c in self.v["refusal"]:
            with self.subTest(text=c["text"]):
                self.assertEqual(core.is_refusal(c["text"]), c["is_refusal"])

    def test_citations(self):
        for c in self.v["citations"]:
            with self.subTest(text=c["text"]):
                self.assertEqual(core.cited_indices(c["text"]), c["cited"])

    def test_prompt_renders_refusal_and_sources(self):
        sysm = core.qa_system_prompt()
        self.assertIn(core.REFUSAL, sysm)
        self.assertNotIn("{refusal}", sysm)
        user = core.qa_user_prompt("What is X?", [
            {"title": "T1", "read_at": "2026-07-14T09:12:00Z", "text": "alpha"},
            {"url": "https://u", "read_at": "2026-07-15", "text": "beta"},
        ])
        self.assertIn("[1] (T1, read 2026-07-14)", user)
        self.assertIn("[2] (https://u, read 2026-07-15)", user)
        self.assertIn("<<UNTRUSTED_CONTENT>>\nalpha\n<<END_UNTRUSTED_CONTENT>>", user)
        self.assertTrue(user.startswith("Question: What is X?"))

    def test_parse_answer_filters_out_of_range(self):
        r = core.parse_answer("Yes [1] and [9].", n_sources=2)
        self.assertEqual(r["decision"], "answer")
        self.assertEqual(r["cited"], [1])
        self.assertEqual(core.parse_answer("Not found in your history", 2)["decision"], "abstain")


if __name__ == "__main__":
    unittest.main()
