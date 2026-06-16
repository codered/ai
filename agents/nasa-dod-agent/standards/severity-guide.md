# Severity Guide

Use this guide to classify every finding. When in doubt between two levels,
choose the higher severity. Safety-critical and security contexts should
always bias toward higher severity.

---

## P0 / Critical — BLOCKS MERGE

**Definition:** A defect that poses a direct risk to system safety, security,
reliability, or data integrity. In a deployed system, this class of issue can
cause crashes, data loss, exploits, deadlocks, infinite loops, or undefined
behavior with no recovery path.

**Decision criteria — any one of these makes a finding P0:**
- Undefined behavior: buffer overflow, integer overflow/underflow, use-after-free, null pointer dereference, out-of-bounds access
- Unbounded loop or recursion with no guaranteed termination
- Dynamic memory allocation after initialization in a safety-critical execution path
- Missing error handling on a code path that can fail and whose failure is not obviously harmless
- Hardcoded secrets, credentials, API keys, or cryptographic material
- Resource acquired (file, socket, memory, lock, handle) but never released on one or more exit paths
- Race condition on shared mutable state with no synchronization
- User-supplied or external input used without validation or sanitization in a sensitive context (SQL, HTML, shell, file path, etc.)
- Calling a function whose return value signals failure, and ignoring that value, in a context where failure has real consequences

**Examples:**
- `malloc()` called inside a flight-critical loop with no paired `free()` on the error path
- `strcpy()` receiving a user-supplied string with no bounds check
- A mutex locked inside an interrupt handler with no acquisition timeout
- An unbounded `while(true)` with a break condition that can never be satisfied
- A database query constructed by string concatenation with unescaped user input
- A hardcoded `password = "admin123"` in a config module

**Tone for P0 findings:** Assertive, no hedging.
> "🔴 P0/Critical — This blocks merge. [explanation of failure mode]. This is non-negotiable."

---

## P1 / Major — Must be resolved before next release

**Definition:** A significant violation of coding standards that meaningfully
increases risk, reduces auditability, or creates conditions that make P0
defects more likely in future changes. Not immediately catastrophic but
cannot be deferred indefinitely.

**Decision criteria — any one of these makes a finding P1:**
- Function exceeds 60 lines or has cyclomatic complexity greater than 10
- Global mutable state accessed from multiple modules without documented synchronization strategy
- Magic numbers used in safety-relevant or business-critical calculations
- Error return value explicitly discarded (`(void)result`, `_ =`, bare `except:`) in non-trivial context
- Missing or severely inadequate test coverage on a critical execution path
- `goto` used in a way that creates non-obvious or unstructured control flow
- Non-deterministic behavior (randomness, time-of-day dependency) in a context that requires determinism
- An API contract stated in a comment but not enforced by the code
- `unsafe` blocks (Rust), `unsafe.Pointer` (Go), or inline assembly used without a documented safety justification comment

**Examples:**
- A 180-line function with 18 conditional branches and zero unit tests
- `errno` not checked after a `read()` or `write()` syscall in a data pipeline
- `#define TIMEOUT 3000` used in 12 places with no named constant and no unit comment
- A goroutine launched with no documented cancellation/shutdown path

**Tone for P1 findings:** Direct and clear.
> "🟠 P1/Major — This needs to be fixed before the next release. [explanation]. Here are three ways to address it:"

---

## P2 / Minor — Should be fixed this sprint

**Definition:** A code quality or maintainability issue that doesn't pose
immediate risk but violates standards and will complicate future work or make
the codebase harder to audit.

**Decision criteria:**
- Naming doesn't follow language conventions or project patterns (unclear abbreviations, misleading names)
- Comment describes *what* the code does rather than *why* — especially for non-obvious choices
- Dead code: unreachable branches, unused variables, unused imports, commented-out code blocks
- A function or method does more than one clearly identifiable thing (SRP violation)
- Inconsistent error handling strategy within a single module
- Missing documentation for a public API, exported function, or module interface
- Overly deep nesting (more than 3–4 levels) that could be flattened with early returns
- Shadowed variables or identifiers that could confuse readers or tooling

**Examples:**
- `int x` used as a meaningful loop counter in a non-trivial algorithm
- A public Python function with no docstring
- `if (flag == true)` instead of `if (flag)` in an idiomatic language context
- A 6-level nested conditional that could be expressed as early returns

**Tone for P2 findings:** Helpful and constructive.
> "🟡 P2/Minor — Easy to clean up. [what and why]. Three options:"

---

## P3 / Advisory — No action required

**Definition:** A best-practice observation. Flagged for awareness; the
developer may consciously choose to address it or defer it. P3 findings
never block and are not tracked for resolution.

**Decision criteria:**
- An alternative approach would be marginally cleaner but current code is correct and clear
- A style preference that is not enforced by the project's documented standards
- A performance micro-optimization that isn't relevant to current load
- A defensive assertion or guard that would be nice but isn't strictly necessary
- A refactoring opportunity that would improve readability but carries no risk

**Examples:**
- A `const` qualifier could be added to a function parameter that isn't modified
- A loop could be expressed more idiomatically using a standard library function
- An inline comment could be expanded to better explain an architectural decision

**Tone for P3 findings:** Light and optional.
> "🔵 P3/Advisory — Something worth knowing. [observation]. No action required, but here are some options if you'd like to refine it:"

---

## Classification Quick Reference

| Ask yourself | If yes → |
|---|---|
| Could this crash, corrupt data, or be exploited in production? | P0 |
| Does this ignore a failure that has real consequences? | P0 |
| Is secret or untrusted data used without validation? | P0 |
| Does this make P0 bugs significantly more likely? | P1 |
| Is a standard explicitly violated with measurable risk? | P1 |
| Is this hard to read, audit, or maintain, but not risky? | P2 |
| Is this a stylistic preference or optional improvement? | P3 |
| Still unsure between two levels? | Choose the higher one |
