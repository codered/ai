<p align="center">
  <h1 align="center">⚡ CodeRed AI Skills</h1>
  <p align="center">Battle-tested skills for AI coding agents. Drop them in. They just work.</p>
</p>

<p align="center">
  <a href="https://github.com/codered/ai/stargazers"><img src="https://img.shields.io/github/stars/codered/ai?style=flat-square&color=yellow" alt="Stars"></a>
  <a href="https://github.com/codered/ai/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License"></a>
  <a href="https://github.com/codered/ai/tree/main/skills"><img src="https://img.shields.io/badge/skills-1-brightgreen?style=flat-square" alt="Skills"></a>
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
