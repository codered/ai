#!/usr/bin/env bash
#
# Produce the company analysis report for one ticker.
#
# Usage: run.sh <TICKER>
#
# The script finds its own directory, so it runs correctly from any working
# directory and from any plugin install location.

set -uo pipefail

if [ "$#" -ne 1 ] || [ -z "${1:-}" ]; then
	echo "usage: run.sh <TICKER>" >&2
	exit 2
fi

ticker="$1"
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
	echo "error: python3 is not installed. The report generator needs it." >&2
	exit 3
fi

# Prefer the Go toolchain, which always builds the current source. Fall back to
# the bundled binary when Go is absent. The binary is Linux x86-64 only.
if command -v go >/dev/null 2>&1; then
	json="$(cd "$dir" && go run . -ticker "$ticker" 2>/dev/null)"
elif [ -x "$dir/company-analysis" ]; then
	json="$("$dir/company-analysis" -ticker "$ticker" 2>/dev/null)"
else
	echo "error: neither the Go toolchain nor the bundled binary is available." >&2
	echo "Install Go 1.25 or later, then run this script again." >&2
	exit 3
fi

if [ -z "$json" ]; then
	echo "error: the data fetcher produced no output." >&2
	exit 3
fi

# The generator prints the report, or one error line when the fetch failed.
printf '%s' "$json" | python3 "$dir/generate_report.py"
