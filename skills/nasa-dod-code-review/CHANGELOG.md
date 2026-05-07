# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.1.0] — 2026-05-06

### Added

- `README.md` — skill entry point with full orchestration flow, dual install
  paths (global + per-repo), trigger phrases, and 8-step agent instructions
- `standards-sources.md` — authoritative URLs for NASA Power of Ten, DOD JSF
  AV C++, NASA/JPL C Standard, SEI CERT (C, C++, Python, Go, Rust, Java, JS),
  MISRA C, OWASP JS/TS security cheat sheets
- `reviewer-prompt.md` — 5-pass analysis framework: safety & security, error
  handling & control flow, complexity & structure, standards compliance,
  code quality & maintainability; language-specific checklists for C/C++,
  Python, Go, Rust, Java, JavaScript/TypeScript
- `severity-guide.md` — P0–P3 severity scale with decision criteria, concrete
  examples, tone guidance, and a classification quick-reference table
- `codeowners-template.md` — guided first-run setup for `.github/CODEOWNERS`
  and `.github/nasa-dod-review-config.json`; collects developers, approvers,
  solo/team mode, and target branch
- `report-template.md` — structured findings report with summary header, gate
  status, "What Looks Good" section, per-severity finding sections, three fix
  options per finding (with pros/cons and language-correct code), Override Log,
  and tone reminders
- P0/Critical gate enforcement: blocks merge, requires 2+ peer approvals for
  team override, allows solo-dev override with recorded notation
- Support for 7 languages: C, C++, Python, Go, Rust, Java, JavaScript/TypeScript
