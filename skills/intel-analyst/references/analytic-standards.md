# Analytic Standards

Rules every product must meet before it is written to disk. Adapted from ODNI
Intelligence Community Directive (ICD) 203, *Analytic Standards*.

## Pre-dissemination checklist

Answer each question about the draft. Every answer must be "yes" before the
product is written. If an answer is "no", fix the draft or record why in
Intelligence Gaps.

- [ ] **Source quality.** Does every Key Judgment and Finding of Fact cite at least one E-ID, and does the Evidence Log grade every source? (see `sourcing.md`)
- [ ] **Uncertainty.** Does every judgment state a probability term from the scale below and a separate confidence level?
- [ ] **Intelligence vs. assumptions vs. judgments.** Can the reader tell which statements are observed facts, which are assumptions, and which are the analyst's judgments?
- [ ] **Alternatives.** Were at least two hypotheses, options, or scenarios tested, and does the product say why the losers lost?
- [ ] **Relevance.** Does the BLUF answer the Key Question for the named readers, including what they should do?
- [ ] **Logical argument.** Does each judgment follow from the cited evidence, with no step the reader has to guess?
- [ ] **Change or consistency.** If an earlier product in `docs/intel/` covered this topic, does this product say whether its judgments changed and why?
- [ ] **Accuracy.** Are all facts, numbers, file paths, commit SHAs, and quotations checked against their sources?
- [ ] **Effective visuals.** Are comparisons, timelines, and risk registers shown as tables, not paragraphs?

## Probability scale

Every judgment uses exactly one of these seven terms. Do not use other
probability words, and do not invent intermediate terms.

| Term | Range |
|---|---|
| almost no chance | 1–5% |
| very unlikely | 5–20% |
| unlikely | 20–45% |
| roughly even chance | 45–55% |
| likely | 55–80% |
| very likely | 80–95% |
| almost certain | 95–99% |

A number may be added in parentheses when it was calculated, for example
"likely (about 70%, from 7 of 10 reproduced runs)". Never state 0% or 100%: a
certain fact is a Finding of Fact, not a judgment.

## Confidence

Confidence describes the evidence behind a judgment. Probability describes the
event. State them separately. Never merge them ("highly likely with high
confidence" is two statements, not one).

- **high** — at least two independent sources graded A–B / 1–2 agree; no
  significant contradicting evidence; key assumptions are *solid*.
- **moderate** — credible sources support the judgment, but corroboration is
  incomplete, or at least one key assumption is *caveated*.
- **low** — sources are weak (D–F), few, or conflicting; or a key assumption is
  *unsupported*. Say so in the BLUF.

Form:

> We assess it is *likely* (moderate confidence) that the timeout regression in
> E4 caused the checkout failures, because …

## Banned words

These words are banned in Key Judgments, Conclusions, and the BLUF:
"may", "could", "possibly", "might", "perhaps".

They hide the probability. Replace each one with a scale term.

| Before | After |
|---|---|
| The cache may be the cause. | It is *unlikely* (moderate confidence) that the cache is the cause. |
| Migration could take two sprints. | It is *likely* (low confidence) that migration takes two sprints or more. |

The words are allowed elsewhere — for example in Investigator's Comments or in
quoted evidence — but prefer a scale term everywhere.
