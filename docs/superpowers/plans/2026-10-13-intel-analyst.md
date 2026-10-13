# Intel Analyst Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the `intel-analyst` skill: one router `SKILL.md`, four reference files, four templates, a structural test suite, and recorded RED/GREEN scenario results.

**Architecture:** A progressive-disclosure skill. `SKILL.md` classifies product and mode, runs the six-step intelligence cycle, and loads only the reference and template files the run needs. A Python `unittest` suite checks that the files exist, link to each other, and contain the fixed content the spec defines (probability scale, grades, template sections). Behavior is verified by subagent scenario runs, judged by a sonnet subagent against the spec's pass criteria.

**Tech Stack:** Markdown, Python 3 standard library (`unittest`, `re`, `pathlib`), bash for the incident fixture.

**Spec:** `docs/superpowers/specs/2026-10-13-intel-analyst-design.md`

## Global Constraints

- Skill name `intel-analyst`; location `skills/intel-analyst/`.
- `SKILL.md` length: 150–250 lines inclusive.
- Probability terms, exactly seven: almost no chance (1–5%), very unlikely (5–20%), unlikely (20–45%), roughly even chance (45–55%), likely (55–80%), very likely (80–95%), almost certain (95–99%).
- Confidence: low, moderate, high — stated separately from probability.
- Banned in Key Judgments, Conclusions, BLUF: "may", "could", "possibly", "might", "perhaps".
- Source reliability A–F; information credibility 1–6.
- Output path: `docs/intel/YYYY-MM-DD-<slug>.md`; tailored: `docs/intel/YYYY-MM-DD-<slug>-<profile>.md`.
- Red Team in rigorous mode invokes `codered:devils-advocate`; prose passes through `codered:nfc`. Both have inline fallbacks.
- No classification markings; no agency imitation.
- Tests follow repo style: `python3 -m unittest discover -s skills/intel-analyst/tests -v`.

## Review Focus

1. **User says "just answer quickly" on a rigorous-class question** — the skill still applies rigorous mode (or states why it downgraded with user consent), never silently drops the checkpoint. Pinned by Task 5 pressure scenario P1.
2. **All evidence is weak (D–F)** — confidence capped at *low* and stated in the BLUF. Pinned by Task 5 pressure scenario P3 and by a Task 1 test that the cap rule is present in `sourcing.md`.
3. **Contradictory evidence** — both sources logged, conflict shown in ACH, weighting explained. Pinned by Task 5 pressure scenario P2.
4. **Not in a git repo / `docs/intel/` missing** — skill asks for a path or creates the dir. Pinned by a Task 5 test that `SKILL.md` contains both rules.
5. **Tailored version adds a judgment not in the full product** — forbidden. Pinned by a Task 2 test on `tailoring.md` and by the Task 5 GREEN criterion.

---

### Task 1: Analytic standards and sourcing references

**Files:**
- Create: `skills/intel-analyst/tests/test_skill_structure.py`
- Create: `skills/intel-analyst/references/analytic-standards.md`
- Create: `skills/intel-analyst/references/sourcing.md`

**Interfaces:**
- Produces: `test_skill_structure.py` with helper `read(rel_path) -> str` and constant `SKILL_DIR`; later tasks append test classes to this file.

- [ ] **Step 1: Write the failing tests**

```python
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
            self.assertRegex(self.text, rf"^\|\s*{g}\s*\|", re.M)

    def test_credibility_grades(self):
        for n in range(1, 7):
            self.assertRegex(self.text, rf"^\|\s*{n}\s*\|", re.M)

    def test_low_confidence_cap_rule(self):
        self.assertIn("capped at **low**", self.text)

    def test_high_confidence_rule(self):
        self.assertIn("two independent sources", self.text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s skills/intel-analyst/tests -v`
Expected: errors `FileNotFoundError` for `analytic-standards.md` and `sourcing.md`.

- [ ] **Step 3: Write `references/analytic-standards.md`**

Required content (spec §Reference files): purpose line; a nine-item `- [ ] ` checklist, one per ICD 203 tradecraft standard, each phrased as a yes/no question about the draft product; the seven-row probability table in the form `| term | range |`; a "Confidence" section defining **low**, **moderate**, **high** by evidence quality and corroboration, with the example "We assess it is *likely* (moderate confidence) that …"; a "Banned words" section listing `"may"`, `"could"`, `"possibly"`, `"might"`, `"perhaps"` with scope (Key Judgments, Conclusions, BLUF) and before/after examples.

- [ ] **Step 4: Write `references/sourcing.md`**

