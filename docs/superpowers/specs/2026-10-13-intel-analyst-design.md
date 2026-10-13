# Intel Analyst — Design

**Date:** 2026-10-13
**Status:** Approved for planning
**Skill name:** `intel-analyst`
**Location:** `skills/intel-analyst/`

## Problem

Engineering analysis — choosing a technology, finding a root cause, judging a
risk — is usually written up without discipline. Three failures recur:

1. **Uncertainty is hidden.** "This may cause problems" tells the reader
   nothing. Probability and confidence are mixed, or not stated.
2. **Claims are not traced to evidence.** A reader cannot tell which statements
   are observed facts, which are inferences, and which are opinions.
3. **One hypothesis wins by default.** The first plausible explanation or option
   is adopted; alternatives are never tested against the evidence.

The US Intelligence Community solved these problems with published analytic
standards and tradecraft. The methods transfer directly to engineering work.

## Solution

A general-purpose analyst skill that applies public IC tradecraft to engineering
questions and writes versioned intelligence-style products into the repository.

**Source standards (all public):**

| Source | What the skill takes from it |
|---|---|
| ODNI ICD 203 — Analytic Standards | Tradecraft checklist, seven-term probability scale, separate confidence levels |
| ODNI ICD 206 — Sourcing Requirements | Every judgment cites its sources; source descriptors |
| ODNI ICD 208 — Maximizing Utility | Reader-tailored versions derived from one full product |
| CIA *Tradecraft Primer: Structured Analytic Techniques* (2009) | ACH, Key Assumptions Check, Indicators/Signposts, High-Impact/Low-Probability, What If?, Red Team |
| Heuer, *Psychology of Intelligence Analysis* | ACH procedure; disconfirmation over confirmation |
| NSA reporting discipline (public principles only) | Statement-level source attribution; facts separated from analyst comment |
| AFOSI Report of Investigation structure | Evidence log, chronology, findings of fact separated from investigator comments |
| NATO Admiralty Code | Source reliability A–F, information credibility 1–6 |

Agency-internal SOPs are not public. The skill borrows method and structure
only. It does not reproduce classification markings or imitate agency products.

## Scope

**In scope:** the skill file, four reference files, four templates, and a
scenario-based test suite.

**Out of scope:** classification or handling markings; publishing to external
services; automated collection integrations (Datadog, PagerDuty, etc.) beyond
what Claude's existing tools already reach; a plugin of its own.

## Artifact

```
skills/intel-analyst/
  SKILL.md                     triggers, classification, workflow, checkpoints
  references/
    analytic-standards.md      ICD 203 checklist, probability scale, confidence
    sourcing.md                ICD 206 citation rules, Admiralty grading
    techniques.md              structured analytic techniques, per-mode usage
    tailoring.md               ICD 208 reader profiles and derivation rules
  templates/
    decision-brief.md
    investigation-package.md
    risk-assessment.md
    bluf-one-pager.md
```

`SKILL.md` stays between 150 and 250 lines. It loads only the references and
templates that the current product and mode need (progressive disclosure).

**Output location:** `docs/intel/YYYY-MM-DD-<slug>.md` in the repository the
user is working in. Tailored versions use a suffix, for example
`docs/intel/YYYY-MM-DD-<slug>-bluf.md`.

## Workflow

### Triggers

"assess", "brief me on", "investigate", "root cause", "risk assessment",
"should we use X or Y", "intel package", "analyze this decision", and
`/intel-analyst`.

### Step 0 — Classify

The skill selects one product type and one mode. It states both in one line
and lets the user override.

| Product | Use | Template |
|---|---|---|
| Decision brief | Technology, vendor, architecture, build-vs-buy choices | `decision-brief.md` |
| Investigation package | Incident root cause, debugging, postmortem | `investigation-package.md` |
| Risk assessment | Security, dependency, project, upgrade risk | `risk-assessment.md` |

| Mode | Select when | Checkpoint |
|---|---|---|
| Quick | Low stakes, under about one hour of analysis, reversible | None |
| Rigorous | Any investigation package; architecture or vendor choice; security risk; irreversible action; leadership reader | Yes, before judgments |

If any rigorous condition is true, the mode is rigorous.

### Steps 1–6 — Intelligence cycle

1. **Tasking.** Ask at most four questions: key intelligence question, readers
   (one or more), decision deadline, what is already known. Skip any question
   the prompt already answers. Quick mode asks at most one.
