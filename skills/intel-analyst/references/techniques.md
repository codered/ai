# Structured Analytic Techniques

Procedures for the techniques the skill uses. Adapted from the CIA *Tradecraft
Primer: Structured Analytic Techniques for Improving Intelligence Analysis*
(2009) and Richards Heuer, *Psychology of Intelligence Analysis*.

## Which techniques run in which mode

| Technique | Quick mode | Rigorous mode |
|---|---|---|
| Analysis of Competing Hypotheses (ACH) | Abbreviated: options × top 3–5 evidence items | Full 8-step procedure |
| Key Assumptions Check | Top three assumptions | Full list |
| Indicators / Signposts | Decision brief only | All products |
| High-Impact / Low-Probability | — | Risk assessment |
| What If? Analysis | — | Optional, when a key assumption is *unsupported* |
| Red Team | Three inline counter-arguments | `codered:devils-advocate` |

## Analysis of Competing Hypotheses

**Use for:** every investigation (cause hypotheses), every decision (options as
hypotheses: "option X is the best choice"), and risk scenarios when more than
one is plausible.

**Core rule:** look for evidence that disconfirms a hypothesis, not evidence
that confirms it. Evidence consistent with every hypothesis has no diagnostic
value. The hypothesis with the fewest *inconsistent* items survives — not the
one with the most consistent items.

**Procedure (Heuer, 8 steps):**

1. List two to five hypotheses. Include at least one you do not expect to win.
2. List the significant evidence and arguments, by E-ID. Include absence of
   evidence ("no error logs before 14:00") as an item.
3. Build the matrix: hypotheses across, evidence down. Mark each cell:
   **C** consistent, **I** inconsistent, **N** neutral or not applicable.
4. Remove evidence rows that are C or N for every hypothesis. They do not
   discriminate. Keep them in the Evidence Log. Exception: when two sources
   conflict, keep both rows in the matrix, side by side, with their grades,
   so the reader sees the conflict and how it was weighted.
5. Count **I** per hypothesis. Weight an **I** from an A/B-graded source more
   than one from a D–F source. Rank hypotheses by fewest inconsistent items.
   Before ranking, count the diagnostic rows (C or I) for each hypothesis. A
   hypothesis with far fewer diagnostic rows than the others is *untested*,
   not winning: collect evidence on it, or mark it "insufficiently tested" in
   the matrix and do not rank it first.
6. Check sensitivity: which few evidence items decide the ranking? If one of
   them is wrong or misread, would the ranking change? Name them.
7. Report every hypothesis, not just the winner, and say why each loser lost.
8. List what would change the conclusion — these become Signposts or
   Indicators.

**Output:**

| Evidence | H1: timeout unit bug | H2: DNS outage | H3: GC pauses |
|---|---|---|---|
| E2 5xx starts at deploy time | C | I | N |
| E5 DNS warnings began 3 h before | N | I | N |
| **Inconsistent (weighted)** | **0** | **2** | **0** |

## Key Assumptions Check

**Use for:** every product.

**Procedure:**

1. List every assumption the Key Judgments rely on — including ones that feel
   obvious ("traffic patterns stay the same", "the staging config matches
   production").
2. For each, ask: why do we believe this? Under what conditions would it be
   false? Has it been false before?
3. Mark each one **solid** (supported by A–B evidence), **caveated** (true
   with conditions — state them), or **unsupported** (believed without
   evidence).
4. A judgment resting on an unsupported assumption has confidence of at most
   **low**, unless the assumption is tested.

**Output:** the Key Assumptions section — one bullet per assumption, its
mark, and its basis.

## Indicators / Signposts

**Use for:** decision briefs (Signposts) and risk assessments
(Indicators & Warnings); investigations when the cause can recur.

**Procedure:**

1. For each judgment or scenario, ask: what would we observe if it turned out
   to be wrong, or if it started to happen?
2. Write each indicator as an observable, checkable event: a metric
   threshold, a release, a vendor announcement, an error signature.
3. Give each indicator what to do when it fires: "revisit the decision",
   "page on-call", "re-run this assessment".

**Output:** a table — Indicator | Observable | Threshold | Action.

## High-Impact / Low-Probability

**Use for:** risk assessments in rigorous mode.

**Procedure:**

1. Pick one event judged *unlikely* or *very unlikely* that would be severe.
2. Assume it happened. Write the most plausible path that leads to it.
3. List the triggers along that path and the indicators that would show each
   trigger.
4. Decide whether any cheap mitigation is justified now.

**Output:** the "high-impact/low-probability" scenario in Scenarios, with its
path and indicators.

## What If? Analysis

**Use for:** rigorous mode, when a key assumption is *unsupported* and the
judgment depends on it.

**Procedure:**

1. Assume the assumption is false.
2. Work backwards: what would have to be true for that? What evidence would
   already exist?
3. Check whether that evidence exists. Record the result as new E-IDs.

**Output:** a short paragraph in Alternative Views, and any change to the
judgment or its confidence.

## Red Team

**Use for:** every product. This step looks for the strongest case against the
draft before the reader does.

**Rigorous mode — invoke `codered:devils-advocate`.** Give it:

1. the draft Key Judgments (or Conclusions), with their probability and confidence,
2. the hypotheses or options, including the ones that lost,
3. the Evidence Log and Key Assumptions.

Invoking the skill loads its method. Apply it to the draft as a separate
pass — switch from author to critic — and write its structured findings.
Attack the judgments, not the format. Then fold the findings back:

- If a challenge breaks a judgment, revise the judgment.
- If a challenge weakens a judgment, lower its confidence or probability.
- If a challenge fails, say why in one line.
- Note every change in Alternative Views / Red Team: "Red Team argued X;
  confidence on KJ2 lowered from moderate to low."

**Quick mode, or fallback when `codered:devils-advocate` is not installed:**
write the three strongest counter-arguments inline in Alternative Views, each
with the evidence that answers it or an admission that it is not answered.
When it is a fallback, state it: "Red Team: inline fallback
(devils-advocate unavailable)."
