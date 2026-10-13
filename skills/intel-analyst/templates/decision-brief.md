# <Title: the decision, as a question or a choice>

**Product:** Decision Brief · **Mode:** <Quick | Rigorous> · **Date:** YYYY-MM-DD · **Analyst:** Claude (+ <user>)
**Key Question:** <one sentence — what must be decided>
**Readers:** <profiles: leadership, engineers, self> · **Decision needed by:** <date or n/a>

**BLUF:** <2–3 sentences: the recommended option, the probability it succeeds
(scale term), and confidence. State what the reader should do and by when.>

## 1. Key Judgments

<!-- 3–5 numbered judgments. Each: scale term + (confidence) + cited E-IDs. No banned words. -->

1. We assess it is *<term>* (<confidence> confidence) that <judgment>. [E1, E3]
2. …

## 2. Options

<!-- One subsection per option, including "do nothing" when it is a real choice. -->

**Option A — <name>.** <one-paragraph description>

| For | Against | Cost / effort | Risk |
|---|---|---|---|
| <evidence, cited> | <evidence, cited> | <estimate> | <main risk> |

**Option B — <name>.** …

## 3. ACH Matrix

<!-- Options as hypotheses ("A is the best choice"). C = consistent, I = inconsistent, N = neutral. Drop rows that do not discriminate. See references/techniques.md. -->

| Evidence | A: <name> | B: <name> | C: <name> |
|---|---|---|---|
| E1 <short> | C | I | N |
| **Inconsistent (weighted)** | **0** | **1** | **0** |

<One paragraph: which evidence decides the ranking, and why each losing option lost.>

## 4. Recommendation

<!-- The chosen option, probability it meets the success criteria, confidence, and the conditions it depends on. -->

Choose **<option>**. It is *<term>* (<confidence> confidence) that it meets
<success criteria> by <date>, provided <key assumption>.

## 5. Signposts

<!-- Observable events that mean the decision should be revisited. -->

| Indicator | Observable | Threshold | Action |
|---|---|---|---|
| <name> | <metric, release, announcement> | <value> | Revisit decision |

## Evidence Log

| ID | Item | Source | Grade |
|---|---|---|---|
| E1 | <one fact or claim> | <path:line @ SHA, URL + date, query + window, person> | <A–F><1–6> |

## Key Assumptions

- <assumption> — **<solid | caveated | unsupported>** — <basis or condition>

## Alternative Views / Red Team

<!-- Red Team summary (devils-advocate in rigorous mode, three inline counter-arguments in quick mode or fallback) and what changed as a result. -->

## Intelligence Gaps

- <unknown> — <how to collect it> — <would it change the recommendation?>
