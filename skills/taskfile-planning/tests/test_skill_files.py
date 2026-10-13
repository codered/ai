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


class SkillDocTest(unittest.TestCase):
    def setUp(self):
        self.text = read("SKILL.md")

    def test_frontmatter(self):
        self.assertTrue(self.text.startswith("---\nname: taskfile-planning\ndescription: "))
        for trigger in ("write a taskfile", "plan this as a Taskfile.ste",
                        "taskfile-planning", "run Taskfile.ste"):
            self.assertIn(trigger, self.text.split("---")[1], trigger)

    def test_length(self):
        self.assertLessEqual(len(self.text.splitlines()), 260)

    def test_every_linked_file_exists(self):
        links = set(re.findall(r"`(references/[\w.-]+)`", self.text))
        self.assertEqual(links, {"references/format.md", "references/ste_lint.py",
                                 "references/example.ste"})
        for rel in links:
            self.assertTrue(os.path.isfile(os.path.join(SKILL_DIR, rel)), rel)

    def test_mode_1_stops_at_the_question(self):
        self.assertIn('"Run this plan now, or later?"', self.text)
        self.assertIn("Never start it on your own.", self.text)

    def test_names_match_the_linter(self):
        model, errors = ste_lint.lint(read("references/example.ste"))
        self.assertEqual(errors, [])
        data = ste_lint.to_json(model)
        self.assertEqual(data["plan"]["integration_branch"], "taskfile/health-check/integration")
        for name in ("taskfile/<plan>/integration", "<WORKTREES>/<plan>/integration",
                     "taskfile/<plan>/tasks/<id>", "<WORKTREES>/<plan>/tasks/<id>"):
            self.assertIn(f"`{name}`", self.text, name)

    def test_flow_contract(self):
        contract = self.text.split("### FLOW contract")[1].split("\n## ")[0]
        for phrase in ("Work only in your worktree", "Do not merge, rebase, or push",
                       "Omit only the steps your SKIP lines name", "Use only the TOOL",
                       "Stay inside PERMIT, DENY, and FILES", "Do not start agents",
                       "Do not edit the Taskfile", "Send a heartbeat",
                       "End with `report`, including on failure",
                       "completed_failure BECAUSE context limit"):
            self.assertIn(phrase, contract, phrase)

    def test_audit_steps_in_order(self):
        audit = self.text.split("### Audit and merge")[1].split("###")[0]
        steps = re.findall(r"^\d\. \*\*(.+?)\*\*", audit, re.M)
        self.assertEqual(steps, ["Save everything.", "Attribute.", "Verify in isolation.",
                                 "Merge.", "Verify after the merge.", "Clean up."])

    def test_failure_reasons_pass_the_linter(self):
        reasons = set(re.findall(r"`[^`\n]*BECAUSE ([A-Za-z ]+)`", self.text))
        self.assertEqual(reasons, {"changed files outside FILES", "merge conflict",
                                   "VERIFY failed after merge", "context limit"})
        for reason in reasons:
            self.assertEqual(ste_lint.ste_problems(reason), [], reason)


if __name__ == "__main__":
    unittest.main()
