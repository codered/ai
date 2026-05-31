# Document Templates

Exact templates for each spec document. Copy and fill in — don't deviate from structure unless a section genuinely doesn't apply (mark it "N/A — [reason]" rather than deleting it).

---

## `00_overview.md` — Architecture & System Overview

```markdown
# System Overview: [Project Name]

## What This System Does
[2–4 sentence plain-English description. What problem does it solve? Who uses it?]

## Tech Stack
| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Language | | | |
| Runtime | | | |
| Web framework | | | |
| Database | | | |
| Cache | | | |
| Queue / messaging | | | |
| Auth | | | |
| Deployment | | | |

## Entry Points
| Entry Point | File | Purpose |
|-------------|------|---------|
| | | |

## High-Level Architecture
[ASCII diagram or prose description of how the major components connect.
Include: client → API layer → service layer → data layer → external services]

```
[Component A] ──► [Component B] ──► [Database]
                       │
                       ▼
               [External API]
```

## Module Map
| Module / Directory | Purpose |
|-------------------|---------|
| | |

## Data Flow Summary
[How does a typical request/operation flow through the system end-to-end?
Describe at least one primary happy-path scenario.]

## External Integrations
| Service | Purpose | Protocol | Auth method |
|---------|---------|----------|------------|
| | | | |

## Environment & Configuration
| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| | | | |

## Build & Run
[How to install dependencies, build, and run the system. Commands if determinable.]

## Test Suite
- Framework: [e.g. pytest, jest, go test]
- Coverage areas: [what's tested]
- Notable gaps: [what's not tested]
```

---

## `01_requirements.md` — Functional & Non-Functional Requirements

```markdown
# Requirements

> These requirements are **inferred from the codebase**. They represent what the code actually does,
> not what it was originally designed to do. Mark anything uncertain as [INFERRED] or [ASSUMED].

## Functional Requirements

### [Feature Area 1]
- FR-001: [The system shall ...]
- FR-002: [The system shall ...]

### [Feature Area 2]
- FR-010: [The system shall ...]

## Non-Functional Requirements

### Performance
- NFR-001: [e.g. "Supports up to N concurrent connections [INFERRED from thread pool size]"]

### Reliability
- NFR-010: [e.g. "Retries failed requests up to 3 times with exponential backoff"]

### Security
- NFR-020: [e.g. "All API endpoints require a valid JWT token"]

### Scalability
- NFR-030: [e.g. "Stateless request handling — no server-side session storage"]

### Compatibility
- NFR-040: [e.g. "Requires Python 3.10+ due to use of structural pattern matching"]

## Out of Scope
[Things the codebase explicitly does NOT do, based on evidence in the code.]
```

---

## `02_assumptions.md` — Assumptions

```markdown
# Assumptions

Things the codebase assumes to be true about its environment, inputs, callers, or infrastructure.
A reimplementation must preserve these assumptions or explicitly document when it breaks them.

## Environment Assumptions
- [e.g. "Assumes a PostgreSQL-compatible database is available at DATABASE_URL"]
- [e.g. "Assumes the host has at least X GB of memory [INFERRED from in-memory cache sizing]"]

## Input Assumptions
- [e.g. "Assumes all incoming timestamps are UTC"]
- [e.g. "Assumes user IDs are non-negative integers"]

## Caller / Client Assumptions
- [e.g. "Assumes callers will always send Content-Type: application/json"]
- [e.g. "Assumes API clients handle 429 rate-limit responses with backoff"]

## Data Assumptions
- [e.g. "Assumes the users table always has at least one admin row"]

## Ordering / Concurrency Assumptions
- [e.g. "Assumes events are processed in-order per user ID"]

## External Service Assumptions
- [e.g. "Assumes the payment gateway responds within 5 seconds"]

## Unresolved Assumptions
[Any assumption that could not be confirmed — mark source and why it's uncertain.]
- [UNRESOLVED] [description] — Source: [file:line]
```

---

## `03_limitations.md` — Limitations & Known Issues

```markdown
# Limitations & Known Issues

## Hard Limits
| Limit | Value | Location | Notes |
|-------|-------|----------|-------|
| [e.g. Max file upload size] | [e.g. 10MB] | [file:line] | [hardcoded / configurable] |

## Unhandled Cases
- [e.g. "No handling for concurrent writes to the same record — last write wins"]
- [e.g. "Empty input arrays cause a divide-by-zero in stats.py:42"]

## Known Bugs / TODOs
[Extract all TODO, FIXME, HACK, XXX comments from the codebase]
| Tag | File | Line | Description |
|-----|------|------|-------------|
| TODO | | | |
| FIXME | | | |

## Deprecated Code
- [List any functions/modules marked deprecated or clearly abandoned]

## Scalability Limits
- [e.g. "In-process cache does not work across multiple instances"]
- [e.g. "Database queries are not paginated — full table scans on large datasets"]

## Security Gaps
- [e.g. "No CSRF protection on state-mutating endpoints"]
- [e.g. "User-supplied filenames are not sanitized before disk write"]

## Missing Features (Stubbed or Placeholder)
- [e.g. "Email notification module returns early with a stub — not implemented"]
```