2. **Collection.** Gather evidence from code, git history, logs, metrics, docs,
   and the web. Record every item in the Evidence Log with an ID (E1, E2, …),
   an exact source, and an Admiralty grade.
3. **Processing.** Separate facts from claims. Form two to five competing
   hypotheses (investigation) or options (decision) or scenarios (risk).
4. **Checkpoint (rigorous mode only).** Show the Evidence Log, the hypotheses,
   and the Key Assumptions. Stop. Continue only after the user adds evidence,
   corrects, or approves.
5. **Analysis.** Run ACH and a Key Assumptions Check. Run the Red Team step by
   invoking `codered:devils-advocate` with the draft key judgments, the
   hypotheses, and the evidence log as input. Write judgments with ICD 203
   probability terms and a separate confidence level.
6. **Dissemination.** Run the ICD 203 checklist. Pass all prose (BLUF, Key
   Judgments, narrative sections) through `codered:nfc`; tables, logs, and
   matrices are not rewritten. Write the full product, then one tailored
   version per additional reader profile.

**Quick mode compression:** one tasking question maximum; short Evidence Log;
no checkpoint; abbreviated ACH (options × top evidence only); Red Team reduced
to three counter-arguments written inline instead of invoking
`codered:devils-advocate`.

## Templates

### Common header (all products)

```
# <Title>
Product: Decision Brief | Investigation Package | Risk Assessment
Mode: Quick | Rigorous    Date: YYYY-MM-DD    Analyst: Claude (+ <user>)
Key Question: <one sentence>
Readers: <list>    Decision needed by: <date or n/a>
BLUF: <2–3 sentences: answer, probability term, confidence>
```

### Common tail (all products)

- **Evidence Log** — table: ID | Item | Source (file:line, commit, URL, log
  query, person) | Grade (A–F / 1–6)
- **Key Assumptions** — each marked *solid*, *caveated*, or *unsupported*
- **Alternative Views / Red Team** — devils-advocate output summary and what
  would change the judgment
- **Intelligence Gaps** — unknowns and how to collect them

### Decision brief

1. Key Judgments — three to five numbered statements, each citing E-IDs
2. Options — per option: description, evidence for and against, cost/effort, risk
3. ACH Matrix — options × evidence; cells: consistent (C), inconsistent (I), neutral (N)
4. Recommendation — chosen option, probability it succeeds, confidence
5. Signposts — indicators that would trigger revisiting the decision

### Investigation package (AFOSI Report of Investigation style)

1. Synopsis — what happened, impact, established cause
2. Chronology — timestamped timeline, each entry citing E-IDs
3. Findings of Fact — observed facts only, each cited, no interpretation
4. Analysis — competing cause hypotheses, ACH matrix, surviving hypothesis
5. Conclusions — root cause and contributing factors, each with probability and confidence
6. Investigator's Comments — opinions, suspicions, patterns; visibly separate
7. Recommended Actions — corrective and preventive, each with an owner placeholder

### Risk assessment

1. Key Judgments
2. Threat/Risk Register — table: Risk | Likelihood (ICD 203 term) | Impact (Low/Medium/High/Critical) | Confidence | Evidence
3. Scenarios — most likely, most dangerous, high-impact/low-probability
4. Indicators & Warnings — observable signals per scenario
5. Mitigations — ranked by risk reduction per unit of effort

### BLUF one-pager (derived)

BLUF, top three judgments, recommendation or action, one-line confidence and
gaps summary, relative link to the full product. No Evidence Log.

## Reference files

### `references/analytic-standards.md`

- The ICD 203 tradecraft standards as a pre-dissemination checklist: describe
  source quality; express uncertainty; distinguish intelligence from
  assumptions and judgments; incorporate alternatives; demonstrate relevance;
  use clear logical argumentation; explain change or consistency with prior
  judgments; make accurate judgments; use effective visuals.
- **Probability scale.** Judgments use only these seven terms:

  | Term | Range |
  |---|---|
  | almost no chance | 1–5% |
  | very unlikely | 5–20% |
  | unlikely | 20–45% |
  | roughly even chance | 45–55% |
  | likely | 55–80% |
  | very likely | 80–95% |
  | almost certain | 95–99% |

- **Confidence** — low, moderate, or high — reflects evidence quality and
  corroboration. It is stated separately from probability, never merged.
  Form: "We assess it is *likely* (moderate confidence) that …"
- **Banned in judgments:** "may", "could", "possibly", "might", "perhaps".
  Replace with a scale term.

### `references/sourcing.md`

