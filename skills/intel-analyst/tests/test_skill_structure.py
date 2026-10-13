"""Structural tests for the intel-analyst skill.

They check that every file the skill loads exists, that files link to each
other correctly, and that the fixed content the spec defines is present.
Run with: python3 -m unittest discover -s skills/intel-analyst/tests -v
"""
import re
import subprocess
import tempfile
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


def flat(rel_path):
    """File text with every run of whitespace collapsed to one space, so
    phrase checks do not depend on where lines wrap."""
    return " ".join(read(rel_path).split())


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

    def test_bluf_rules(self):
        self.assertIn("The BLUF contains no judgment of its own", self.text)
        self.assertIn("Risk-level adjectives", self.text)
        self.assertIn('Do not add an estimated percentage', self.text)

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

    def test_conflict_and_support_rules(self):
        self.assertIn('"Neither was weighted heavily" does not meet this rule', self.text)
        self.assertIn("never as the only support", self.text)

    def test_conflict_rule_lands_in_key_judgment(self):
        self.assertIn("Put this sentence in the Key Judgment", flat("references/sourcing.md"))

    def test_derived_items_rule(self):
        self.assertIn("`derived from E1, E3`", self.text)
        self.assertIn("Not an Evidence Log item", self.text)


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

    def test_ach_keeps_conflicting_rows(self):
        self.assertIn("when two sources conflict, keep both rows", flat("references/techniques.md"))

    def test_ach_survival_and_weight_rules(self):
        text = flat("references/techniques.md")
        self.assertIn("Survival test.", text)
        self.assertIn("Weights must match the words.", text)
        self.assertIn("the Recommendation must say the choice is provisional", text)

    def test_every_mode_keeps_template_headings(self):
        self.assertIn("Not run (quick mode).", flat("references/techniques.md"))
        self.assertIn("Not run (quick mode).", flat("SKILL.md"))

    def test_investigation_indicators_have_a_home(self):
        self.assertIn('Type "Detective"', flat("references/techniques.md"))
        self.assertIn("Detective", read("templates/investigation-package.md"))

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


HEADER_FIELDS = ["Product:", "Mode:", "Date:", "Analyst:", "Key Question:",
                 "Readers:", "Decision needed by:", "BLUF:"]
TAIL_SECTIONS = ["Evidence Log", "Key Assumptions",
                 "Alternative Views / Red Team", "Intelligence Gaps"]
TEMPLATE_SECTIONS = {
    "decision-brief": ["Key Judgments", "Options", "ACH Matrix",
                       "Recommendation", "Signposts"],
    "investigation-package": ["Synopsis", "Chronology", "Findings of Fact",
                              "Analysis", "Conclusions",
                              "Investigator's Comments", "Recommended Actions"],
    "risk-assessment": ["Key Judgments", "Threat/Risk Register", "Scenarios",
                        "Indicators & Warnings", "Mitigations"],
}


class TemplatesTest(unittest.TestCase):
    def test_full_templates(self):
        for name, sections in TEMPLATE_SECTIONS.items():
            text = read(f"templates/{name}.md")
            for field in HEADER_FIELDS:
                self.assertIn(field, text, f"{name}: {field}")
            headings = re.findall(r"^## (?:\d+\. )?(.+)$", text, re.M)
            self.assertEqual(headings, sections + TAIL_SECTIONS, name)

    def test_evidence_log_columns(self):
        for name in TEMPLATE_SECTIONS:
            self.assertRegex(read(f"templates/{name}.md"),
                             r"\|\s*ID\s*\|\s*Item\s*\|\s*Source\s*\|\s*Grade\s*\|")

    def test_risk_bluf_forbids_risk_levels(self):
        text = read("templates/risk-assessment.md")
        self.assertNotIn("overall risk level", text)
        self.assertIn("No risk-level adjectives", text)

    def test_bluf_one_pager(self):
        text = read("templates/bluf-one-pager.md")
        self.assertNotIn("Evidence Log", text)
        self.assertIn("Full product:", text)
        self.assertIn("BLUF:", text)


class FixtureTest(unittest.TestCase):
    """The investigation scenario fixture builds a repo with the planted bug."""

    def test_builds_repo_with_planted_bug(self):
        script = SKILL_DIR / "tests" / "fixtures" / "make_incident_repo.sh"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "checkout"
            subprocess.run(["bash", str(script), str(repo)], check=True,
                           capture_output=True)
            log = subprocess.run(["git", "-C", str(repo), "log", "--oneline"],
                                 check=True, capture_output=True, text=True)
            self.assertEqual(len(log.stdout.splitlines()), 4)
            payments = (repo / "checkout" / "payments.py").read_text()
            self.assertIn("timeout_ms=RETRY_TIMEOUT", payments)
            config = (repo / "checkout" / "config.py").read_text()
            self.assertIn("RETRY_TIMEOUT = 30  # seconds", config)
            self.assertIn("dns: slow resolution", (repo / "logs" / "app.log").read_text())

    def test_refuses_non_empty_dir(self):
        script = SKILL_DIR / "tests" / "fixtures" / "make_incident_repo.sh"
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "keep.txt").write_text("x")
            result = subprocess.run(["bash", str(script), tmp],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("is not empty", result.stderr)


class SkillFileTest(unittest.TestCase):
    def setUp(self):
        self.text = read("SKILL.md")

    def test_frontmatter(self):
        self.assertTrue(self.text.startswith("---\nname: intel-analyst\n"))
        self.assertRegex(self.text, r"\ndescription: ")

    def test_length(self):
        n = len(self.text.splitlines())
        self.assertTrue(150 <= n <= 250, n)

    def test_red_team_runs_last(self):
        text = flat("SKILL.md")
        self.assertLess(text.index("Run the other techniques"), text.index("**Red Team** — last"))

    def test_never_overwrite(self):
        self.assertIn("Never overwrite a file.", flat("SKILL.md"))

    def test_every_linked_file_exists(self):
        links = set(re.findall(r"`((?:references|templates)/[\w-]+\.md)`", self.text))
        self.assertEqual(len(links), 8)
        for rel in links:
            self.assertTrue((SKILL_DIR / rel).is_file(), rel)

    def test_integrations_and_fallbacks(self):
        for s in ("codered:devils-advocate", "codered:nfc", "codered:mission-grade", "fallback"):
            self.assertIn(s, self.text)

    def test_code_review_and_refactor_use_mission_grade(self):
        text = flat("SKILL.md")
        self.assertIn("When collection reviews code", text)
        self.assertIn("refactors or fixes code", text)

    def test_output_rules(self):
        self.assertIn("docs/intel/YYYY-MM-DD-<slug>.md", self.text)
        self.assertIn("not inside a git repository", self.text)

    def test_checkpoint_is_a_stop(self):
        self.assertRegex(self.text, r"(?i)checkpoint.*\n(?:.*\n){0,6}.*\bSTOP\b")


if __name__ == "__main__":
    unittest.main()
