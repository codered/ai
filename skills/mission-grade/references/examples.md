# Worked Examples

Companion to `skills/mission-grade/SKILL.md`. Three end-to-end runs: one write, one refactor,
one review.

---

## Example 1 — Writing a feature

**Request:** "Add a rate limiter to the upload endpoint. 10 uploads per minute per tenant."

**RED.** The test name and its failure message are artifact prose, so `strict` binds them.

```python
def test_rate_limiter_blocks_the_eleventh_upload_in_one_minute():
    limiter = RateLimiter(limit=10, window_seconds=60)
    for _ in range(10):
        assert limiter.allow("tenant-a") is True
    assert limiter.allow("tenant-a") is False, "The limiter must refuse the 11th upload."
```

Run it. Show the output:

```
E   NameError: name 'RateLimiter' is not defined
```

That is a failure for the right reason. A test that fails on a typo proves nothing.

**GREEN.** Minimum code. Identifiers checked as they are chosen: `RateLimiter`, `allow`,
`window_seconds` — each 1 to 2 concept words, and `tenant` is already the module's term.

```python
class RateLimiter:
    """Limits how many attempts one tenant can make in a sliding time window.

    `limit` is the maximum number of attempts. `window_seconds` is the length of
    the window in seconds. Both must be positive.
    """

    def __init__(self, limit: int, window_seconds: int) -> None:
        assert limit > 0, "limit must be positive"
        assert window_seconds > 0, "window_seconds must be positive"
        self._limit = limit
        self._window_seconds = window_seconds
        self._hits: dict[str, list[float]] = {}

    def allow(self, tenant: str) -> bool:
        assert tenant, "tenant must not be empty"
        now = time.monotonic()
        cutoff = now - self._window_seconds
        recent = [t for t in self._hits.get(tenant, []) if t > cutoff]
        if len(recent) >= self._limit:
            self._hits[tenant] = recent
            return False
        recent.append(now)
        self._hits[tenant] = recent
        return True
```

Power of Ten as applied: bounded loop (rule 2), 14 lines (rule 4), three assertions (rule 5),
inputs validated (rule 7).

**REFACTOR.** Docstring in `clear` — conclusion first, no idioms, no emoji:

```python
    def allow(self, tenant: str) -> bool:
        """Reports whether an upload is permitted, and records it only when it is.

        Returns True when the tenant made fewer than `limit` attempts in the last
        `window_seconds`. Returns False otherwise, and does not record the attempt.

        The window slides. It does not reset on a fixed boundary.
        """
```

The error string the endpoint returns is `strict` — what failed, why, what to do:

```python
raise RateLimitExceeded(
    f"The limiter refused the upload. Tenant {tenant} reached {limit} uploads "
    f"in {window_seconds} seconds. Retry after {retry_after} seconds."
)
```

**COMMIT.** `clear`, imperative subject, explains why:

```
feat(uploads): limit each tenant to 10 uploads per minute

A single tenant could saturate the upload workers and delay every other
tenant. The limiter uses a sliding window, so a burst at a minute
boundary cannot pass twice the limit.
```

---

## Example 2 — Refactoring

**Request:** "Split this 90-line handler up."

The module already uses these terms: `subscription`, `proration`, `invoice`. Existing names
include `compute_customer_subscription_proration_credit_amount` — 5 concept words, over the cap.

**What the skill does:** extracts by phase, giving each helper a name built from the module's
existing terms.

```python
def handle_subscription_change(request):
    """Computes the invoice for a subscription change."""
    change = _parse_subscription_change(request)
    credit = _compute_proration_credit(change)
    invoice = _build_invoice(change, credit)
    return invoice
```

**What the skill does not do:** rename
`compute_customer_subscription_proration_credit_amount`. It exceeds the concept-word cap, and
it is untouched by this change. Consistency beats cluster length, and a rename is its own pull
request. The skill does not mention the rename as an option unless the user asks.

Tests exist before any of this moves. A refactor without tests is a rewrite.

---

## Example 3 — Reviewing

**Input:** a pull request adding an admin endpoint, with a hardcoded token and a docstring
reading `"Nukes the tenant's data 💥 — no takebacks!"`.

**The report.** Conversation side, so emoji are required and the prose explains normally:

> Nice work threading the tenant scope through the deletion path — the cascade order is right,
> and the integration test covers the orphaned-rows case properly.
>
> ⚠️ **Do this first:** `ADMIN_TOKEN = "at_live_9f2b…"` is committed at `admin/routes.py:14`.
> That token is in git history permanently and must be treated as compromised. Revoke it at the
> provider now, before reading the rest of this review.
>
> 🔴 **Gate status: BLOCKED** — 2 blockers, 1 major, 1 nit.
>
> **Blocker — DoD baseline #4 (secrets management)** — the admin token is hardcoded, so anyone
> with repository read access holds production admin rights.
>
> **Options:**
> 1. **Rotate, then load from the environment (recommended):** revoke now, issue a new token,
>    read `ADMIN_TOKEN` at startup, and fail fast when it is missing.
> 2. **Rotate, then pull from your secret manager:** better if you already run Vault or AWS
>    Secrets Manager, since it gets you rotation for free.
> 3. **Rotate, then use a gitignored env file:** cheapest and weakest. Local development only.
>
> Option 1 regardless — the revoke step cannot wait for the design discussion.
>
> **Blocker — Gate 6 (contradictory docstring)** — the docstring says the deletion is
> irreversible, but the implementation writes to `deleted_tenants` and the runbook restores from
> it. A caller reading this docstring will refuse a legitimate restore request.
>
> **Options:**
> 1. **Correct the docstring (recommended):** state that rows move to `deleted_tenants` and
>    name the retention window.
> 2. **Correct it and link the restore runbook:** better if support staff read this file.
> 3. **Make the code match the docstring:** only if the retention behavior was unintended.
>
> **Major — Power of Ten #7 (input validation)** — `delete_tenant` does not validate
> `tenant_id` before it reaches the query builder. … [options follow]
>
> **Nit — Gate 6 (emoji and idiom in shipped prose)** — 💥 and "no takebacks" render
> inconsistently across terminals and do not survive translation.

Note the split. The ⚠️ and 🔴 in the report are required. The 💥 in the docstring is a finding.
Same document, opposite rules, because one is the conversation and one is the artifact.
