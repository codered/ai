<p align="center">
  <h1 align="center">⚡ CodeRed AI Skills</h1>
  <p align="center"><b>Give your AI coding agent institutional knowledge — in five minutes, with zero config.</b></p>
</p>

<p align="center">
  <a href="https://github.com/codered/ai/stargazers"><img src="https://img.shields.io/github/stars/codered/ai?style=flat-square&color=yellow" alt="Stars"></a>
  <a href="https://github.com/codered/ai/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License"></a>
  <a href="https://github.com/codered/ai/tree/main/skills"><img src="https://img.shields.io/badge/skills-8-brightgreen?style=flat-square" alt="Skills"></a>
  <img src="https://img.shields.io/badge/agents-Claude%20%C2%B7%20Cursor%20%C2%B7%20Copilot%20%C2%B7%20Gemini-lightgrey?style=flat-square" alt="Agent support">
</p>

---

<p align="center">
  <img src="assets/demo/nasa-dod-code-review/demo.gif" alt="The NASA/DOD Code Review skill catching an unbounded loop, citing the violated rule, offering three fix options, and blocking the merge" width="800">
  <br>
  <sub>The <a href="skills/nasa-dod-code-review/">NASA/DOD Code Review</a> skill catching a real Power-of-Ten violation — rule citation, fix options, and merge gate, all in one pass. (<a href="assets/demo/nasa-dod-code-review/demo.tape">regenerate with VHS</a>)</sub>
</p>

---

## Why this exists

Every new chat with your AI coding agent starts from zero. It doesn't know your team's review standards, your branching conventions, or the five-step process you always run before merging. So you re-explain it — every session, every project, in slightly different words, until the agent's behavior drifts from what you actually wanted.

**Skills fix that.** A skill is a focused set of markdown instructions that encodes a specific way of working — a review process, a planning workflow, an analysis format — once, precisely, so any agent that can read a file can run it the same way every time.

> [!NOTE]
> If your agent can read a file, it can use these skills. No frameworks, no SDK — and if you're on Claude Code, this repo doubles as a plugin marketplace for one-command installs.

---

## 🚀 Quickstart

### Claude Code (fastest)

This repo is also a Claude Code plugin marketplace, so you can install it directly — no cloning, no context-file edits. Skills then show up namespaced as `codered:<skill-name>` (e.g. `codered:nasa-dod-code-review`), exactly like `superpowers:brainstorming`.

```bash
/plugin marketplace add codered/ai
/plugin install codered@codered
```

Then just ask for what you need:

```
nasa-dod review
```

Claude Code resolves that to `codered:nasa-dod-code-review` and loads the skill automatically.

### Any other agent

**1. Clone the repo**

```bash
# Global install (available across all your projects)
git clone https://github.com/codered/ai ~/.codered

# Per-project install (lives alongside your code)
git clone https://github.com/codered/ai .codered
```

**2. Tell your agent where to find the skills**

Add one line to your agent's context file. The exact file depends on your agent — see [Installation](#-installation) for specifics.

```text
Skills are available at <path>/skills/. Load the SKILL.md in the relevant skill folder when asked to use a skill.
```

**3. Use a skill**

```
nasa-dod review
```

That's it.

---

## 📦 Skills

### 🔴 [NASA/DOD Code Review](skills/nasa-dod-code-review/)

Reviews your code against the same engineering standards used for flight software, defense systems, and mission-critical infrastructure.

Works in two modes — full codebase scan during development, diff-first during PR review. Critical findings block the merge. Every issue comes with three fix options, trade-offs included, and working code in your language.

> 📺 See it catch a real Power-of-Ten violation in the demo at the top of this README.

| | |
|---|---|
| **Trigger** | `nasa-dod review` · `nasa-dod dev review` · `nasa-dod pr review` |
| **Languages** | C/C++, Python, Go, Rust, Java, JavaScript/TypeScript |
| **Standards** | NASA Power of Ten · DOD JSF AV · SEI CERT · MISRA · OWASP |
| **Gate** | P0/Critical blocks merge · 2+ approvals to override on teams |

### 🛡️ [Applying NASA/DOD Coding Standards](skills/applying-nasa-dod-coding-standards/)

