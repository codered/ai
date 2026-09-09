#!/usr/bin/env bash
# Minimal fake agent REPL for the demo GIF — replays a real
# ./tools/company-analysis/run.sh AAPL run captured on 2026-09-08.
# Prices, headlines, and simulation rows are verbatim from that run;
# long headline text and 8 of the 12 simulation rows are elided to fit
# the frame. Nothing here is recomputed or reworded.

p() { printf '%s\n' "$1"; sleep "${2:-0.35}"; }

printf '> '
read -r _request
echo

printf '$ ./tools/company-analysis/run.sh AAPL\n'
sleep 1.2
p "---" 0.15
p "**Disclaimer:** This is not financial advice, it's a report and simulation." 0.15
p "---" 0.6
echo
p "# Company Analysis: AAPL" 0.25
p "**Current Price:** \$316.22" 0.15
p "**1-Day Change:** -1.17%" 0.15
p "**1-Week Change:** -2.74%" 0.15
p "**3-Month Change:** 4.87%" 0.15
p "**YTD Change:** 16.32%" 0.6
echo
p "## Earnings Summary" 0.25
p "- **EPS Estimate:** 1.98" 0.15
p "- **EPS Actual:** 2.02" 0.15
p "- **EPS beat estimate**" 0.15
p "- **Next Earnings Date:** 2026-10-29" 0.7
echo
p "## News & Sentiment Analysis" 0.3
p "### Bearish Themes" 0.25
p "- **Motley Fool**: [History Says September Is the Worst Month for Stocks...]" 0.2
p "- **Barrons.com**: [Review & Preview: A Slippery Start to Fall]" 0.6
p "### Other Headlines" 0.25
p "- **Investopedia**: [Apple Is Set to Reveal New iPhones Wednesday...]" 0.2
p "- **TheStreet**: [Louis Navellier's Apple stock rating shifts massively...]" 0.7
echo
p "## Trade Simulations" 0.4
p "| Qty | Cost to Buy | Fee Scenario | Tax Scenario | Gross | Fees | Taxes | Net |" 0.2
p "|-----|------------|--------------|--------------|-------|------|-------|-----|" 0.2
p "| 5   | \$1581.10   | Robinhood/Vanguard | Short-term | \$158.11 | \$0.00 | \$37.95 | \$120.16 |" 0.25
p "| 5   | \$1581.10   | Traditional Broker | Long-term  | \$158.11 | \$9.90 | \$23.72 | \$124.49 |" 0.25
p "| 25  | \$7905.50   | Robinhood/Vanguard | Short-term | \$790.55 | \$0.00 | \$189.73 | \$600.82 |" 0.25
p "| 25  | \$7905.50   | Traditional Broker | Long-term  | \$790.55 | \$9.90 | \$118.58 | \$662.07 |" 0.5
p "                                                        ... 8 more rows" 0.9
echo
p "The tools computed every number — the agent only shows the output." 1.0
