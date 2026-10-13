# <Title: the risk subject — system, change, dependency, project>

**Product:** Risk Assessment · **Mode:** <Quick | Rigorous> · **Date:** YYYY-MM-DD · **Analyst:** Claude (+ <user>)
**Key Question:** <one sentence — what could go wrong, and how much it matters>
**Readers:** <profiles: leadership, engineers, self> · **Decision needed by:** <date or n/a>

**BLUF:** <2–3 sentences: the top risk with its likelihood (scale term),
impact, and confidence; and the most valuable mitigation. Every judgment here
is also a Key Judgment. No risk-level adjectives ("moderate risk") — see
references/analytic-standards.md.>

## 1. Key Judgments

<!-- 3–5 numbered judgments. Each: scale term + (confidence) + cited E-IDs. No banned words. -->

1. We assess it is *<term>* (<confidence> confidence) that <judgment>. [E1]
2. …

## 2. Threat/Risk Register

<!-- One row per risk. Likelihood uses only the seven scale terms. Impact: Low / Medium / High / Critical. -->

| # | Risk | Likelihood | Impact | Confidence | Evidence |
|---|---|---|---|---|---|
| R1 | <risk> | <scale term> | <Low/Medium/High/Critical> | <low/moderate/high> | E1, E3 |

## 3. Scenarios

<!-- Three scenarios. Rigorous mode: run High-Impact / Low-Probability for the third. -->

**Most likely.** <what happens, likelihood, impact>

**Most dangerous.** <worst credible outcome, likelihood, impact>

**High-impact / low-probability.** <event, the path that leads to it, its triggers>

## 4. Indicators & Warnings

| Indicator | Scenario | Observable | Threshold | Action |
|---|---|---|---|---|
| <name> | <scenario> | <metric, log signature, release> | <value> | <action> |

## 5. Mitigations

<!-- Ranked by risk reduction per unit of effort, highest first. -->

| Rank | Mitigation | Reduces | Effort | Residual risk |
|---|---|---|---|---|
| 1 | <mitigation> | R1 | <S/M/L> | <scale term + impact after> |

## Evidence Log

| ID | Item | Source | Grade |
|---|---|---|---|
| E1 | <one fact or claim> | <path:line @ SHA, URL + date, query + window, person> | <A–F><1–6> |

## Key Assumptions

- <assumption> — **<solid | caveated | unsupported>** — <basis or condition>

## Alternative Views / Red Team

<!-- Red Team summary (devils-advocate in rigorous mode, three inline counter-arguments in quick mode or fallback) and what changed as a result. -->

## Intelligence Gaps

- <unknown> — <how to collect it> — <would it change the assessment?>
