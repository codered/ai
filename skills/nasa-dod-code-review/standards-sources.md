# Standards Sources

This file lists the authoritative sources the agent fetches and digests before
performing a code review. Fetch all Universal sources on every run. Fetch
language-specific sources only for languages detected in the target repo.

Cache all fetched content in-session — do not re-fetch the same URL twice.

If a URL is unreachable, note it in the report header as:
`⚠️ Standards source unavailable: [URL] — review continues with in-memory knowledge.`

---

## Universal (fetch on every run)

### NASA Power of Ten Rules
- **URL:** https://spinroot.com/gerard/pdf/P10.pdf
- **What to extract:** All 10 rules with their rationale. Apply to every language regardless of paradigm.
- **Key rules to internalize:**
  1. No goto, setjmp, longjmp
  2. All loops must have a fixed upper bound — provably terminating
  3. No dynamic memory allocation after initialization
  4. Functions must be no longer than ~60 lines (one page)
  5. Minimum 2 assertions per function
  6. Data objects declared at smallest possible scope
  7. Return value of non-void functions must be checked; parameters validated
  8. No preprocessor use beyond includes and simple macros (C-specific but principle applies)
  9. Restrict pointer use — no more than 1 level of dereferencing; no function pointers
  10. Warnings treated as errors; static analysis tools run on all code

### SEI CERT Coding Standards (index)
- **URL:** https://wiki.sei.cmu.edu/confluence/display/seccode/SEI+CERT+Coding+Standards
- **What to extract:** Use as the index to navigate to language-specific standards below. The universal principles to extract from this page: input validation before use, no reliance on undefined behavior, all resource acquisitions must be released on every exit path.

### DOD Joint Strike Fighter AV C++ Coding Standards (JSF AV)
- **URL:** https://www.stroustrup.com/JSF-AV-rules.pdf
- **What to extract:** All numbered AV rules. The following apply universally regardless of language:
  - AV Rule 14: Error-handling strategy must be defined for the project
  - AV Rule 17: No reliance on undefined or unspecified behavior
  - AV Rule 24: No magic numbers — use named constants
  - AV Rule 58: Every function returns at most one value through its return mechanism
  - AV Rule 59: Functions shall have a single point of exit at the end
  - AV Rule 126: Every switch must have a default case
  - AV Rule 142: All variables initialized before use
  - AV Rule 143: Variables declared in the smallest possible scope
  - AV Rule 166–171: Assertions, error handling, exception safety

### NASA/JPL Institutional Coding Standard for C
- **URL:** https://lars-lab.jpl.nasa.gov/JPL_Coding_Standard_C.pdf
- **What to extract:** All rules. The following apply universally:
  - No dynamic memory allocation after program initialization
  - All loops must have an explicit upper bound
  - No recursion unless bounded by a depth counter
  - Avoid function pointers (they defeat static analysis)
  - One point of return per function preferred
  - All inputs validated at module boundary
  - All error returns checked

---

## Language-Specific

### C / C++
Fetch in addition to Universal sources above (which are already C/C++-heavy).

- **CERT C Coding Standard**
  - URL: https://wiki.sei.cmu.edu/confluence/display/c/SEI+CERT+C+Coding+Standard
  - Extract: All rules, especially MEM (memory management), STR (strings), INT (integers), ERR (error handling), FLP (floating point), SIG (signals), ENV (environment)

- **CERT C++ Coding Standard**
  - URL: https://wiki.sei.cmu.edu/confluence/display/cplusplus/SEI+CERT+C%2B%2B+Coding+Standard
  - Extract: All rules, especially MEM (memory), EXP (expressions), ERR (exceptions), DCL (declarations), CTR (containers)

- **MISRA C (public summary)**
  - URL: https://www.misra.org.uk/misra-c/
  - Extract: Free rule summaries. Key mandatories: no implicit type conversions, no unreachable code, all variables initialized, no recursion, no dynamic allocation.

### Python
- **CERT Python Coding Standard**
  - URL: https://wiki.sei.cmu.edu/confluence/display/python/SEI+CERT+Python+Coding+Standard
  - Extract: All rules, especially IDS (input/data sanitization), ENV (environment), MSC (miscellaneous)

- **NASA Python Coding Conventions**
  - URL: https://github.com/nasa/NASA-SW-VnV-Std-18011-Python
  - Extract: Naming conventions, module structure, documentation requirements, static analysis tool requirements

### Go
- **SEI CERT Go Coding Standard**
  - URL: https://wiki.sei.cmu.edu/confluence/display/golang/SEI+CERT+Go+Coding+Standard
  - Extract: All rules, especially concurrency (goroutines, channels), error handling, memory safety

- **Go Code Review Comments (official)**
  - URL: https://github.com/golang/go/wiki/CodeReviewComments
  - Extract: Error handling idioms, naming conventions, interface design, concurrency patterns

### Rust
- **Rust API Guidelines**
  - URL: https://rust-lang.github.io/api-guidelines/
  - Extract: Naming (C-CASE), documentation (C-CRATE-DOC), error handling (C-GOOD-ERR), safety (C-SAFE)

- **SEI CERT Rust (where applicable)**
  - URL: https://wiki.sei.cmu.edu/confluence/display/rust
  - Extract: Any published rules. If page is sparse, rely on Rust API Guidelines and Unsafe Code Guidelines.

- **Rust Unsafe Code Guidelines**
  - URL: https://rust-lang.github.io/unsafe-code-guidelines/
  - Extract: Requirements for `unsafe` blocks — every unsafe block must have an explicit safety comment justifying the invariant maintained.

### Java
- **SEI CERT Oracle Coding Standard for Java**
  - URL: https://wiki.sei.cmu.edu/confluence/display/java/SEI+CERT+Oracle+Coding+Standard+for+Java
  - Extract: All rules, especially OBJ (objects), MET (methods), ERR (errors), THI (threads), IDS (input), SEC (security)

- **Sun/Oracle Java Code Conventions (historical reference)**
  - URL: https://web.archive.org/web/20111018064908/http://java.sun.com/docs/codeconv/
  - Note: No official DOD Java coding standard exists. Apply JSF AV universal rules and SEI CERT Java as the primary standards. This historical reference covers naming and file organization conventions only.

### JavaScript / TypeScript
- **SEI CERT JavaScript Coding Standard**
  - URL: https://wiki.sei.cmu.edu/confluence/display/js/SEI+CERT+JavaScript+Coding+Standard
  - Extract: All rules, especially ENV (environment), DOM (DOM manipulation), STR (strings)

- **OWASP JavaScript Security Cheat Sheet**
  - URL: https://cheatsheetseries.owasp.org/cheatsheets/JavaScript_Security_Cheat_Sheet.html
  - Extract: XSS prevention (no innerHTML with untrusted input), eval prohibition, CSP, dependency security

- **OWASP TypeScript Cheat Sheet**
  - URL: https://cheatsheetseries.owasp.org/cheatsheets/TypeScript_Security_Cheat_Sheet.html
  - Extract: Type safety enforcement, `any` prohibition, strict mode requirements

---

## Fallback — Language Not Listed

If the target repo uses a language not covered above (e.g., Swift, Kotlin, Ruby,
C#, Bash, Scala), apply all Universal standards. Do not halt or skip the review.

Note in the report header:
> ⚠️ No language-specific standards entry found for [language] — universal NASA/DOD
> standards applied. Consider contributing a language-specific section to this skill.
