# CodeRed AI Skills

A collection of skills for AI coding assistants. Each skill is a focused,
standalone instruction set that teaches your agent a specific capability —
without requiring any special tooling, framework, or platform.

Works with Claude Code, GitHub Copilot, Cursor, Gemini CLI, and any other
agent that can read a markdown file.

---

## How it works

Skills are plain markdown files. When you install this repo and tell your
agent where to find them, it reads the relevant skill before tackling a task
— and follows its instructions from that point forward.

There's no plugin system to configure, no CLI to install, and no API keys to
manage. The skills are the interface. Your agent reads them the same way it
reads any other context: one file, clear instructions, immediate effect.

Skills are designed to be composable. You can use one or all of them. Each
one works independently, and they don't interfere with each other.

---

## Quickstart

Install for: [Claude Code](#claude-code) · [Cursor](#cursor) · [GitHub Copilot](#github-copilot) · [Gemini CLI](#gemini-cli) · [Any agent](#any-agent)

---

## Installation

### Claude Code

**Global install** — skills available in every project:
```bash
git clone https://github.com/codered/ai ~/.codered-skills
```

Add to `~/.claude/CLAUDE.md`:
```text
Skills are available at ~/.codered-skills/skills/. When asked to use a skill,
load and follow the README.md inside the relevant skill folder.
```

**Per-project install** — skills live alongside your code:
```bash
git clone https://github.com/codered/ai .codered-skills
```

Add to `CLAUDE.md` in your project root:
```text
Skills are available at .codered-skills/skills/. When asked to use a skill,
load and follow the README.md inside the relevant skill folder.
```

### Cursor

**Global install**:
```bash
git clone https://github.com/codered/ai ~/.codered-skills
```

Add to `~/.cursor/rules/codered.mdc`:
```text
Skills are available at ~/.codered-skills/skills/. When asked to use a skill,
load and follow the README.md inside the relevant skill folder.
```

**Per-project install**: clone into `.codered-skills/` and add a `.cursor/rules/codered.mdc`
to your project root with the per-project path.

### GitHub Copilot

```bash
git clone https://github.com/codered/ai .codered-skills
```

Add to `.github/copilot-instructions.md`:
```text
Skills are available at .codered-skills/skills/. When asked to use a skill,
load and follow the README.md inside the relevant skill folder.
```

### Gemini CLI

```bash
git clone https://github.com/codered/ai ~/.codered-skills
```

Add to `~/.gemini/GEMINI.md`:
```text
Skills are available at ~/.codered-skills/skills/. When asked to use a skill,
load and follow the README.md inside the relevant skill folder.
```

### Any agent

If your agent reads a system prompt, context file, or instruction document:

```bash
git clone https://github.com/codered/ai ~/.codered-skills
# or per-project:
git clone https://github.com/codered/ai .codered-skills
```

Add one line to whatever context file your agent reads:
```text
Skills are available at <path>/skills/. When asked to use a skill,
load and follow the README.md inside the relevant skill folder.
```

---

## Skills

### [NASA/DOD Code Review](skills/nasa-dod-code-review/)

Reviews your code against NASA and DOD engineering standards — the same
standards used for flight software, defense systems, and other contexts
where bugs have real consequences.

Works in two modes: full codebase scan during development, and diff-first
review during PR. Critical issues block the merge. Every finding comes with
three fix options, complete with trade-offs and working code in your language.

**Trigger:** `nasa-dod review` · `nasa-dod dev review` · `nasa-dod pr review`

**Languages:** C/C++, Python, Go, Rust, Java, JavaScript/TypeScript

---

## Philosophy

**One skill, one job.** Each skill does exactly one thing and does it well.
No skill depends on another, and none of them require a specific agent or platform.

**Instructions over frameworks.** The skills are markdown files, not code.
They work because agents are good at following clear written instructions —
and they're easy to read, improve, and contribute to.

**Earning trust through rigor.** The skills that exist here are held to a high
standard: clear trigger conditions, unambiguous instructions, tested against
real codebases, and reviewed before merge. Quality over quantity.

---

## Contributing

Contributions are welcome. A few things to know before you start:

- **New skills** should follow the existing file structure: a `README.md` as
  the agent entry point, with companion files for anything that would make the
  README unwieldy. See `skills/nasa-dod-code-review/` as a reference.
- **Each skill must work across agents.** Before submitting, test your skill
  with at least two different coding assistants.
- **No vague instructions.** If an instruction could be interpreted two ways,
  pick one and make it explicit.
- **Open an issue first** for new skills, so we can align on scope before you
  build it out.

```bash
# Fork the repo, then:
git checkout -b skill/your-skill-name
# build it, test it, then open a PR
```

---

## License

MIT — see [LICENSE](LICENSE) for details.
