# STE for Code

Companion to `skills/mission-grade/SKILL.md`. Load this when you need the word rules applied to
identifiers, user-facing strings, or comments, or when you need the substitution table.

ASD-STE100 was written for maintenance manuals. Three of its word rules transfer directly to
code, and this file defines what they mean when the unit is a symbol rather than a sentence.

---

## 1. Identifiers

Three rules apply. Nothing else does — sentence length and voice are meaningless for a name.

| Rule | In code |
|---|---|
| One word, one meaning | A word means the same thing everywhere in the module. Do not use `process` as both a noun and a verb in the same file. |
| Noun clusters of 3 or fewer | An identifier names at most 3 concept words. |
| Same word for the same thing | One term per concept per module. Do not alternate `file`, `document`, and `record` for one thing. |

**Counting concept words.** A leading verb (`get`, `set`, `build`, `parse`, `is`) and a
trailing type or role word do not count toward the 3. The concept words in between do. The
trailing words are exactly these: `List`, `Map`, `Set`, `Error`, `Handler`, `Config`. Treat
that list as closed — a word not on it counts.

- `getUserSessionToken` — verb `get`, concepts `user session token` = 3. Approved.
- `getMainLandingGearDoorActuatorSeal` — 6 concept words. Rejected.
- `parseInvoiceLineItemDiscountRuleSet` — 5 concept words. Rejected.

**Fixing an over-long name** — extract the inner concept into a type, so the name shortens
because the model got better:

> Rejected: `main_landing_gear_door_actuator_seal`
>
> Approved: a `LandingGearDoor` type with an `actuator_seal` attribute, reached as
> `door.actuator_seal`

**One term per concept:**

> Rejected: `save_file()`, `load_document()`, `delete_record()` — three names, one concept
>
> Approved: `save_file()`, `load_file()`, `delete_file()`

**These rules bind new concepts only.** If the module already calls it
`userAuthTokenExpiryPolicy`, a new function about that concept uses that term. Codebase
consistency beats cluster length. Never rename an existing symbol to satisfy this file.

**These rules never apply to** names fixed by something outside your control: external API
fields, protocol constants, database column names, framework hooks, and names in generated
code.

---

## 2. User-facing strings

Error, log, and CLI-help strings are `strict`. They are read by someone who is already stuck,
often at speed, often at 3 a.m.

**The formula: what failed, why, what to do.**

> Rejected: `Error: operation could not be completed successfully.`
>
> Approved: `Cannot write the config file. The directory /etc/app is read-only. Run the command
> with sudo, or set APP_CONFIG_DIR to a writable path.`

Rules that carry the most weight here:

- 20 words or fewer per sentence. Split a long message into short sentences, not clauses.
- Active voice. Name the actor. `The parser rejected line 12`, not `Line 12 was rejected`.
- Name an action the reader can take. A message with no action is a Gate 6 major.
- No hedging. `The file may not exist` is useless — check, then say which it is.
- No emoji. They render inconsistently across terminals, log aggregators, and CI output.
- No idioms. `Something went sideways` means nothing to a non-native reader or a translator.

> Rejected: `Oops! Something went wrong 😅 — the upload may have failed.`
>
> Approved: `The upload failed. The server returned status 507, which means it is out of
> storage. Retry after you free space, or contact support with request ID {id}.`

---

## 3. Comments and docstrings

Docstrings and rationale comments are `clear`. Procedural comments are `strict`.

**State the conclusion first.** The first sentence of a docstring says what the function does.
Reasoning, caveats, and history come after.

> Rejected: `Because the upstream API changed in v3 and we had trouble with the old retry
> logic, this now wraps the client and handles backoff.`
>
> Approved: `Sends a request with exponential backoff. Wraps the v3 client, which changed its
> retry semantics.`

**One instruction per sentence, imperative first, in procedural comments.**

> Rejected: `Stop the worker and drain the queue before you restart, then verify the offset.`
>
> Approved:
> ```
> # 1. Stop the worker.
> # 2. Drain the queue.
> # 3. Restart the worker.
> # 4. Make sure the offset is correct.
> ```

**A warning goes before the step it applies to, never after.** This is the single highest-value
rule in the whole skill. A caution placed below a destructive command is read too late.

> Rejected:
> ```
> # Drop the schema and rebuild it.
> # Note: this deletes all customer data.
> ```
>
> Approved:
> ```
> # WARNING: this deletes all customer data. Take a backup first.
> # Drop the schema and rebuild it.
> ```

**Never let a docstring contradict the code.** A wrong comment is worse than no comment, and
precedence rule 1 means accuracy beats every constraint in this file.

---

## 4. Substitutions for code prose

Apply to comments, docstrings, and user-facing strings. **Do not apply to identifiers that
mirror an external API** — if the library's method is `terminate()`, your wrapper says
`terminate()`.

| Rejected | Approved |
|---|---|
| ensure, verify, confirm, validate | make sure |
| utilize | use |
| commence, initiate | start |
| terminate, cease | stop |
| accomplish, execute, perform | do |
| obtain, acquire | get |
| require, necessitate | need |
| prior to | before |
| subsequent to, following | after |
| in order to | to |
| in the event that | if |
| is able to, has the ability to | can |
| due to the fact that | because |
| approximately | about |
| additional | more |

**Delete rather than replace** — these add length without meaning: `basically`, `essentially`,
`actually`, `really`, `very`, `quite`, `simply`, `just`, `obviously`, `clearly`, `of course`,
`it should be noted that`.

This is a working aid built from commonly cited substitutions. It is **not** the ASD-STE100
dictionary, which holds roughly 900 entries and is ASD's copyrighted content. For the full
table, see `skills/nfc/references/style-rules.md` section 5 if that skill is present. For the
authoritative list, obtain the official specification free of charge from
<https://www.asd-ste100.org/STE_downloads.html>.

---

## 5. What STE never touches

- Code syntax, keywords, and operators.
- Quoted or reproduced material — code you cite in a review, command output, log excerpts.
- Names fixed outside your control: external APIs, protocol constants, database columns.
- Existing identifiers, unless the user asked for a rename.
- Test fixture data and sample payloads.
