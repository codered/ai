#!/usr/bin/env python3
"""Generate a comprehensive Markdown report from the company-analysis Go tool output."""

import json
import re
import sys
import argparse

# Sentiment terms. Each entry is a regular expression that matches the word and
# its usual inflections, anchored on word boundaries. A bare substring test
# gives false matches, such as "cut" inside "circuit", so every term is a
# pattern rather than a plain string.
BULLISH_TERMS = [
    r"beat(s|en)?", r"best", r"boost\w*", r"bullish", r"climb\w*", r"gain\w*",
    r"grow(s|th|ing)?", r"jump(s|ed|ing)?", r"outperform\w*", r"positive",
    r"profit\w*", r"rally|rallie[sd]|rallying", r"rais(e|es|ed|ing)",
    r"rebound\w*", r"record", r"ris(e|es|ing|en)", r"soar\w*", r"strength",
    r"strong(er|est)?", r"surg(e|es|ed|ing)", r"top(s|ped|ping)",
    r"upgrade[sd]?", r"win(s|ning)?",
]

BEARISH_TERMS = [
    r"bearish", r"concern\w*", r"cut(s|ting)?", r"declin\w*",
    r"disappoint\w*", r"downgrade[sd]?", r"drop(s|ped|ping)?",
    r"fall(s|ing|en)?", r"fell", r"layoff[s]?", r"lawsuit[s]?", r"loss(es)?",
    r"miss(es|ed)?", r"negative", r"plung\w*", r"pressure[sd]?", r"prob(e|es|ing)",
    r"risk[sy]?", r"selloff", r"sink(s|ing)?|sank", r"slid(e|es|ing)|slipp\w*",
    r"slow(down|ing)", r"slump\w*", r"tumbl\w*", r"underperform\w*",
    r"warn\w*", r"weak(er|ness)?", r"worst",
]

BULLISH_PATTERNS = [re.compile(r"\b(?:%s)\b" % term) for term in BULLISH_TERMS]
BEARISH_PATTERNS = [re.compile(r"\b(?:%s)\b" % term) for term in BEARISH_TERMS]

# A summary longer than this is cut, so one verbose article cannot crowd out the
# rest of the section.
SUMMARY_LIMIT = 220

# EPS is reported to the cent, so figures closer than half a cent are equal.
EPS_TOLERANCE = 0.005


def determine_sentiment(headline, summary):
    """Classify one article as bullish, bearish or neutral by keyword matching."""
    text = (headline + " " + summary).lower()
    bullish_count = sum(1 for pattern in BULLISH_PATTERNS if pattern.search(text))
    bearish_count = sum(1 for pattern in BEARISH_PATTERNS if pattern.search(text))

    if bullish_count > bearish_count:
        return "bullish"
    elif bearish_count > bullish_count:
        return "bearish"
    return "neutral"


def compare_eps(actual, estimate):
    """Report actual EPS against the estimate as beat, met or missed.

    Both figures are reported to the cent, so a difference below half a cent is
    a match. A direct equality test on floats can call a match a miss.
    """
    if abs(actual - estimate) < EPS_TOLERANCE:
        return "met"
    return "beat" if actual > estimate else "missed"


def format_headline(item):
    """Render one news item as a Markdown bullet, with its summary when present."""
    source = item.get("source") or "N/A"
    headline = item.get("headline", "")
    summary = " ".join((item.get("summary") or "").split())
    if len(summary) > SUMMARY_LIMIT:
        summary = summary[: SUMMARY_LIMIT - 1].rstrip() + "\u2026"
    if summary:
        return f"- **{source}**: {headline} \u2014 {summary}"
    return f"- **{source}**: {headline}"


