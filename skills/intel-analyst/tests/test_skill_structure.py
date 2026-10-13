"""Structural tests for the intel-analyst skill.

They check that every file the skill loads exists, that files link to each
other correctly, and that the fixed content the spec defines is present.
Run with: python3 -m unittest discover -s skills/intel-analyst/tests -v
"""
import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent

SCALE = [
    ("almost no chance", "1–5%"),
    ("very unlikely", "5–20%"),
    ("unlikely", "20–45%"),
    ("roughly even chance", "45–55%"),
    ("likely", "55–80%"),
    ("very likely", "80–95%"),
    ("almost certain", "95–99%"),
]
BANNED = ["may", "could", "possibly", "might", "perhaps"]


def read(rel_path):
    return (SKILL_DIR / rel_path).read_text(encoding="utf-8")


class AnalyticStandardsTest(unittest.TestCase):
    def setUp(self):
        self.text = read("references/analytic-standards.md")

    def test_scale_rows_are_exact(self):
        for term, rng in SCALE:
            self.assertRegex(self.text, rf"\|\s*{re.escape(term)}\s*\|\s*{re.escape(rng)}\s*\|")

    def test_confidence_levels_defined(self):
        for level in ("low", "moderate", "high"):
            self.assertRegex(self.text, rf"\*\*{level}\*\*", level)

    def test_banned_words_listed(self):
        for word in BANNED:
            self.assertIn(f'"{word}"', self.text)

    def test_nine_standards_checklist(self):
        self.assertEqual(len(re.findall(r"^- \[ \] ", self.text, re.M)), 9)


class SourcingTest(unittest.TestCase):
    def setUp(self):
        self.text = read("references/sourcing.md")

    def test_reliability_grades(self):
        for g in "ABCDEF":
            self.assertRegex(self.text, re.compile(rf"^\|\s*{g}\s*\|", re.M))

    def test_credibility_grades(self):
        for n in range(1, 7):
            self.assertRegex(self.text, re.compile(rf"^\|\s*{n}\s*\|", re.M))

    def test_low_confidence_cap_rule(self):
        self.assertIn("capped at **low**", self.text)

    def test_high_confidence_rule(self):
        self.assertIn("two independent sources", self.text)


class TechniquesTest(unittest.TestCase):
    def setUp(self):
        self.text = read("references/techniques.md")

    def test_all_techniques_have_sections(self):
        for name in ("Analysis of Competing Hypotheses", "Key Assumptions Check",
                     "Indicators / Signposts", "High-Impact / Low-Probability",
                     "What If? Analysis", "Red Team"):
            self.assertRegex(self.text, re.compile(rf"^## {re.escape(name)}", re.M))

    def test_red_team_delegates_to_devils_advocate(self):
        self.assertIn("codered:devils-advocate", self.text)

    def test_ach_seeks_disconfirmation(self):
        self.assertIn("inconsistent", self.text.lower())
        self.assertIn("disconfirm", self.text.lower())

    def test_mode_table_present(self):
        self.assertRegex(self.text, r"\|\s*Technique\s*\|\s*Quick mode\s*\|\s*Rigorous mode\s*\|")


class TailoringTest(unittest.TestCase):
    def setUp(self):
        self.text = read("references/tailoring.md")

    def test_profiles(self):
        for profile in ("leadership", "engineers", "self"):
            self.assertIn(f"`{profile}`", self.text)

    def test_no_new_judgments_rule(self):
        self.assertIn("never add a judgment", self.text)

    def test_links_back_rule(self):
        self.assertIn("links to the full product", self.text)


if __name__ == "__main__":
    unittest.main()