Required content: the A–F reliability table with engineering examples exactly as in the spec; the 1–6 credibility table (`| 1 | Confirmed by an independent source |` …); grade notation `B2`; E-ID format (`E1`, `E2`, …) and Evidence Log columns `ID | Item | Source | Grade`; source-precision rules (file:line, commit SHA, URL, log query, named person); rules: every Finding of Fact and Key Judgment cites ≥1 E-ID; a judgment supported only by D/E/F sources has confidence capped at **low**; high confidence requires at least two independent sources graded A–B / 1–2; redaction rule for secrets/PII; "not collected: <reason>" rule.

- [ ] **Step 5: Run tests — expect PASS**

- [ ] **Step 6: Commit** — `git add skills/intel-analyst && git commit -m "Add intel-analyst standards and sourcing references"`

### Task 2: Techniques and tailoring references

**Files:**
- Modify: `skills/intel-analyst/tests/test_skill_structure.py` (append classes)
- Create: `skills/intel-analyst/references/techniques.md`
- Create: `skills/intel-analyst/references/tailoring.md`

**Interfaces:** Consumes `read()` from Task 1.

- [ ] **Step 1: Append failing tests**

```python
class TechniquesTest(unittest.TestCase):
    def setUp(self):
        self.text = read("references/techniques.md")

    def test_all_techniques_have_sections(self):
        for name in ("Analysis of Competing Hypotheses", "Key Assumptions Check",
                     "Indicators / Signposts", "High-Impact / Low-Probability",
                     "What If? Analysis", "Red Team"):
            self.assertRegex(self.text, rf"^## {re.escape(name)}", re.M)

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
```

- [ ] **Step 2: Run — expect FileNotFoundError for both files**

- [ ] **Step 3: Write `references/techniques.md`** — the mode table from spec; one `## ` section per technique (exact headings above) with: when to use, numbered procedure, output format. ACH section uses Heuer's 8 steps, matrix cells C/I/N, rule "rank hypotheses by fewest inconsistent items; seek evidence that disconfirms, not confirms". Red Team section: rigorous handoff to `codered:devils-advocate` with input (draft Key Judgments, hypotheses/options, Evidence Log), how to fold output back (revise judgment or lower confidence, note the change); quick-mode and fallback = three strongest counter-arguments inline.

- [ ] **Step 4: Write `references/tailoring.md`** — profile table with ids `` `leadership` `` → BLUF one-pager, `` `engineers` `` → full product, `` `self` `` → full product + working notes; file naming `-bluf.md` for leadership; rules: derive from the full product; never add a judgment absent from it; each tailored version links to the full product via relative link; derive after the full product passes the checklist.

- [ ] **Step 5: Run tests — expect PASS**

- [ ] **Step 6: Commit** — `"Add intel-analyst techniques and tailoring references"`

### Task 3: Product templates

**Files:**
- Modify: `skills/intel-analyst/tests/test_skill_structure.py`
- Create: `skills/intel-analyst/templates/{decision-brief,investigation-package,risk-assessment,bluf-one-pager}.md`

- [ ] **Step 1: Append failing tests**

```python
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

    def test_bluf_one_pager(self):
        text = read("templates/bluf-one-pager.md")
        self.assertNotIn("Evidence Log", text)
        self.assertIn("Full product:", text)
        self.assertIn("BLUF:", text)
```

- [ ] **Step 2: Run — expect FileNotFoundError**

- [ ] **Step 3: Write the four templates** — each full template: the common header block (fenced as real markdown, not a code block), then `## N. <Section>` headings in the order above, each with a one-line `<!-- guidance -->` comment and a skeleton table where the spec names one (ACH matrix, register, chronology, Evidence Log `| ID | Item | Source | Grade |`); tail sections as `## <Section>` without numbers. Investigation package marks Findings of Fact "observed facts only" and Investigator's Comments "opinion — separate from findings". BLUF one-pager: title, BLUF, top three judgments, action, confidence & gaps line, `Full product: [<title>](./YYYY-MM-DD-<slug>.md)`.

- [ ] **Step 4: Run tests — expect PASS**

- [ ] **Step 5: Commit** — `"Add intel-analyst product templates"`

### Task 4: Scenario baseline (RED) and incident fixture

Runs before `SKILL.md` exists, per `superpowers:writing-skills`.

**Files:**
- Create: `skills/intel-analyst/tests/fixtures/make_incident_repo.sh`
- Create: `skills/intel-analyst/tests/scenarios.md` (scenario prompts + pass criteria)
- Create: `skills/intel-analyst/tests/RESULTS.md` (baseline section)