def generate_report(json_output):
    """Generate Markdown report from JSON analysis data."""
    data = json.loads(json_output)

    ticker = data.get("ticker", "N/A")
    current_price = data.get("current_price", 0)
    # The Go tool sets these to null when a fetch fails, so treat null and
    # missing the same way.
    price_changes = data.get("price_changes") or {}
    earnings_data = data.get("earnings_data") or {}
    news = data.get("news") or []
    simulations = data.get("simulations") or []

    one_day = price_changes.get("1d", 0)
    one_week = price_changes.get("1w", 0)
    three_m = price_changes.get("3m", 0)
    ytd = price_changes.get("ytd", 0)

    # Sentiment analysis. Every article lands in exactly one bucket, so no
    # headline is dropped from the report.
    bullish_highlights = []
    bearish_highlights = []
    neutral_highlights = []

    for item in news:
        sentiment = determine_sentiment(item.get("headline", ""), item.get("summary") or "")
        highlight = format_headline(item)
        if sentiment == "bullish":
            bullish_highlights.append(highlight)
        elif sentiment == "bearish":
            bearish_highlights.append(highlight)
        else:
            neutral_highlights.append(highlight)

    # Analyst recommendations inference
    analyst_recs = []
    for item in news:
        headline = item.get("headline", "").lower()
        summary = item.get("summary", "").lower()
        if any(kw in headline + summary for kw in ["upgrade", "raise", "increase", "buy", "outperform"]):
            analyst_recs.append(format_headline(item))
        elif any(kw in headline + summary for kw in ["downgrade", "cut", "decrease", "sell", "underperform"]):
            analyst_recs.append(format_headline(item))

    if not analyst_recs:
        analyst_recs.append("- No specific analyst recommendations found in available news data.")

    # Simulations breakdown
    robinhood_simulations = [s for s in simulations if s["fee_scenario"] == "Robinhood/Vanguard"]
    traditional_simulations = [s for s in simulations if s["fee_scenario"] == "Traditional Broker"]

    # Build Markdown report
    report_lines = []

    # Disclaimer
    report_lines.append("---")
    report_lines.append("**Disclaimer:** This is not financial advice, it's a report and simulation.")
    report_lines.append("---")
    report_lines.append("")

    # Company Overview
    report_lines.append(f"# Company Analysis: {ticker}")
    report_lines.append(f"**Current Price:** ${current_price:.2f}")
    report_lines.append(f"**1-Day Change:** {one_day:.2f}%")
    report_lines.append(f"**1-Week Change:** {one_week:.2f}%")
    report_lines.append(f"**3-Month Change:** {three_m:.2f}%")
    report_lines.append(f"**YTD Change:** {ytd:.2f}%")
    report_lines.append("")

    # Earnings Summary
    report_lines.append("## Earnings Summary")
    eps_estimate = earnings_data.get("eps_estimate", None)
    eps_actual = earnings_data.get("eps_actual", None)
    earnings_date = earnings_data.get("earnings_date", None)

    if eps_estimate is not None:
        report_lines.append(f"- **EPS Estimate:** {eps_estimate:.2f}")
    if eps_actual is not None:
        report_lines.append(f"- **EPS Actual:** {eps_actual:.2f}")
        if eps_estimate is not None:
            report_lines.append(f"- **EPS {compare_eps(eps_actual, eps_estimate)} estimate**")
    if earnings_date:
        report_lines.append(f"- **Next Earnings Date:** {earnings_date}")
    report_lines.append("")

    # News & Sentiment Analysis
    report_lines.append("## News & Sentiment Analysis")
    report_lines.append("")

    if bullish_highlights:
        report_lines.append("### Bullish Themes")
        for h in bullish_highlights:
            report_lines.append(h)
        report_lines.append("")

    if bearish_highlights:
        report_lines.append("### Bearish Themes")
        for h in bearish_highlights:
            report_lines.append(h)
        report_lines.append("")

    # Headlines that match no sentiment term still carry market information, so
    # they are listed rather than discarded.
    if neutral_highlights:
        report_lines.append("### Other Headlines")
        for h in neutral_highlights:
            report_lines.append(h)
        report_lines.append("")

    if not news:
        report_lines.append("- No news headlines available for sentiment analysis.")
        report_lines.append("")

    # Analyst Recommendations
    report_lines.append("## Analyst Recommendations")
    report_lines.append("")
    for rec in analyst_recs:
        report_lines.append(rec)
    report_lines.append("")

    # Trade Simulations
    report_lines.append("## Trade Simulations")
    report_lines.append("")
    report_lines.append("| Quantity | Cost to Buy | Fee Scenario | Tax Scenario | Gross Profit | Fees | Taxes | Net Profit |")
    report_lines.append("|----------|------------|-------------|-------------|-------------|------|-------|-----------|")

    for sim in simulations:
        quantity = sim["quantity"]
        # Older payloads have no purchase_cost field, so derive it when absent.
        purchase_cost = sim.get("purchase_cost", quantity * current_price)
        fee_scenario = sim["fee_scenario"]
        tax_scenario = sim["tax_scenario"]
        gross_profit = sim["gross_profit"]
        fees = sim["fees"]
        taxes = sim["taxes"]
        net_profit = sim["net_profit"]
        report_lines.append(
            f"| {quantity} | ${purchase_cost:.2f} | {fee_scenario} | {tax_scenario} | "
            f"${gross_profit:.2f} | ${fees:.2f} | ${taxes:.2f} | ${net_profit:.2f} |"
        )
    report_lines.append("")

    # Simulation details
    report_lines.append("### Simulation Details")
    report_lines.append("")
    report_lines.append("**Fee Scenarios:**")
    report_lines.append("- **Robinhood/Vanguard:** $0 commission per trade")
    report_lines.append("- **Traditional Broker:** $4.95 per trade (applied to both buy and sell transactions)")
    report_lines.append("")
    report_lines.append("**Tax Scenarios:**")
    report_lines.append("- **Short-term gains (held < 1 year):** Flat default rate of ~24%")
    report_lines.append("- **Long-term gains (held ≥ 1 year):** Flat default rate of ~15%")
    report_lines.append("")
    report_lines.append("**Base Assumptions:**")
    report_lines.append("- Cost to buy: quantity × current price, before fees")
    report_lines.append("- Simulated sell price: current price × 1.10 (+10% hypothetical gain)")
    report_lines.append("- Holdings period used for tax classification: determined by tax scenario")

    return "\n".join(report_lines)


def main():
    parser = argparse.ArgumentParser(description="Generate Markdown report from company-analysis JSON")
    parser.add_argument("json_input", nargs="?", help="JSON input from Go tool (or read from stdin)")
    args = parser.parse_args()

    json_input = args.json_input

    if not json_input:
        # Read from stdin
        json_input = sys.stdin.read()

    try:
        data = json.loads(json_input)
    except json.JSONDecodeError as exc:
        sys.exit(f"error: input is not valid JSON: {exc}")

    # The Go tool reports a failed fetch as an error field. Stop here, because a
    # report built on missing price data would show invented numbers.
    if data.get("error"):
        sys.exit(f"error: {data['error']}")

    report = generate_report(json_input)
    print(report)


if __name__ == "__main__":
    main()