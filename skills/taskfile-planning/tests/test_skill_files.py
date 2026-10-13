"""Structural tests for SKILL.md and references/format.md.

They check that the documents name every file, keyword, error code, and branch
name that the linter defines, so the documents and the linter cannot drift apart.
Run with: python3 -m unittest discover -s skills/taskfile-planning/tests -v
"""
import os
import re
import sys
import unittest

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(SKILL_DIR, "references"))
import ste_lint  # noqa: E402


def read(rel_path):
    with open(os.path.join(SKILL_DIR, rel_path), encoding="utf-8") as handle:
        return handle.read()


class FormatDocTest(unittest.TestCase):
    def setUp(self):
        self.text = read("references/format.md")

    def test_every_keyword_is_documented(self):
        for keyword in ste_lint.KEYWORDS:
            self.assertRegex(self.text, r"`" + keyword + r"\b", keyword)

    def test_every_code_has_its_row(self):
        for code, meaning in ste_lint.CODES.items():
            row = f"| {code} | {meaning[0].upper() + meaning[1:]} |"
            self.assertIn(row, self.text.replace("`${id.key}`", "${id.key}"), code)

    def test_no_unknown_codes(self):
        documented = set(re.findall(r"^\| ([SGPFTX]\d{3}) \|", self.text, re.M))
        self.assertEqual(documented, set(ste_lint.CODES))

    def test_links_the_example(self):
        self.assertIn("`example.ste`", self.text)
        self.assertTrue(os.path.isfile(os.path.join(SKILL_DIR, "references", "example.ste")))


if __name__ == "__main__":
    unittest.main()