Source reliability, adapted for engineering:

| Grade | Meaning | Engineering examples |
|---|---|---|
| A | Completely reliable | System of record, own reproduced test, production metrics |
| B | Usually reliable | Official docs, vendor changelog, source code of the dependency |
| C | Fairly reliable | Reputable third-party benchmark, maintainer comment |
| D | Not usually reliable | Forum answer, blog post, unverified issue comment |
| E | Unreliable | Known-wrong or marketing-only source |
| F | Cannot be judged | Unattributed claim, hearsay |

Information credibility: 1 confirmed by an independent source; 2 probably
true; 3 possibly true; 4 doubtful; 5 improbable; 6 cannot be judged.

Rules:
- Every Finding of Fact and every Key Judgment cites at least one E-ID.
- A judgment supported only by D-, E-, or F-graded sources has confidence capped at *low*.
- High confidence requires at least two independent sources graded A–B / 1–2.

### `references/techniques.md`

Step-by-step procedures for each technique and when to apply it:

| Technique | Quick mode | Rigorous mode |
|---|---|---|
| ACH (Heuer 8-step; seek disconfirming evidence) | Abbreviated | Full |
| Key Assumptions Check | Top three assumptions | Full list |
| Indicators / Signposts | Decision brief only | All products |
| High-Impact / Low-Probability | — | Risk assessment |
| What If? analysis | — | Optional, when a key assumption is *unsupported* |
| Red Team | Three inline counter-arguments | `codered:devils-advocate` |

Red Team handoff to `codered:devils-advocate`: input is the draft Key
Judgments, the hypotheses or options, and the Evidence Log. The output is
summarized in the Alternative Views section; any judgment the Red Team breaks is
revised or its confidence lowered, and the change is noted.

### `references/tailoring.md`

| Profile | Receives |
|---|---|
| Leadership / stakeholder | BLUF one-pager |
| Peer engineers | Full product |
| Self | Full product plus working notes (rejected hypotheses, raw ACH scoring) |

Rules: tailored versions derive from the full product; they never add a
judgment absent from it; each links to the full product.

## Error handling

| Situation | Behavior |
|---|---|
| Thin evidence (fewer than three items, or all D–F) | Proceed; cap confidence at *low*; state this in the BLUF; populate Intelligence Gaps with collection actions |
| Conflicting sources | Log both; record the conflict in ACH; state in the judgment which source was weighted and why |
| No hypothesis survives ACH | Report "cause undetermined" with the closest hypotheses and the evidence that would separate them; never fabricate a conclusion |
| Source unreachable (logs, web, metrics) | Log "not collected: <reason>"; list under Gaps; continue |
| Question too vague after tasking | Restate as a precise key question; confirm once before collection |
| `codered:devils-advocate` or `codered:nfc` unavailable | Fall back to inline Red Team (three strongest counter-arguments) or plain-writing rules; note the fallback in the product |
| Sensitive data in evidence (secrets, PII) | Redact in the Evidence Log; cite the location, not the content |
| `docs/intel/` missing | Create it. If not inside a git repository, ask the user for an output path |

## Testing

Follows `superpowers:writing-skills` RED → GREEN → REFACTOR. Scenarios run in
subagents; a sonnet subagent judges each output against the checklist below.

**Scenarios**

1. Decision — "Postgres vs. DynamoDB for our event store."
2. Investigation — a seeded fixture repo with a planted bug and misleading log noise.
3. Risk — "Risk of upgrading to framework vX."

**Baseline (RED):** run each scenario without the skill; record failures.

**With skill (GREEN) — pass criteria:**

- Judgments use only the seven scale terms; no banned hedge words appear in Key Judgments, Conclusions, or the BLUF.
- Probability and confidence are stated separately on every Key Judgment.
- Every Key Judgment and Finding of Fact cites at least one E-ID that exists in the Evidence Log.
- Findings of Fact contain no interpretation; opinions appear only in Investigator's Comments.
- At least two hypotheses or options appear in the ACH matrix.
- Rigorous mode stops at the checkpoint; quick mode does not.
- The BLUF one-pager contains no judgment absent from the full product.
- Output files are written to `docs/intel/YYYY-MM-DD-<slug>[-<profile>].md`.

**Pressure tests:** "just give me the answer fast" on a rigorous-class
question; contradictory evidence; all sources graded D–F. The skill keeps its
standards under each.

**REFACTOR:** tighten skill wording for every failure found; re-run the
affected scenario.
