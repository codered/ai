#!/usr/bin/env bash
# Minimal fake agent REPL for the demo GIF — replays a condensed,
# authentic codebase-spec pass (mirrors the real 5-phase structure
# and spec/ output described in skills/codebase-spec/SKILL.md).

p() { printf '%s\n' "$1"; sleep "${2:-0.32}"; }

printf '> '
read -r _request
echo

p "Phase 0 — Orientation: 38 files, Go + Postgres, 6 packages mapped" 0.6
p "Phase 1 — Ambiguity resolution: 2 questions answered, assumptions logged" 0.6
p "Phase 2 — Module analysis: api/ · auth/ · billing/ · worker/ · storage/" 0.6
p "Phase 3 — Cross-cutting: auth, error handling, concurrency, logging" 0.6
p "Phase 4 — Delivery: writing spec/ ..." 0.7
echo
p "  spec/00_overview.md           ✓" 0.22
p "  spec/01_architecture.md       ✓" 0.22
p "  spec/02_requirements.md       ✓" 0.22
p "  spec/03_data_models.md        ✓" 0.22
p "  spec/04_api_contracts.md      ✓" 0.22
p "  spec/05_module_api.md         ✓" 0.22
p "  spec/06_module_worker.md      ✓" 0.22
p "  spec/07_cross_cutting.md      ✓" 0.5
echo
p "✅ spec/ ready — 8 documents, reimplementation checklist passed" 0.8
