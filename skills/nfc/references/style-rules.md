# NFC Style Rules

Reference for `skills/nfc/SKILL.md`. Load this when you need the full rule set, the word
substitutions, or the reasoning behind a constraint.

Two kinds of rule appear below, and they are labelled:

- **[STE]** — derived from ASD-STE100 writing rules. These apply in `strict` mode.
- **[NFC]** — this skill's own extension, for general-purpose writing that ASD-STE100 does not
  cover, such as conversational replies and hedging.

---

## 1. Sentence rules

| # | Rule | Source |
|---|---|---|
| 1.1 | A procedural sentence has 20 words or fewer. | [STE] |
| 1.2 | A descriptive sentence has 25 words or fewer. | [STE] |
| 1.3 | A sentence contains exactly one instruction. Split compound instructions. | [STE] |
| 1.4 | Do not omit the subject, the verb, or an article to save words. | [STE] |
| 1.5 | Use the active voice. Use the passive only in a description where the actor is unknown or irrelevant. | [STE] |
| 1.6 | State the conclusion in the first sentence. Put the reasoning after it. | [NFC] |

**Splitting a compound instruction:**

> Rejected: Stop the pump and close the valve before you drain the tank, then check the seal.
>
> Approved:
> 1. Stop the pump.
> 2. Close the valve.
> 3. Drain the tank.
> 4. Check the seal.

---

## 2. Verb rules

| # | Rule | Source |
|---|---|---|
| 2.1 | Use only these forms: infinitive, imperative, simple present, simple past, simple future, and past participle as an adjective. | [STE] |
| 2.2 | Do not use the present perfect. Use the simple past. | [STE] |
| 2.3 | Use an `-ing` form only as a technical noun, or inside a technical noun. | [STE] |
| 2.4 | Start every step in a procedure with an imperative verb. | [STE] |

**Tense:**

> Rejected: We have received the reports.
>
> Approved: We received the reports.

**`-ing` forms:**

> Rejected: Removing the panel, disconnect the cable.
>
> Approved: Remove the panel. Disconnect the cable.
>
> Approved: Check the bearing. *(`bearing` is a technical noun)*
>
> Approved: Open the landing gear door. *(`landing` is inside a technical noun)*

---

## 3. Paragraph and structure rules

| # | Rule | Source |
|---|---|---|
| 3.1 | A paragraph contains 6 sentences or fewer. | [STE] |
| 3.2 | A paragraph covers one topic. | [STE] |
| 3.3 | Put complex or sequential information in a vertical list, not in prose. | [STE] |
| 3.4 | Put a warning or caution before the step it applies to. | [STE] |
| 3.5 | Use a heading whenever the topic changes. | [NFC] |
| 3.6 | Do not bury an action inside an explanation. Give the action its own line. | [NFC] |

---

## 4. Word rules

| # | Rule | Source |
|---|---|---|
| 4.1 | One word has one part of speech and one meaning. Do not reuse a word in a second sense. | [STE] |
| 4.2 | A noun cluster contains 3 words or fewer. | [STE] |
| 4.3 | Do not use idioms, metaphors, figures of speech, or sarcasm. | [STE] |
| 4.4 | Define a technical term on first use, or replace it with a common word. | [STE] |
| 4.5 | Use the same word for the same thing every time. Do not vary vocabulary for style. | [STE] |
| 4.6 | Hedge only when the uncertainty is real. State what causes it. | [NFC] |
| 4.7 | Do not use emoji as meaning. They render inconsistently and carry unstable connotations. | [NFC] |

**One word, one meaning** — `follow` means "to come after", never "to obey":

> Rejected: Follow the safety instructions.
>
> Approved: Obey the safety instructions.

**Noun clusters:**

> Rejected: main landing gear door actuator seal *(6 words)*
>
> Approved: the seal on the actuator for the main landing gear door

**Consistent vocabulary** — pick one term and keep it:

> Rejected: Open the file. Then save the document. Close the record.
>
> Approved: Open the file. Save the file. Close the file.

---

## 5. Word substitutions

Replace the word on the left with the word on the right. This table is a working aid built
from commonly cited ASD-STE100 substitutions. It is **not** the ASD-STE100 dictionary, and it
is not exhaustive. The authoritative list of approved words is in the official specification —
see [Obtaining the official dictionary](#obtaining-the-official-dictionary).

| Rejected | Approved |
|---|---|
| ensure, verify, confirm, validate | make sure |
| utilize, employ (as a verb) | use |
| commence, initiate | start |
| terminate, cease | stop |
| endeavour, attempt | try |
| accomplish, execute, perform | do |
| obtain, acquire, procure | get |
| require, necessitate | need |
| assist, aid | help |
| permit | let, allow |
| prior to | before |
| subsequent to, following | after |
| in order to, so as to | to |
| in the event that | if |
| at this point in time | now |
| in the vicinity of | near |
| a number of, numerous | many, some |
| the majority of | most |
| approximately | about |
| sufficient | enough |
| additional | more |
| initial | first |
| terminate the operation of | stop |
| is able to, has the ability to | can |
| it is necessary that you | you must |
| it is recommended that | we recommend that you |
| there is a possibility that | possibly, or state the condition |
| due to the fact that | because |
| in spite of the fact that | although |

**Words to delete rather than replace** — they add length without meaning:

`basically`, `essentially`, `actually`, `really`, `very`, `quite`, `simply`, `just`,
`obviously`, `clearly`, `of course`, `needless to say`, `it should be noted that`,
`as you may know`, `at the end of the day`.

---

## 6. Rules NFC does not implement

ASD-STE100 contains 53 writing rules. NFC implements the mechanical ones — the rules that a
model can check against its own draft by counting or pattern-matching.

NFC does **not** implement:

- **The approved-word dictionary.** Around 900 entries, each fixed to one part of speech and
  one meaning. NFC's substitution table in section 5 covers common cases only.
- **Technical name and technical verb procedures.** ASD-STE100 defines a formal process for
  admitting domain-specific terms into a project's vocabulary. That process needs a human
  decision and a maintained project word list.
- **Aerospace-specific conventions.** Warning and caution formats, procedural document
  structure, and illustration rules that assume a maintenance manual.

If you need full conformance — for a regulated document, an S1000D deliverable, or a customer
contract that specifies ASD-STE100 — use the official specification and a checker tool. NFC
improves clarity. It does not certify conformance, and you should not claim that it does.

---

## Obtaining the official dictionary

ASD-STE100 Issue 9 (January 2025) is available free of charge, as a PDF, from the STE
Maintenance Group. You request it through a short form:

- Downloads: <https://www.asd-ste100.org/STE_downloads.html>
- FAQ: <https://www.asd-ste100.org/STE_faq.html>
- Contact: stemg@asd-ste100.org

Copyright in ASD-STE100 is owned by ASD (AeroSpace and Defence Industries Association of
Europe). It is free to obtain, but no public redistribution licence is stated. For that
reason the dictionary is not vendored into this repository.

**To use the official dictionary with NFC:** download the PDF, save it next to this file as
`references/ASD-STE100.pdf`, and add one line to your agent's context file:

```text
When using the NFC skill in strict mode, check word choices against
skills/nfc/references/ASD-STE100.pdf and prefer approved words.
```

Do not commit that PDF to a public repository.
