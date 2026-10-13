# Sourcing

How to record, grade, and cite evidence. Adapted from ODNI ICD 206,
*Sourcing Requirements*, and the NATO Admiralty Code.

## The Evidence Log

Every item of evidence gets one row. IDs are `E1`, `E2`, … in collection order
and are never reused or renumbered.

| ID | Item | Source | Grade |
|---|---|---|---|
| E1 | `charge()` passes `timeout_ms=RETRY_TIMEOUT` to `post()` | `checkout/payments.py:11` @ `a1b2c3d` | A2 |
| E2 | Checkout 5xx rate rose from 0.1% to 12% at 14:02 UTC | Grafana `checkout-errors`, query `sum(rate(http_5xx[5m]))` | A2 |

**Item** is one fact or one claim, in one sentence. **Source** must let a reader
find the exact evidence again:

- code: `path:line` and the commit SHA
- git history: commit SHA and subject line
- logs and metrics: the system, the query, and the time window
- web: the URL and the date read
- a person: name or role, and when they said it

"The docs" or "the logs" is not a source.

## Observations, derivations, and inferences

The Evidence Log holds what was observed, plus calculations made directly
from it. It does not hold conclusions.

- **Observation** — read from a source. Graded normally.
- **Derived** — a calculation or code trace that follows mechanically from
  logged items ("30 passed as milliseconds is a 0.03 s timeout"). Source:
  `derived from E1, E3`. Grade: the lowest reliability and credibility of its
  inputs. Prefix the item with "Derived:".
- **Inference** — an explanation, a "because", or a judgment about what the
  evidence means. Not an Evidence Log item. It belongs in Analysis, Key
  Judgments, or Conclusions, where it cites the E-IDs it rests on.

Test: if two careful analysts would always get the same result from the
inputs, it is derived. If they might disagree, it is an inference.

Signal words: "so", "which suggests", "probably", "because", "would not
allow", "means that". An Evidence Log item or a Finding of Fact that contains
one is usually an inference. Split it: log the observation, move the
inference to Analysis.

## Source reliability (A–F)

Grade the source, not the claim.

| Grade | Meaning | Engineering examples |
|---|---|---|
| A | Completely reliable | System of record, own reproduced test, production metrics |
| B | Usually reliable | Official docs, vendor changelog, source code of the dependency |
| C | Fairly reliable | Reputable third-party benchmark, maintainer comment |
| D | Not usually reliable | Forum answer, blog post, unverified issue comment |
| E | Unreliable | Known-wrong or marketing-only source |
| F | Cannot be judged | Unattributed claim, hearsay |

## Information credibility (1–6)

Grade the claim, not the source.

| Grade | Meaning |
|---|---|
| 1 | Confirmed by an independent source |
| 2 | Probably true — consistent with other evidence, not independently confirmed |
| 3 | Possibly true — not contradicted, not corroborated |
| 4 | Doubtful — conflicts with some other evidence |
| 5 | Improbable — contradicted by better evidence |
| 6 | Cannot be judged |

Write the grade as one token: `B2`, `D3`, `A1`.

## Citation rules

1. Every Finding of Fact and every Key Judgment cites at least one E-ID, in
   brackets: `[E2, E5]`.
2. A cited E-ID must exist in the Evidence Log.
3. A judgment supported only by D-, E-, or F-graded sources has confidence
   capped at **low**.
4. High confidence requires at least two independent sources graded A–B / 1–2.
   Two items from the same source (two lines of the same log) count as one.
5. When sources conflict, log both. Record the conflict in the ACH matrix and
   say in the judgment which source was weighted more, and why, naming the
   grades: "The colleague's benchmark (C3) was weighted over the vendor blog
   (E3) because …". "Neither was weighted heavily" does not meet this rule;
   if they are weighted equally, say so and say why. Put this sentence in the
   Key Judgment the conflict affects, not only in the ACH section. ACH weights
   must follow the grades.
6. A Key Judgment needs at least one supporting E-ID that is an observation or
   a derived row. "Not collected" rows and F-graded analyst recall can be cited
   as gaps, but never as the only support.

## Evidence that could not be collected

If a source is unreachable (no log access, web fetch failed, metrics expired),
log it anyway:

| ID | Item | Source | Grade |
|---|---|---|---|
| E7 | not collected: no access to production load balancer logs | — | — |

List the same item under Intelligence Gaps with a way to collect it.

## Sensitive data

Never copy secrets, tokens, credentials, or personal data into the Evidence Log.
Cite where the item is and describe it: "API key committed in `deploy.env:3`
(value redacted)".
