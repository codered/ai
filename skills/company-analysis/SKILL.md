---
name: company-analysis
description: >
  Use this skill to perform a deep analysis for a given company. It correlates market news, sentiment, earnings, and stock price performance (1d, 1w, 3m, YTD).
  It highlights bearish and bullish sections, provides analyst recommendations, and performs a simulation of buying 5, 10, or 25 shares to maximize profits
  after removing fees and taxes for both short-term and long-term holdings. This is not financial advice, it's a report and simulation.
---

# Company Analysis & Simulation Skill

Performs a deep analysis for a given company using a Go-based data fetcher and simulation tool, followed by Host LLM sentiment analysis and report generation.

## Usage

```
/company-analysis <TICKER>
```

## Process

1. **Invoke Go Data Fetcher & Simulator**: Run the `company-analysis` Go tool with the company ticker symbol:
   ```bash
   go run ./tools/company-analysis/main.go -ticker <TICKER>
   ```
   This fetches structured financial data (prices, earnings, news) and performs trade simulations, outputting a structured JSON payload.

2. **Host LLM Report Generation**: The Host LLM (this AI) receives the structured JSON payload and:
   - Performs sentiment analysis on the news headlines/summaries and earnings data to identify **bullish** and **bearish** themes.
   - Extracts or infers **analyst recommendations** from the fetched news and summary data.
   - Assembles the final comprehensive Markdown report including:
     - Disclaimer: "This is not financial advice, it's a report and simulation."
     - Company Overview and key financial metrics.
     - Stock Price Performance (1d, 1w, 3m, YTD changes).
     - Earnings Summary.
     - News & Sentiment Analysis (bullish and bearish highlights).
     - Analyst Recommendations.
     - Trade Simulations (detailed breakdown for 5, 10, and 25 share purchases, including fee and tax scenarios).

## Simulation Parameters

- **Fee Scenarios**:
  - Robinhood/Vanguard: $0 commission per trade
  - Traditional Broker: $4.95 per trade (applied to both buy and sell transactions)
- **Tax Scenarios**:
  - Short-term gains (held < 1 year): Flat default rate of ~24%
  - Long-term gains (held ≥ 1 year): Flat default rate of ~15%