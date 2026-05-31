<p align="center">
  <h1 align="center">⚡ CodeRed AI Skills</h1>
  <p align="center">Battle-tested skills for AI coding agents. Drop them in. They just work.</p>
</p>

<p align="center">
  <a href="https://github.com/codered/ai/stargazers"><img src="https://img.shields.io/github/stars/codered/ai?style=flat-square&color=yellow" alt="Stars"></a>
  <a href="https://github.com/codered/ai/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License"></a>
  <a href="https://github.com/codered/ai/tree/main/skills"><img src="https://img.shields.io/badge/skills-4-brightgreen?style=flat-square" alt="Skills"></a>
</p>

<p align="center">
  <b>Works with Claude Code · Cursor · GitHub Copilot · Gemini CLI · Any agent that reads markdown</b>
</p>

---

## What is this?

A growing library of skills for AI coding agents. Each skill is a focused set of markdown instructions — no plugins, no frameworks, no configuration required. Point your agent at the folder and it knows what to do.

Skills are designed to be precise, opinionated, and immediately useful. They encode hard-won knowledge — engineering standards, team workflows, review processes — in a format any agent can act on.

> [!NOTE]
> If your agent can read a file, it can use these skills.

---

## 🚀 Quickstart

**1. Clone the repo**

```bash
# Global install (available across all your projects)
git clone https://github.com/codered/ai ~/.codered

# Per-project install (lives alongside your code)
git clone https://github.com/codered/ai .codered
```

**2. Tell your agent where to find the skills**

Add one line to your agent's context file. The exact file depends on your agent — see [Installation](#installation) for specifics.

```text
Skills are available at <path>/skills/. Load the README.md in the relevant skill folder when asked to use a skill.
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

Works in two modes: full codebase scan during development, diff-first during PR review. Critical findings block the merge. Every issue comes with three fix options — with trade-offs and working code in your language.

| | |
|---|---|
| **Trigger** | `nasa-dod review` · `nasa-dod dev review` · `nasa-dod pr review` |
| **Languages** | C/C++, Python, Go, Rust, Java, JavaScript/TypeScript |
| **Standards** | NASA Power of Ten · DOD JSF AV · SEI CERT · MISRA · OWASP |
| **Gate** | P0/Critical blocks merge · 2+ approvals to override on teams |

### 🤖 [Agent Team](skills/agent-team/)

Assembles a five-role engineering team inside any repository — PM, Developer, QA, Security, and DevOps. Each agent has a distinct persona, scope, and responsibilities. They coordinate through a shared memory system and a rolling pipeline that keeps work moving without bottlenecks.

The PM creates a phased plan with explicit gate criteria. The Dev agent implements using TDD and self-reviews with the NASA/DOD Code Review skill before handoff. QA and Security review each completed task while Dev moves forward. DevOps handles CI/CD, infra, and produces the final readiness gate before anything ships.

| | |
|---|---|
| **Trigger** | `init agent team` · `agent team` · `agent team status` |
| **Roles** | PM · Dev · QA · Security · DevOps |
| **Pipeline** | Rolling — Dev never blocks waiting on review |
| **Gate** | P0/P1 findings block task close · phase gates before advancing |

### 🔍 [Code Analyst](skills/code-analyst/)

Produces a structured Markdown analysis of any piece of code — function breakdowns, data flow, dependencies, and test case analysis — within a strict 2-minute time budget. Emits live status updates as it works so you always know where it is.

Covers purpose, parameters, return values, side effects, error conditions, and edge cases. Saves the result as `<filename>_analysis.md` when file tools are available. Designed for developers who need to quickly understand code they didn't write.

| | |
|---|---|
| **Trigger** | "analyze this code" · "explain what this does" · "document this function" · pasting code with no explanation |
| **Output** | Structured Markdown: overview, function breakdown, data flow, dependencies, test cases |
| **Time budget** | 120 seconds — pauses and asks to continue if the limit is reached |
| **Tone** | Plain language for developers who didn't write the code |

### 📐 [Codebase Spec](skills/codebase-spec/)

Reads an entire codebase and produces a multi-document specification suite thorough enough that an engineer — or an AI agent — can reimplement the whole thing in a different language with no access to the original source.

Works in five phases: orientation, ambiguity resolution, module-by-module analysis, cross-cutting concerns, and delivery. Outputs a `spec/` directory with numbered documents covering architecture, requirements, assumptions, limitations, data models, API contracts, per-module deep-dives, and cross-cutting concerns (auth, error handling, logging, concurrency, security). Designed for large codebases (100+ files) but works at any scale.

| | |
|---|---|
| **Trigger** | "write a spec for this codebase" · "document this project" · "I want to migrate this" · "reverse engineer this" |
| **Output** | `spec/` directory — `00_overview.md` through `NN_cross_cutting.md` |
| **Scale** | Designed for 100+ file codebases; works at any size |
| **Gate** | Reimplementation completeness checklist before delivery |


---

## 🔧 Installation

### Claude Code

<details>
<summary><strong>Global install</strong></summary>

```bash
git clone https://github.com/codered/ai ~/.codered
```

Add to `~/.claude/CLAUDE.md`:

```text
Skills are available at ~/.codered/skills/. When asked to use a skill,
load and follow the README.md in the relevant skill folder.
```

</details>

<details>
<summary><strong>Per-project install</strong></summary>

```bash
git clone https://github.com/codered/ai .codered
```

Add to `CLAUDE.md` in your project root:

```text
Skills are available at .codered/skills/. When asked to use a skill,
load and follow the README.md in the relevant skill folder.
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
load and follow the README.md in the relevant skill folder.
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
load and follow the README.md in the relevant skill folder.
```

</details>

### GitHub Copilot

```bash
git clone https://github.com/codered/ai .codered
```

Add to `.github/copilot-instructions.md`:

```text
Skills are available at .codered/skills/. When asked to use a skill,
load and follow the README.md in the relevant skill folder.
```

### Gemini CLI

```bash
git clone https://github.com/codered/ai ~/.codered
```

Add to `~/.gemini/GEMINI.md`:

```text
Skills are available at ~/.codered/skills/. When asked to use a skill,
load and follow the README.md in the relevant skill folder.
```

### Any agent

If your agent reads a context file — `AGENTS.md`, `system-prompt.txt`, `.cursorrules`, or anything else — add this:

```text
Skills are available at <path>/skills/. When asked to use a skill,
load and follow the README.md in the relevant skill folder.
```

Use the path that matches where you cloned the repo.

> [!TIP]
> Not sure which file your agent reads? Check its documentation or look for `AGENTS.md`, `CLAUDE.md`, or `.cursorrules` in your project root.

---

## 💡 How skills work

Each skill is a folder inside `skills/`. When you invoke a skill by name, your agent loads the `README.md` in that folder and follows its instructions from that point forward. Companion files (referenced inside the README) are loaded as needed during execution.

```
skills/
└── nasa-dod-code-review/
    ├── README.md              ← agent entry point
    ├── standards-sources.md   ← fetched at runtime
    ├── reviewer-prompt.md     ← analysis instructions
    ├── severity-guide.md      ← P0–P3 classification
    ├── codeowners-template.md ← first-run setup
    └── report-template.md     ← output format
```

Skills are plain markdown. They work because agents are good at following clear written instructions — and plain text is easy to read, version, improve, and contribute to.

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
- **New skills** should follow the structure in `skills/nasa-dod-code-review/` — one `README.md` as the agent entry point, companion files for anything that would bloat it
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