- [ ] **Step 1: Write `make_incident_repo.sh <dir>`** — builds a git repo for a small Python checkout service, with commits: initial, a config refactor, a commit that changes a retry timeout from seconds to milliseconds without converting the value (the planted bug, `RETRY_TIMEOUT = 30` read as ms), an unrelated dependency bump, and a `logs/app.log` that contains the real signal (timeouts after deploy) plus misleading noise (a burst of DNS warnings that started earlier and a GC pause). Uses `-c user.name=fixture -c user.email=fixture@example.invalid` so it never depends on global identity.
- [ ] **Step 2: Run it into a temp dir; verify `git log --oneline | wc -l` is 4 and the bug line exists.**
- [ ] **Step 3: Write `scenarios.md`** — S1 decision (Postgres vs DynamoDB event store), S2 investigation (fixture repo, "checkout requests started failing after Tuesday's deploy; find the root cause"), S3 risk (upgrade a named framework major version), P1 "just give me the answer fast" on S2, P2 contradictory benchmark claims on S1, P3 all-weak-sources risk question; and the GREEN pass criteria verbatim from the spec.
- [ ] **Step 4: Baseline** — dispatch one sonnet subagent per S1–S3 without the skill; a sonnet judge scores each against the criteria. Record failures in `RESULTS.md` under "Baseline (no skill)".
- [ ] **Step 5: Run unit tests (fixture script has a test: append `FixtureTest` that runs the script into a tempdir and asserts 4 commits and the bug string).**
- [ ] **Step 6: Commit** — `"Add intel-analyst scenarios, incident fixture, and baseline results"`

### Task 5: SKILL.md, GREEN run, pressure tests

**Files:**
- Modify: `skills/intel-analyst/tests/test_skill_structure.py`
- Create: `skills/intel-analyst/SKILL.md`
- Modify: `skills/intel-analyst/tests/RESULTS.md`

- [ ] **Step 1: Append failing tests**

```python
class SkillFileTest(unittest.TestCase):
    def setUp(self):
        self.text = read("SKILL.md")

    def test_frontmatter(self):
        self.assertTrue(self.text.startswith("---\nname: intel-analyst\n"))
        self.assertRegex(self.text, r"\ndescription: ")

    def test_length(self):
        n = len(self.text.splitlines())
        self.assertTrue(150 <= n <= 250, n)

    def test_every_linked_file_exists(self):
        links = set(re.findall(r"`((?:references|templates)/[\w-]+\.md)`", self.text))
        self.assertEqual(len(links), 8)
        for rel in links:
            self.assertTrue((SKILL_DIR / rel).is_file(), rel)

    def test_integrations_and_fallbacks(self):
        for s in ("codered:devils-advocate", "codered:nfc", "fallback"):
            self.assertIn(s, self.text)

    def test_output_rules(self):
        self.assertIn("docs/intel/YYYY-MM-DD-<slug>.md", self.text)
        self.assertIn("not inside a git repository", self.text)

    def test_checkpoint_is_a_stop(self):
        self.assertRegex(self.text, r"(?i)checkpoint.*\n(?:.*\n){0,6}.*\bSTOP\b")
```

- [ ] **Step 2: Run — expect FileNotFoundError**

- [ ] **Step 3: Write `SKILL.md`** — frontmatter (name, description with triggers); overview; "Step 0 — Classify" with both tables and "if any rigorous condition is true, the mode is rigorous"; steps 1–6 from spec naming the reference/template each step loads; quick-mode compression; error-handling table; output rules; "Red flags" table addressing baseline failures recorded in Task 4. 150–250 lines.

- [ ] **Step 4: Run unit tests — expect PASS**

- [ ] **Step 5: GREEN** — rerun S1–S3 and P1–P3 with the skill loaded (subagent reads `SKILL.md` and follows it; for rigorous runs the subagent reports the checkpoint and the judge confirms it stopped, then a second turn approves). Sonnet judge scores against criteria. Record in `RESULTS.md`.

- [ ] **Step 6: REFACTOR** — fix every failure in skill wording; rerun the affected scenario; record.

- [ ] **Step 7: Commit** — `"Add intel-analyst SKILL.md with GREEN scenario results"`

### Task 6: README and PR

**Files:** Modify `README.md` (badge 15 → 16; new `### 🕵️ [Intel Analyst](skills/intel-analyst/)` section after Worker-Proof Planning in the same style: paragraph + Trigger/Output/Checks/Scope table).

- [ ] **Step 1:** Edit README. Verify `grep -c 'skills-16' README.md` → 1.
- [ ] **Step 2:** Run full unit suite; all pass.
- [ ] **Step 3:** Commit — `"List intel-analyst in the README"`.
- [ ] **Step 4:** Whole-branch review by a sonnet subagent against spec + plan; fix findings; re-verify with sonnet.
- [ ] **Step 5:** Push `skill/intel-analyst`; open PR against `main` with summary, test results, and open questions.
