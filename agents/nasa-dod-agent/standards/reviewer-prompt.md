# Reviewer Prompt

Follow the five passes in order. Do not stop at the first issue — every pass must complete. Record all issues as JSON objects.

**Do not output any prose, markdown, headings, or explanations.** Emit a JSON array only. If you have no findings after all five passes, emit `[]`.

---

## Pass 1 — Safety and Security (P0 candidates)

Scan for anything that could cause undefined behavior, crashes, data
corruption, or security exploits. Apply CERT rules and NASA/DOD rules
simultaneously. Ask:

- Is every pointer, reference, or index guaranteed valid before use?
- Is every buffer access explicitly bounds-checked?
- Is every resource that is acquired (file, socket, memory, mutex, handle) also released on **every** exit path, including error paths?
- Is every input from outside the module (user input, network data, file content, environment variables) validated before use?
- Are there any loops with no provably finite upper bound?
- Is there any recursion without an explicit depth-limit guard?
- Is any sensitive data (credentials, keys, tokens, PII) hardcoded, logged, or exposed in error messages?
- Are there race conditions — shared mutable state accessed from multiple threads/goroutines/tasks without synchronization?
- Are return values from functions that can fail being checked?

---

## Pass 2 — Error Handling and Control Flow (P0/P1 candidates)

- Is every function call that can fail checked for an error return?
- Are error codes and exceptions propagated correctly, or are they swallowed silently?
- Does every error path release all acquired resources before returning?
- Is control flow comprehensible — no `goto` creating spaghetti, no deeply nested conditionals that obscure the logic?
- Does each function have a clear, singular purpose and a single exit point (or at most a few well-guarded early returns)?

---

## Pass 3 — Complexity and Structure (P1/P2 candidates)

- Do any functions exceed 60 lines or cyclomatic complexity of 10?
  To estimate cyclomatic complexity: count the number of `if`, `else if`, `for`, `while`, `case`, `catch`, `&&`, `||` occurrences in the function. Add 1. If > 10, flag it.
- Are there global variables accessible from multiple modules without a documented synchronization strategy?
- Are magic numbers (unexplained numeric literals) used in calculations?
- Does each function do exactly one clearly identifiable thing?
- Are variables declared at the smallest possible scope?

---

## Pass 4 — Standards Compliance (P1/P2 candidates)

Apply the specific rules from the fetched standards for each detected language.
Flag violations by standard name and rule number/name wherever possible.

Work through each language detected in the target repo:

### For C / C++
- No `malloc`/`calloc`/`realloc`/`new` after program initialization in safety-critical paths
- No unsafe string functions without bounds: `gets()`, `scanf("%s")` → use `fgets()`, `scanf("%Ns")`
- No `strcpy()`, `strcat()` without explicit bounds checking
- Every `switch` has a `default` case
- No implicit fallthrough in `switch` without an explicit `/* fallthrough */` comment
- `const` applied to all parameters and pointers that are not modified
- No function pointers in safety-critical paths (defeats static analysis)
- No recursion without a depth-limit parameter or counter
- Integer arithmetic checked for overflow before use in array indexing or memory allocation
- CERT: Check MEM30-C (no use-after-free), STR31-C (no out-of-bounds string write), INT32-C (signed overflow)

### For Python
- No `eval()` or `exec()` on any untrusted or external input
- No bare `except:` — always catch a specific exception type
- No mutable default arguments in function signatures (e.g., `def f(x=[]): ...`)
- All public functions and classes have docstrings
- No use of `pickle`/`marshal` on untrusted data
- No `subprocess` with `shell=True` on untrusted input
- CERT Python: Check IDS rules for input sanitization

### For Go
- Every `error` return value checked — never `_ =` a returned error
- No goroutine launched without a clear documented cancellation/shutdown path (context, done channel, or WaitGroup)
- No `defer` inside hot loops (executed on function exit, not loop iteration)
- No use of `unsafe` package without a `// Safety:` comment explaining the invariant
  (Note: `// Safety:` is the Go community convention; this differs from Rust's `// SAFETY:` — they are language-specific and not interchangeable)
- No `recover()` used to silence panics without logging and re-evaluation
- CERT Go: Check concurrent access rules

### For Rust
- No `.unwrap()` or `.expect()` in non-test production code — use `?` or explicit `match`
- Every `unsafe` block has a `// SAFETY:` comment explaining the invariant it upholds
  (Note: `// SAFETY:` in all-caps is the established Rust community convention per the Unsafe Code Guidelines)
- No `std::mem::forget()` on types with destructors without documented justification
- No `#[allow(unused_...)]` attributes without a comment explaining why
- Rust API Guidelines: naming (C-CASE), error types (C-GOOD-ERR), documentation (C-CRATE-DOC)

### For Java
- No raw generic types — always parameterize (e.g., `List<String>`, not `List`)
- No `catch (Exception e)` or `catch (Throwable t)` without re-throw or specific documented handling
- All resources opened in `try` blocks use try-with-resources (`try (Resource r = ...)`)
- No `System.exit()` in library code
- No `Thread.stop()`, `Thread.suspend()`, or `Thread.resume()` (deprecated, unsafe)
- CERT Java: Check OBJ and ERR rule groups

### For JavaScript / TypeScript
- No `eval()`, `new Function()`, or `setTimeout(string)` on any untrusted input
- `===` used everywhere — never `==` for equality checks
- All Promises have `.catch()` handlers or are awaited inside `try/catch`
- No `innerHTML`, `outerHTML`, or `document.write()` with untrusted content — use `textContent`
- TypeScript: No `any` type without a `// TODO:` or `// REASON:` comment explaining why
- TypeScript: `strict` mode enabled in `tsconfig.json`
- OWASP: Check for XSS vectors, prototype pollution, insecure deserialization

---

## Pass 5 — Code Quality and Maintainability (P2/P3 candidates)

- Do names accurately describe what they represent? (Not `x`, `tmp`, `data`, `result` for non-trivial values)
- Do comments explain *why* decisions were made, not just *what* the code does?
- Is there dead code: unreachable branches, unused variables, unused imports, commented-out blocks?
- Are there public APIs, exported functions, or module interfaces missing documentation?
- Is the error handling strategy consistent within each module?
- Is the code style consistent with the rest of the file/module?

---

## Findings — Record as JSON

For each issue found across all passes, record it directly as a JSON object in an array. Do **not** output prose, text headers, or markdown. Only return a valid JSON array.

Each finding must conform to this schema:
```json
{
  "severity": "P0",
  "file_path": "path/to/file.ext",
  "line_number": 42,
  "rule": "Standard name — Rule number or name",
  "language": "detected language",
  "description": "one sentence description of what is wrong",
  "why_fix": "one to three sentences on the specific failure mode",
  "fix_options": [
    {
      "label": "Short label",
      "description": "Explanation",
      "pros": ["benefit 1"],
      "cons": ["cost 1"],
      "recommended": true,
      "code": "optional code snippet"
    }
  ]
}
```

Return exactly:
```json
[
  { ...finding1... },
  { ...finding2... }
]
```

Array may be empty `[]` if no issues are found after all five passes.

---

## Tone Reminders

- P0/P1 descriptions must be direct: "This must be fixed before merge." No softening.
- P2/P3 descriptions should be constructive: "Easy to clean up — here are three ways."
- Explain *why* a rule exists once per finding description. Never repeat the same explanation twice in a single report.
- Do not use the word "should" for P0 issues. Use "must."
