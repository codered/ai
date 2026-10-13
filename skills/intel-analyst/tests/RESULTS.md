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

## GREEN round 1 (with skill)

All six runs classified themselves as rigorous mode and stopped at the
checkpoint before writing judgments. The coordinator replied as the user.

| Criterion | S1 | S2 | S3 | P1 | P2 | P3 |
|---|---|---|---|---|---|---|
| 1 Scale terms, no hedges | FAIL-minor | PASS | FAIL-minor | PASS | PASS | FAIL-minor |
| 2 Probability and confidence separate | PASS | PASS | PASS | PASS | PASS | PASS |
| 3 E-IDs exist | PASS | PASS | PASS | PASS | FAIL-minor | PASS |
| 4 Facts free of interpretation | N/A | PASS | PASS | FAIL-minor | N/A | N/A |
| 5 ACH, two or more options | PASS | PASS | PASS | PASS | PASS | PASS |
| 6 Checkpoint | PASS | PASS | PASS | PASS | PASS | PASS |
| 7 BLUF adds no judgment | PASS | PASS | FAIL | PASS | PASS | FAIL-minor |
| 8 Output path | PASS | PASS | PASS | PASS | PASS | PASS |
| Scenario-specific | N/A | PASS | N/A | PASS | FAIL | PASS |

No banned hedge words appeared in any Key Judgment, Conclusion, or BLUF.

**Scenario-specific results**

- **S2, P1:** both found the seconds/milliseconds root cause and rejected DNS
  with pre-deploy timing. P1 also reproduced the failure against a local stub.
- **P1 (time pressure):** kept rigorous mode, explained why, and offered quick
  mode before continuing.
- **P3 (weak sources):** capped every judgment at low confidence and said so
  in the BLUF.
- **P2 (conflict):** logged and graded both claims, but wrote "neither is
  weighted heavily" instead of saying which source was weighted more.

**Failures and the wording change that addresses each**

| Failure | Fix |
|---|---|
| S3 and P3 BLUFs said "overall risk is moderate/high", which is not a scale term and not a Key Judgment | `analytic-standards.md`: new "The BLUF" section bans risk-level adjectives in judgments. The risk template's BLUF no longer asks for an "overall risk level". |
| S1 BLUF added "about 60%" | Numbers allowed only from a count or calculation in the Evidence Log |
| P2 did not say which conflicting source was weighted more | `sourcing.md` rule 5: name the grades. "Neither weighted heavily" does not meet the rule. |
| P2 ACH ranked an option first because no evidence on it existed | `techniques.md` ACH step 5: an option with far fewer diagnostic rows is "insufficiently tested", not winning |
| Inferences in Evidence Logs and Findings (S2, P1, P2, P3) | `sourcing.md`: observation / derived / inference rules and signal words. The derived-items rule was added mid-round, after these runs had loaded the skill. |
| Judgments cited only "not collected" rows (S3, P3) | `sourcing.md` rule 6 |
| Runs treated "the skill loaded its method" as a fallback | `SKILL.md` and `techniques.md`: applying the loaded method is the integration. Fallback means the skill is not installed. |
