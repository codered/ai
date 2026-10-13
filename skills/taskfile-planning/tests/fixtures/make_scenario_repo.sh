#!/usr/bin/env bash
# Create a scratch git repository with a Taskfile for the Mode 2 scenario run.
# Usage: make_scenario_repo.sh DIR   (DIR must not exist)
set -euo pipefail
dir="$1"
if [ -e "$dir" ]; then
  echo "$dir exists" >&2
  exit 2
fi
mkdir -p "$dir/src"
cd "$dir"
git init -q -b main
git config user.name "Scenario"
git config user.email "scenario@example.invalid"
echo ".worktrees/" > .gitignore
echo "Scenario repository for taskfile-planning." > README.md
touch src/.keep
cat > Taskfile.ste <<'TASKFILE'
PLAN scenario 1

GLOBAL
  AGENTS max 2
  PERMIT read **
  PERMIT write src/**
  PERMIT run test grep
  TOOL edit Write
  FLOW read -> edit -> verify -> report
  RULE Do not change files outside FILES.
END

TASK alpha
  GOAL Create the file src/alpha.txt with the word "alpha".
  FILES src/alpha.txt
  OUTPUT word = alpha
  VERIFY grep -q alpha src/alpha.txt
END

TASK beta
  GOAL Create the file src/beta.txt with the word "beta".
  FILES src/beta.txt
  VERIFY grep -q beta src/beta.txt
END

TASK delta
  GOAL Create the file src/delta.txt with the word "delta".
  FILES src/delta.txt
  VERIFY test -f src/never.txt
END

TASK gamma
  DEPENDS beta
  GOAL Create the file src/gamma.txt with the word ${alpha.word}.
  FILES src/gamma.txt
  VERIFY grep -q alpha src/gamma.txt
END

TASK epsilon
  DEPENDS delta
  GOAL Create the file src/epsilon.txt with the word "epsilon".
  FILES src/epsilon.txt
  VERIFY test -f src/epsilon.txt
END
TASKFILE
git add .gitignore README.md src/.keep
git commit -q -m "Scenario start"
echo "$dir"
