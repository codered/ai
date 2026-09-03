---
name: company-analysis
description: >
  Use this skill to perform a deep analysis for a given company. It correlates market news, sentiment, earnings, and stock price performance (1d, 1w, 3m, YTD).
  It highlights bearish and bullish sections, provides analyst recommendations, and performs a simulation of buying 5, 10, or 25 shares to maximize profits
  after removing fees and taxes for both short-term and long-term holdings. This is not financial advice, it's a report and simulation.
---

# Company Analysis & Simulation Skill

Two bundled scripts produce the report. The Go tool fetches the data and runs the
simulations. The Python script assembles the Markdown. Run both and show the
output.

## Usage

```
/company-analysis <TICKER>
```

## Process

Run this single pipeline from the `tools/company-analysis` directory. Replace
`<TICKER>` with the symbol, such as `AAPL`.

```bash
cd tools/company-analysis
go run . -ticker <TICKER> | python3 generate_report.py
```

The command prints the finished Markdown report. Show that output to the user.

The Go tool prints JSON. The Python script converts that JSON into the report.
Neither step needs help from you.

## Rules

**Do not write any part of the report yourself.**

- Do not read the JSON and compose your own Markdown.
- Do not add your own sentiment analysis. `generate_report.py` does this.
- Do not add your own analyst recommendations. `generate_report.py` does this.
- Do not calculate prices, changes, fees, taxes, or profits. The Go tool does this.
- Do not add sections, remove sections, or reword the output.
- Do not summarize the report in place of showing it.

The report is deterministic. Two runs with the same data give the same text.
Your own wording would break that.

## Prerequisites

- **Go 1.25 or later.** The first run downloads the module dependencies.
- **Python 3.6 or later.** `generate_report.py` imports only the standard
  library (`json`, `sys`, `argparse`). There is nothing to `pip install`. Do not
  create a virtual environment for it.

## If a step fails

When the Go tool cannot fetch the price data, it prints a JSON object with an
`error` field and exits with status 1. `generate_report.py` sees that field,
prints one line, and stops before it writes a report:

```
$ go run . -ticker ZZZZ | python3 generate_report.py
error: fetch price data for ZZZZ: yahoo finance returned status 404
```

Report that line to the user. Common causes:

| Error text | Cause |
|---|---|
| `status 404` | The ticker symbol does not exist. |
| `status 429` after retries | Yahoo Finance is rate limiting. Wait, then retry. |
| `fetch crumb` | Yahoo Finance blocked the session token request. |

Do not substitute a placeholder price and do not write the report by hand
instead. A report built on invented data is worse than no report.

Earnings and news are optional. If those fetches fail, the Go tool logs a
warning to stderr and still prints usable JSON. Let the pipeline continue.

## Simulation Parameters

- **Fee Scenarios**:
  - Robinhood/Vanguard: $0 commission per trade
  - Traditional Broker: $4.95 per trade (applied to both buy and sell transactions)
- **Tax Scenarios**:
  - Short-term gains (held < 1 year): Flat default rate of ~24%
  - Long-term gains (held ≥ 1 year): Flat default rate of ~15%
- **Sell price**: current price × 1.10, a hypothetical +10% gain
