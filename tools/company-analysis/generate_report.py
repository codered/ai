#!/usr/bin/env python3
"""Generate a comprehensive Markdown report from the company-analysis Go tool output."""

import json
import sys
import argparse


def determine_sentiment(headline, summary):
    """Simple sentiment analysis based on keyword matching."""
    bullish_keywords = ["beat", "best", "growth", "gain", "rise", "upgrade", "positive", "strong", "record", "profit"]
    bearish_keywords = ["miss", "worst", "decline", "loss", "drop", "downgrade", "negative", "weak", "concern", "risk"]

    text = (headline + " " + summary).lower()
    bullish_count = sum(1 for kw in bullish_keywords if kw in text)
    bearish_count = sum(1 for kw in bearish_keywords if kw in text)

    if bullish_count > bearish_count:
        return "bullish"
    elif bearish_count > bullish_count:
        return "bearish"
    return "neutral"


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

    # Sentiment analysis
    bullish_highlights = []
    bearish_highlights = []

    for item in news:
        sentiment = determine_sentiment(item.get("headline", ""), item.get("summary", ""))
        highlight = f"- **{item.get('source', 'N/A')}**: {item.get('headline', '')}"
        if sentiment == "bullish":
            bullish_highlights.append(highlight)
        elif sentiment == "bearish":
            bearish_highlights.append(highlight)

    # Analyst recommendations inference
    analyst_recs = []
    for item in news:
        headline = item.get("headline", "").lower()
        summary = item.get("summary", "").lower()
        if any(kw in headline + summary for kw in ["upgrade", "raise", "increase", "buy", "outperform"]):
            analyst_recs.append(f"- **{item.get('source', 'N/A')}**: {item.get('headline', '')}")
        elif any(kw in headline + summary for kw in ["downgrade", "cut", "decrease", "sell", "underperform"]):
            analyst_recs.append(f"- **{item.get('source', 'N/A')}**: {item.get('headline', '')}")

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
            beat_miss = "beat" if eps_actual > eps_estimate else "missed"
            report_lines.append(f"- **EPS {beat_miss} estimate**")
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

    if not bullish_highlights and not bearish_highlights:
        report_lines.append("- No significant news headlines available for sentiment analysis.")
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
    report_lines.append("| Quantity | Fee Scenario | Tax Scenario | Gross Profit | Fees | Taxes | Net Profit |")
    report_lines.append("|----------|-------------|-------------|-------------|------|-------|-----------|")

    for sim in simulations:
        quantity = sim["quantity"]
        fee_scenario = sim["fee_scenario"]
        tax_scenario = sim["tax_scenario"]
        gross_profit = sim["gross_profit"]
        fees = sim["fees"]
        taxes = sim["taxes"]
        net_profit = sim["net_profit"]
        report_lines.append(
            f"| {quantity} | {fee_scenario} | {tax_scenario} | ${gross_profit:.2f} | ${fees:.2f} | ${taxes:.2f} | ${net_profit:.2f} |"
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