---

## `04_data_models.md` — Data Models & Schemas

```markdown
# Data Models

## [ModelName]
**Source**: [file path]
**Storage**: [e.g. PostgreSQL table `users`, in-memory dict, Redis key pattern]

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| id | uuid | yes | auto | Primary key |
| ... | | | | |

**Relationships**:
- belongs_to: [OtherModel] via [field]
- has_many: [OtherModel] via [foreign key]

**Invariants**:
- [e.g. "email must be unique across all users"]
- [e.g. "status must be one of: pending, active, archived"]

**Lifecycle**:
[How is this entity created, updated, deleted? Any soft-delete pattern?]

---

_(Repeat for each significant model / schema / type)_

## Enums & Constants
| Name | Values | Used In |
|------|--------|---------|
| | | |

## External Schema Contracts
[Any JSON schemas, protobuf definitions, or API response shapes this code depends on]
```

---

## `05_api_contracts.md` — Public API & Interface Contracts

```markdown
# API Contracts

## HTTP API (if applicable)

### [GET/POST/...] `/path/to/endpoint`
**Purpose**: [what it does]
**Auth required**: [yes/no — method]

**Request**:
| Field | Location | Type | Required | Description |
|-------|----------|------|----------|-------------|
| | query/body/header | | | |

**Response** (200):
```json
{
  "field": "type — description"
}
```

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | [when] |
| 401 | [when] |
| 404 | [when] |
| 500 | [when] |

---

## Internal Function / Module API

### `functionName(param1: Type, param2: Type) → ReturnType`
**Module**: [file path]
**Purpose**: [what it does]
**Side effects**: [none / list them]
**Raises**: [exception type — when]

| Param | Type | Description |
|-------|------|-------------|
| param1 | | |

---

## Events / Messages (if applicable)
| Event Name | Producer | Consumer | Payload Schema |
|-----------|---------|---------|---------------|
| | | | |

## CLI Commands (if applicable)
| Command | Args | Description |
|---------|------|-------------|
| | | |
```

---

## `06_<module>.md` — Per-Module Spec

```markdown
# Module: [ModuleName]

**Location**: `path/to/module/`
**Purpose**: [one sentence]
**Depends on**: [internal modules it imports]
**Depended on by**: [modules that import this one]

## Responsibilities
- [bullet list of what this module owns]

## Public Interface
[Use the function/class signature format from `05_api_contracts.md`]

## Key Internal Logic

### [Algorithm or process name]
[Step-by-step description of the logic. Language-agnostic. Use numbered steps for sequences.]

1. [Step one]
2. [Step two]
   - If [condition]: [branch]
   - Otherwise: [branch]
3. [Step three]

### [Another significant piece of logic]
[...]

## State & Data
[Any internal state this module maintains. How is it initialized? When is it mutated? Thread-safe?]

## Configuration
| Key | Default | Effect |
|-----|---------|--------|
| | | |

## Error Handling
[How does this module handle errors? What does it catch vs propagate?]

## Assumptions
[What must be true for this module to work correctly?]

## Limitations
[Known gaps, hardcoded values, unhandled cases specific to this module]

## Test Coverage
[What tests exist for this module? What's covered? What's missing?]
```

---

## `NN_cross_cutting.md` — Cross-Cutting Concerns

```markdown
# Cross-Cutting Concerns

## Authentication & Authorization
[How identity is established, what tokens/sessions are used, how permissions are checked]

## Error Strategy
[Global error handling: where errors are caught, how they're formatted, what gets surfaced to callers vs swallowed]

## Logging & Observability
| What gets logged | Level | Format | Destination |
|-----------------|-------|--------|------------|
| | | | |

## Concurrency Model
[Async/sync, thread pools, worker processes, locks, queues — describe the concurrency model]

## Caching Strategy
[What is cached, where, TTL, invalidation strategy]

## Data Validation
[Where and how inputs are validated — at the API boundary, in the service layer, in the DB layer?]

## Security Patterns
[Input sanitization, secrets management, network boundaries, encryption in transit/at rest]

## Rate Limiting & Throttling
[Any rate limiting — where it's enforced, limits, response behavior]

## Internationalization
[Any i18n/l10n support, or assumed locale]
```
