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
| 7 One-pager has no judgment absent from full product | PASS | PASS | FAIL | PASS | PASS | FAIL-minor |
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

## REFACTOR round 2 (S3 and P2 re-run)

Re-ran the two scenarios with the most round-1 failures against the revised
skill. The checkpoint was pre-approved (verified in round 1), so criterion 6
is N/A.

| Check | S3 | P2 |
|---|---|---|
| 1–3, 5, 8 | PASS | PASS |
| Risk-level adjectives or estimated % in judgments | PASS (fixed) | PASS |
| BLUF judgment matches Key Judgment | PASS (fixed) | FAIL-minor — "cost about the same" stronger than KJ2 |
| Key Judgment rests only on gap rows | PASS (fixed) | PASS |
| ACH ranks an untested option first | PASS | PASS (fixed — option marked "untested") |
| Conflict weighting stated with grades | N/A | FAIL — conflicting cost rows dropped from ACH as non-discriminating |
| Inferences in Evidence Log | FAIL-minor | FAIL-minor |

**Cause of the P2 failure:** ACH step 4 told the analyst to drop rows that do
not discriminate between options, which removed both conflicting sources
before the conflict rule applied. The skill contradicted itself.

**Fixes:** ACH step 4 now keeps conflicting rows side by side; the weighting
sentence must appear in the affected Key Judgment; the BLUF and tailored
versions may not add estimates, quantities, or comparisons.

**Variation note:** round 1 P2 recommended Postgres; round 2 recommended
DynamoDB. Both rated the overall-fit judgment at or near *roughly even chance*
with low confidence, so the products agree that the evidence does not decide
the question.

## REFACTOR round 3 (P2 re-run)

Both conflicting cost sources now appear in the ACH matrix with grades, and a
Key Judgment names the weighting: "colleague benchmark (D3) was weighted over
the vendor blog (E3)". Three consistency failures remained: the stated
weighting did not match equal matrix weights; an option marked "insufficiently
tested" was recommended without a provisional label; the one-pager ranked gaps
the full product never ranked. All three are addressed in the branch-review
fixes below.

## Branch review fixes

A whole-branch review found rules that made other rules impossible to
satisfy. Fixed: quick mode keeps every template heading ("Not run (quick
mode)."); investigation indicators go to Recommended Actions as "Detective"
rows; the one-pager copies cost instead of estimating it; the Red Team runs
after every other technique; ACH gains a survival test, a weights-match-words
rule, and a provisional label for untested recommendations; Intelligence Gaps
are ordered by impact; output never overwrites; quick mode gained scenario Q1.

## Final verification (final wording)

| Check | S2 Investigation (rigorous) | Q1 Decision (quick) |
|---|---|---|
| 1–3, 5, 8 | PASS | PASS |
| 4 Findings free of interpretation | PASS | N/A |
| 6 Checkpoint behavior | PASS — stopped | PASS — did not stop |
| 7 One-pager adds nothing | PASS | N/A (reader `self`, no tailored file) |
| Scenario-specific | PASS — unit mismatch found, reproduced locally; DNS rejected on timing | PASS — quick mode, Working Notes present |
| Risk adjectives / estimated % | PASS | PASS |
| ACH survival test, weights, provisional label | PASS | PASS — "no clear winner", provisional choice with reversing test named |
| Detective rows; Red Team last | PASS | N/A |
| Evidence Log: inferences / derived grades | FAIL-minor — one derived row graded A1, lowest input A2 | PASS |

## Known residuals

- Derived-grade arithmetic (lowest-input rule) is occasionally misapplied by
  one step. The rule is stated; this is an execution slip, not a wording gap.
- P2 (contradictory evidence) was not re-run after the final wording. Its
  remaining round-3 failures map to rules added in the branch-review fixes,
  which S2 and Q1 exercised (survival test, weights, provisional label).
- Recommendations on close decisions vary between runs (P2 chose Postgres in
  rounds 1 and 3, DynamoDB in round 2). Every run rated the deciding judgment
  near *roughly even chance* with low confidence, which is the honest output
  for that evidence.
- Scenario runs used sonnet subagents. Behavior on other models is untested.