The companion to the review skill above — this one shapes code *as you write it*, rather than grading it after the fact. Applies the discipline behind flight software (NASA's "Power of Ten") and defense systems (DISA STIGs, CERT Secure Coding, NIST SSDF) to everyday production work, with TDD as the non-negotiable baseline: no production code without a failing test first.

<p align="center">
  <img src="assets/demo/applying-nasa-dod-coding-standards/demo.gif" alt="The skill opening with the Iron Law, writing a failing rate-limiter test first, watching it fail red, then writing the minimum code to turn it green" width="700">
</p>

| | |
|---|---|
| **Trigger** | Writing production code · reviewing a PR · refactoring safety-critical systems · setting standards for a new project |
| **Discipline** | TDD as the iron law — write the failing test, then the minimum code to pass, then refactor |
| **Rules** | Bounded loops · short functions · assertion density · minimal scope · input validation |
| **Standards** | NASA Power of Ten · DISA STIGs · CERT Secure Coding · NIST SSDF |

### 🤖 [Agent Team](skills/agent-team/)

Assembles a five-role engineering team inside any repository — PM, Developer, QA, Security, and DevOps. Each agent has a distinct persona, scope, and responsibilities. They coordinate through a shared memory system and a rolling pipeline that keeps work moving without bottlenecks.

The PM creates a phased plan with explicit gate criteria. The Dev agent implements using TDD and self-reviews with the NASA/DOD Code Review skill before handoff. QA and Security review each completed task while Dev moves forward. DevOps handles CI/CD, infra, and produces the final readiness gate before anything ships.

<p align="center">
  <img src="assets/demo/agent-team/demo.gif" alt="The agent team's rolling pipeline — Dev marks a task in_review and immediately starts the next one while QA and Security review in parallel, never blocking" width="700">
</p>

| | |
|---|---|
| **Trigger** | `init agent team` · `agent team` · `agent team status` |
| **Roles** | PM · Dev · QA · Security · DevOps |
| **Pipeline** | Rolling — Dev never blocks waiting on review |
| **Gate** | P0/P1 findings block task close · phase gates before advancing |

### 🔍 [Code Analyst](skills/code-analyst/)

Produces a structured Markdown analysis of any piece of code — function breakdowns, data flow, dependencies, and test case analysis — within a strict 2-minute time budget. Emits live status updates as it works so you always know where it is.

Covers purpose, parameters, return values, side effects, error conditions, and edge cases. Saves the result as `<filename>_analysis.md` when file tools are available. Designed for developers who need to quickly understand code they didn't write.

<p align="center">
  <img src="assets/demo/code-analyst/demo.gif" alt="The skill emitting live status updates while reading code, then producing a structured Markdown analysis with Overview, Parameters, and Edge Cases sections, and saving it to a file" width="700">
</p>

| | |
|---|---|
| **Trigger** | "analyze this code" · "explain what this does" · "document this function" · pasting code with no explanation |
| **Output** | Structured Markdown: overview, function breakdown, data flow, dependencies, test cases |
| **Time budget** | 120 seconds — pauses and asks to continue if the limit is reached |
| **Tone** | Plain language for developers who didn't write the code |

### 📐 [Codebase Spec](skills/codebase-spec/)

Reads an entire codebase and produces a multi-document specification suite thorough enough that an engineer — or an AI agent — can reimplement the whole thing in a different language with no access to the original source.

Works in five phases: orientation, ambiguity resolution, module-by-module analysis, cross-cutting concerns, and delivery. Outputs a `spec/` directory with numbered documents covering architecture, requirements, assumptions, limitations, data models, API contracts, per-module deep-dives, and cross-cutting concerns (auth, error handling, logging, concurrency, security). Designed for large codebases (100+ files) but works at any scale.

<p align="center">
  <img src="assets/demo/codebase-spec/demo.gif" alt="The skill walking through its five phases — orientation, ambiguity resolution, module analysis, cross-cutting concerns, delivery — then populating a spec/ directory with numbered documents" width="700">
</p>

| | |
|---|---|
| **Trigger** | "write a spec for this codebase" · "document this project" · "I want to migrate this" · "reverse engineer this" |
| **Output** | `spec/` directory — `00_overview.md` through `NN_cross_cutting.md` |
| **Scale** | Designed for 100+ file codebases; works at any size |
| **Gate** | Reimplementation completeness checklist before delivery |

### 🗣️ [Devil's Advocate](skills/devils-advocate/)

Challenges a request, design, plan, or position by actively hunting for logical gaps, hidden assumptions, missed edge cases, and unconsidered counter-framings — in a tone that's friendly yet firm. Doubles as a general-purpose debate partner for any topic, technical or not.

Triages every exchange as low-stakes or high-stakes first, and that single call drives everything downstream: how many rounds of pushback it runs, how direct its tone gets, and whether it replies in structured findings or natural conversation. It's advisory only — it never blocks anything, and it never re-raises a concern you've already closed.

<p align="center">
  <img src="assets/demo/devils-advocate/demo.gif" alt="The skill auto-offering to challenge a plan to remove a cache layer, then — once accepted — raising a hidden assumption and a missed edge case in its structured high-stakes findings format" width="700">
</p>

| | |
|---|---|
| **Trigger** | "play devil's advocate" · "poke holes in this" · "challenge my thinking" · "steelman the other side" · any general debate request |
| **Categories** | Logical/reasoning gaps · hidden assumptions · missed edge cases · counter-framings |
| **Pushback** | 1 mention (low-stakes) · up to 3 rounds (high-stakes), then defers either way |
| **Output** | Conversational prose (low-stakes/debate) · structured findings list (high-stakes/design review) |

### 📚 [Teach Me](skills/teach-me/)

Turns "I want to learn X" into a self-contained, multi-chapter course written straight to disk. Asks what you want to learn, how deep to go (beginner/intermediate/advanced), and your background — proposes a chapter outline you can adjust before anything is written, then generates markdown chapters with diagrams, worked examples, and quizzes, plus a separate answer key with reasoning, and a combined PDF when pandoc is available.

<p align="center">
  <img src="assets/demo/teach-me/demo.gif" alt="The teach-me skill running the intake flow, presenting a 6-chapter outline for approval, then writing the first chapter with its quiz — with ANSWERS.md updated in the same pass" width="700">
</p>

| | |
|---|---|
| **Trigger** | "teach me X" · "I want to learn Y" · "create a lesson on Z" · "build me a course on..." |
| **Flow** | Intake (topic/depth/background) → outline approval checkpoint → chapter-by-chapter generation |
| **Output** | `lessons/<topic-slug>/` — numbered chapters, `00_index.md`, `ANSWERS.md`, optional combined PDF |
| **Depth** | Beginner · Intermediate · Advanced — calibrates vocabulary, pacing, and chapter count |

---

### 🧠 [Memory](skills/memory/)

Builds and maintains a persistent, file-based memory store for a project — split into short-term (active, frequently-needed) and long-term (full project detail) tiers, backed by JSON indexes so any agent can quickly tell whether it already knows something and exactly where to look if it doesn't.

Always delegates the actual reading, categorizing, and writing to a sub-agent, so the main conversation's context stays clean. Can be triggered anytime, and offers itself when the agent estimates its own context is filling up — checkpointing what's been learned before it risks being lost.

<p align="center">
  <img src="assets/demo/memory/demo.gif" alt="The Memory skill assembling a scratch-list of session learnings, dispatching a sub-agent that surveys the repo and files facts into short- and long-term tiers, then relaying a one-line status receipt" width="700">
</p>

| | |
|---|---|
| **Trigger** | "build memory" · "update memory" · self-offered at ~25% context |
| **Tiers** | `short/` — active & frequent · `long/` — full project detail |
| **Lookup** | JSON indexes (top-level tag manifest + per-tier detail) for fast "do we know this?" checks |
| **Always** | Delegates to a sub-agent — never reads/writes memory files in the main context |

---

## 🤖 Agents

Not every problem fits in a markdown skill loaded into someone else's context window. Some need their own process: a loop that reviews, fixes, re-reviews, and repeats — with state that survives a crash and a rubric that decides when to stop. The [`agents/`](agents/) directory holds standalone tools like that.

### 🛰️ [NASA/DoD Deep Agent](agents/nasa-dod-agent/)

A LangGraph CLI that runs the NASA/DOD review loop end-to-end instead of just reporting it: scans a codebase, generates patches for findings above your fix threshold, applies them with backups, re-reviews only the changed files, and repeats until the rubric passes or it hits `max_iterations`.

<p align="center">
  <img src="assets/demo/nasa-dod-agent/demo.gif" alt="The NASA/DoD Deep Agent reviewing a Go file with an unguarded divide-by-zero, generating a patch, applying it, and ending with a diff showing the zero-check it added" width="800">
  <br>
  <sub>A live run: catches an unguarded divide-by-zero, patches it, and ends with a diff of the fix. (<a href="assets/demo/nasa-dod-agent/demo.tape">regenerate with VHS</a>)</sub>
</p>

| | |
|---|---|
| **Install** | `cd agents/nasa-dod-agent && uv pip install -e ".[dev]"` |
| **Run** | `nasa-dod-agent review path/to/code` |
| **Loop** | review → evaluate rubric → generate fix → apply → re-review → repeat |
| **State** | Checkpoints + `.bak` backups under `.nasa-dod-agent/` — resumable and restorable |

See the [nasa-dod-agent README](agents/nasa-dod-agent/) for full usage, config, and architecture.

---

## 🔧 Installation

### Claude Code

<details open>
<summary><strong>Plugin install (recommended)</strong></summary>

This repo ships its own `.claude-plugin/marketplace.json`, so Claude Code can install it directly as a plugin — no cloning, no `CLAUDE.md` edits. Skills are namespaced as `codered:<skill-name>` (e.g. `codered:nasa-dod-code-review`, `codered:memory`), the same way plugins like `superpowers` show up.

Run both commands inside Claude Code:

```bash
/plugin marketplace add codered/ai
/plugin install codered@codered
```

Verify it's loaded:

```bash
/plugin list
```

To update later:

```bash
/plugin marketplace update codered
```

</details>

<details>
<summary><strong>Manual install (global)</strong></summary>

```bash
git clone https://github.com/codered/ai ~/.codered
```

Add to `~/.claude/CLAUDE.md`:

```text
Skills are available at ~/.codered/skills/. When asked to use a skill,
load and follow the SKILL.md in the relevant skill folder.
```

</details>

<details>
<summary><strong>Manual install (per-project)</strong></summary>

```bash
git clone https://github.com/codered/ai .codered
```

Add to `CLAUDE.md` in your project root:

```text
Skills are available at .codered/skills/. When asked to use a skill,
load and follow the SKILL.md in the relevant skill folder.
```

</details>

### Cursor

<details>
<summary><strong>Global install</strong></summary>

```bash
git clone https://github.com/codered/ai ~/.codered
```

Add to `~/.cursor/rules/codered.mdc`:

```text
Skills are available at ~/.codered/skills/. When asked to use a skill,
load and follow the SKILL.md in the relevant skill folder.
```

</details>

<details>
<summary><strong>Per-project install</strong></summary>

```bash
git clone https://github.com/codered/ai .codered
```

Add to `.cursor/rules/codered.mdc` in your project root:

```text
Skills are available at .codered/skills/. When asked to use a skill,
load and follow the SKILL.md in the relevant skill folder.
```

</details>

### GitHub Copilot

```bash
git clone https://github.com/codered/ai .codered
```

Add to `.github/copilot-instructions.md`:

```text
Skills are available at .codered/skills/. When asked to use a skill,
load and follow the SKILL.md in the relevant skill folder.
```

### Gemini CLI

```bash
git clone https://github.com/codered/ai ~/.codered
```

Add to `~/.gemini/GEMINI.md`:

```text
Skills are available at ~/.codered/skills/. When asked to use a skill,
load and follow the SKILL.md in the relevant skill folder.
```

### Any agent

If your agent reads a context file — `AGENTS.md`, `system-prompt.txt`, `.cursorrules`, or anything else — add this:

```text
Skills are available at <path>/skills/. When asked to use a skill,
load and follow the SKILL.md in the relevant skill folder.
```

Use the path that matches where you cloned the repo.

> [!TIP]
> Not sure which file your agent reads? Check its documentation or look for `AGENTS.md`, `CLAUDE.md`, or `.cursorrules` in your project root.

---

## 💡 How skills work

Each skill is a folder inside `skills/`. When you invoke a skill by name, your agent loads the `SKILL.md` in that folder — a YAML frontmatter block (`name`, `description`) followed by the instructions — and follows it from that point forward. Companion files referenced inside are loaded as needed during execution.

```
skills/
└── nasa-dod-code-review/
    ├── SKILL.md               ← agent entry point (frontmatter + instructions)
    ├── standards-sources.md   ← fetched at runtime
    ├── reviewer-prompt.md     ← analysis instructions
    ├── severity-guide.md      ← P0–P3 classification
    ├── codeowners-template.md ← first-run setup
    └── report-template.md     ← output format
```

Skills are plain markdown. They work because agents are good at following clear written instructions — and plain text is easy to read, version, improve, and contribute to.

> [!TIP]
> On Claude Code, installing this repo as a plugin (see [Installation](#-installation)) namespaces every skill under `codered:` — `codered:nasa-dod-code-review`, `codered:memory`, and so on — so they're unambiguous alongside skills from other plugins like `superpowers:brainstorming`. You can still trigger them by their natural-language phrases (`nasa-dod review`, `build memory`); Claude Code resolves those to the namespaced skill automatically. The manual clone install doesn't apply a namespace — skills are simply loaded by their plain folder name.

---

## 🧭 Philosophy

**One skill, one job.** Each skill does exactly one thing well. No skill depends on another, and none require a specific agent or platform.

**Blocking is an act of care.** A critical finding that stops a bad merge is worth more than a report that gets ignored. Skills that have gates, have them for a reason.

**Actionable over advisory.** Every finding comes with working code, not just a rule number.

**Quality over quantity.** Skills ship when they're ready — tested against real codebases, reviewed, and held to a high standard of clarity.

---

## 🤝 Contributing

Contributions are welcome. A few things before you start:

- **Open an issue first** for new skills so we can align on scope
- **New skills** should follow the structure in `skills/nasa-dod-code-review/` — a `SKILL.md` with frontmatter as the agent entry point, companion files for anything that would bloat it
- **Test with at least two agents** before submitting a PR
- **No vague instructions** — if a step could be interpreted two ways, pick one and make it explicit

```bash
git checkout -b skill/your-skill-name
# build, test, then open a PR
```

---

## ⭐ Show your support

If these skills save you time or catch a bug before it ships, consider leaving a star. It helps others find the project.

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.
</content>
