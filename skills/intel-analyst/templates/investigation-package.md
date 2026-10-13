# <Title: what happened, where, when>

**Product:** Investigation Package · **Mode:** <Rigorous | Quick (user override)> · **Date:** YYYY-MM-DD · **Analyst:** Claude (+ <user>)
**Key Question:** <one sentence — usually "what caused X?">
**Readers:** <profiles: leadership, engineers, self> · **Decision needed by:** <date or n/a>

**BLUF:** <2–3 sentences: the root cause with probability term and confidence,
the impact, and the most important corrective action. If the cause is
undetermined, say so here.>

## 1. Synopsis

<!-- What happened, the impact (users, duration, data), and the established cause in one paragraph. -->

## 2. Chronology

<!-- Timestamped, UTC, oldest first. Every entry cites at least one E-ID. -->

| Time (UTC) | Event | Evidence |
|---|---|---|
| YYYY-MM-DD HH:MM | <event> | E1 |

## 3. Findings of Fact

<!-- Observed facts only. No interpretation: no "so", "because", "probably", "which means". Each finding cites E-IDs. -->

1. <observed fact>. [E2]
2. …

## 4. Analysis

<!-- Competing cause hypotheses, the ACH matrix, and the surviving hypothesis. See references/techniques.md. -->

| Evidence | H1: <cause> | H2: <cause> | H3: <cause> |
|---|---|---|---|
| E2 <short> | C | I | N |
| **Inconsistent (weighted)** | **0** | **1** | **0** |

<Why the surviving hypothesis survived; why each other one was rejected; which evidence decides it.>

## 5. Conclusions

<!-- Root cause and contributing factors. Each: scale term + (confidence) + E-IDs. If no hypothesis survives, write "Cause undetermined" with the closest hypotheses and the evidence that would separate them. -->

1. **Root cause:** It is *<term>* (<confidence> confidence) that <cause>. [E2, E4]
2. **Contributing factor:** …

## 6. Investigator's Comments

<!-- Opinion — separate from findings. Suspicions, patterns, process observations. Not evidence, and not cited as evidence elsewhere. -->

## 7. Recommended Actions

<!-- Detective rows carry the indicators that would show the cause recurring. -->

| # | Action | Type | Owner | Addresses |
|---|---|---|---|---|
| 1 | <action> | Corrective / Preventive / Detective | <owner> | Conclusion 1 |

## Evidence Log

| ID | Item | Source | Grade |
|---|---|---|---|
| E1 | <one fact or claim> | <path:line @ SHA, commit, query + window, person> | <A–F><1–6> |

## Key Assumptions

- <assumption> — **<solid | caveated | unsupported>** — <basis or condition>

## Alternative Views / Red Team

<!-- Red Team summary from devils-advocate (or inline fallback) and what changed as a result. -->

## Intelligence Gaps

<!-- Ordered by how much each gap would change the answer, largest first. -->

- <unknown> — <how to collect it> — <would it change the conclusion?>
