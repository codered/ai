# Gate 6 — The Prose Gate

Companion to `skills/mission-grade/SKILL.md`. Load this when reviewing, to classify a prose
finding or to decide whether something is a finding at all.

Gate 6 inspects prose that ships in the repository. It never inspects your own review output.

---

## Severity mapping

Severity tracks harm to a reader who trusts the prose. It does not track how many rules the
line breaks.

### Blocker — must fix before merge

| Finding | Why |
|---|---|
| A warning or caution placed after a destructive step | The reader runs the command before reaching the warning. This is the failure mode the rule exists to prevent. |
| A comment or docstring that contradicts the code | A wrong comment is worse than no comment. Callers trust it and build on a false premise. |
| An error message instructing an unsafe action | The message causes the harm it was meant to prevent. |
| A secret, token, or PII value in a log string | Also DoD baseline #7. Report it under Gate 3 with the immediate-action callout. |

### Major — fix before merge

| Finding | Why |
|---|---|
| A public API with no docstring | The caller has to read the implementation to use it. |
| An error message that states a failure and no action | The reader is stuck with no next step. |
| A new identifier introducing a second term for an existing concept | Vocabulary drift compounds. Every later reader pays. |
| Undefined jargon on first use in a public docstring | Excludes exactly the reader who most needs the doc. |

### Minor — fix if easy

- A procedural comment over the 20-word cap
- Passive voice where the actor is known
- A new identifier with 4 concept words
- Hedging with no stated cause
- An emoji in a user-facing string

### Nit — optional

- A substitution-table word (`utilize` for `use`)
- An emoji in an internal comment or docstring
- A dropped article
- A filler word (`basically`, `simply`, `just`)

---

## Not a finding

Do not report any of these. A review that flags them trains the author to ignore Gate 6, which
costs you the blockers too.

- **Existing identifiers** that exceed the concept-word cap, when this change did not introduce
  them. Consistency beats cluster length.
- **Names fixed outside the author's control** — external API fields, protocol constants,
  database columns, framework hooks.
- **Quoted or reproduced material** — code cited from elsewhere, log excerpts, command output,
  sample payloads.
- **Generated files.** Report the generator instead, once.
- **Test fixture strings and sample data.** Deliberately messy input is the point.
- **Your own review prose.** Findings, citations, and callouts are conversation side and exempt.
- **A qualifier that survived a word cap.** Precedence rule 1 says accuracy wins. A longer,
  correct sentence is not a finding.

---

## Finding template

Gate 6 findings use the same shape as every other gate. Cite the rule, state the concrete
failure mode, give 2-3 options, mark the recommendation.

```
**Blocker — Gate 6 (warning placement)** — the caution about wiping customer data sits below
the three steps it applies to, so a reader following the steps in order runs the destructive
command before reading it.

**Options:**
1. **Move the warning above step 1 (recommended):** one-line change, matches the rule, and the
   reader cannot miss it.
2. **Move it above step 1 and add a confirmation prompt:** better if this runs interactively in
   production, since the comment only protects readers of the source.
3. **Move it to the function docstring:** cheapest to read at the call site, but it is lost to
   anyone editing the body.

I'd take option 1 now and open a ticket for option 2 if this is ever run by hand.
```

---

## Review checklist

Run in order. Stop only when all six are answered.

1. Is any warning below the step it applies to? Is that step destructive?
2. Does any comment or docstring state something the code does not do?
3. Does every error string name an action?
4. Does any new identifier introduce a second term for a concept the module already names?
5. Is there an idiom, metaphor, or emoji in shipped prose?
6. Is any public API undocumented, or is jargon undefined on first use?
