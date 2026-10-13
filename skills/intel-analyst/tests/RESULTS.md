# Intel Analyst — Scenario Results

Scenarios and pass criteria: `scenarios.md`. Each run used a fresh sonnet
subagent; a separate sonnet judge scored the output. Run date: 2026-10-13.

## Baseline (no skill)

Criterion numbers refer to the pass criteria in `scenarios.md`. Criterion 6
(checkpoint) cannot be judged from a document and is N/A for the baseline.

| Criterion | S1 Decision | S2 Investigation | S3 Risk |
|---|---|---|---|
| 1 Scale terms, no hedges | FAIL — "Probably overkill at 2k/sec" | FAIL — no scale terms | FAIL — "Overall risk: Low to Medium" |
| 2 Probability and confidence separate | FAIL | FAIL | FAIL |
| 3 E-ID citations | FAIL — no Evidence Log | FAIL — ad hoc commit/timestamp citations | FAIL — no Evidence Log |
| 4 Facts vs. opinion | N/A | FAIL — "It is why they are so consistent" in evidence | N/A |
| 5 ACH, two or more hypotheses | FAIL — comparison table only | FAIL — "ruled out" bullet list | FAIL — risk matrix only |
| 6 Checkpoint | N/A | N/A | N/A |
| 7 Tailored version | FAIL — one document | FAIL — manager summary inside main document | FAIL — one document |
| 8 Output path | FAIL | FAIL | FAIL |

**S2 specifics:** root cause correct (commit 3 passes 30 s to a millisecond
parameter). DNS was partly rejected with timing evidence, but the summary then
blamed DNS as a contributing mechanism ("payments host takes roughly 1 second
or more to resolve"), which mixes a distractor into the conclusion.

**Most common baseline failures**

1. No Evidence Log; citations are ad hoc or missing.
2. No calibrated language; probability and confidence never separated.
3. Hedge words in judgments ("probably", "usually").
4. Interpretation mixed into evidence sections.
5. No ACH matrix, no tailored reader version, no consistent output path.

**Baseline strength:** all three documents stated their assumptions and
unverified claims honestly.
