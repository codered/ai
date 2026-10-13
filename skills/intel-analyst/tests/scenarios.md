# Intel Analyst — Behavior Scenarios

Scenarios for the RED → GREEN → REFACTOR cycle in `superpowers:writing-skills`.
Each scenario runs in a fresh subagent. A separate judge subagent scores the
output against the pass criteria below. Results are recorded in `RESULTS.md`.

## Setup

S2 and P1 need the incident fixture:

```bash
bash skills/intel-analyst/tests/fixtures/make_incident_repo.sh <empty-dir>
```

## Scenarios

**S1 — Decision.** "We're picking the event store for our new order-events
pipeline: Postgres or DynamoDB. About 2k events/sec peak, append-only, read by
stream consumers and an occasional replay. My team lead and the engineers on
the team need a brief to decide this week."

**S2 — Investigation.** In the fixture repo: "Checkout requests started failing
after Tuesday's deploy (2026-10-06). Find the root cause and write it up for
the team and our engineering manager." Expected cause: commit 3 passes
`RETRY_TIMEOUT = 30` (seconds) to a parameter that takes milliseconds.
Expected distractors: DNS slowness (started three hours before the deploy),
GC pause, gunicorn bump.

**S3 — Risk.** "Assess the risk of upgrading our Django 4.2 service to
Django 5.2 this quarter. Write it up for me and my manager."

**P1 — Time pressure.** S2, with the prompt prefixed: "I'm in a hurry — just
give me the answer fast."

**P2 — Contradictory evidence.** S1, with added context: "A vendor blog says
DynamoDB handles this at a tenth of the cost; a colleague's benchmark says
Postgres was cheaper for us last year." Neither source is provided in full.

**P3 — Weak sources.** "Is it risky to adopt the `fastqueue` library (v0.3,
one maintainer, 40 GitHub stars) for our job runner? All I have is a Reddit
thread and the README."

**Q1 — Quick mode.** In an existing repo: "Quick one, just for me: should
our internal CLI use `argparse` or `click`? Easy to change later." Expected:
quick mode (low stakes, reversible, `self` reader), no checkpoint, every
template heading present.

## Pass criteria (from the spec)

1. Judgments use only the seven scale terms; no banned hedge words ("may",
   "could", "possibly", "might", "perhaps") appear in Key Judgments,
   Conclusions, or the BLUF.
2. Probability and confidence are stated separately on every Key Judgment.
3. Every Key Judgment and Finding of Fact cites at least one E-ID that exists
   in the Evidence Log.
4. Findings of Fact contain no interpretation; opinions appear only in
   Investigator's Comments.
5. At least two hypotheses or options appear in the ACH matrix.
6. Rigorous mode stops at the checkpoint; quick mode does not.
7. The BLUF one-pager contains no judgment absent from the full product.
8. Output files are written to `docs/intel/YYYY-MM-DD-<slug>[-<profile>].md`.

Scenario-specific:

- **S2/P1:** the root cause identified is the seconds/milliseconds mismatch,
  and DNS is rejected with the timing evidence.
- **P1:** the skill keeps rigorous mode, or states the downgrade and gets
  consent; it does not silently skip the checkpoint.
- **P2:** both claims are logged and graded; the conflict appears in ACH; the
  judgment says which was weighted more and why.
- **P3:** confidence is capped at low and the BLUF says so.
- **Q1:** classified quick; did not stop for a checkpoint; sections whose
  technique did not run say "Not run (quick mode)."; no tailored file (reader
  is `self`), and the Working Notes appendix is present.

Criteria that do not apply to a scenario (for example 4 for S1) are scored N/A.
