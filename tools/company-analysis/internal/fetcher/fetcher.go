package fetcher

import (
	"context"
	"fmt"
	"log"
	"net/url"

	"company-analysis/internal/models"
)

// FetchPriceData retrieves the current price and the price changes.
func FetchPriceData(ticker string) (*models.PriceChanges, float64, error) {
	// A one year range of daily closes supplies the 1w, 3m and YTD baselines.
	endpoint := fmt.Sprintf("%s/v8/finance/chart/%s?range=1y&interval=1d",
		yahooFinanceBaseURL, url.PathEscape(ticker))

	body, err := defaultClient.get(context.Background(), endpoint)
	if err != nil {
		return nil, 0, fmt.Errorf("fetch price data for %s: %w", ticker, err)
	}

	return parseChart(body)
}

// FetchSummaryData retrieves the company earnings data. This endpoint needs a
// cookie and a crumb token, so the client obtains both before the request.
func FetchSummaryData(ticker string) (*models.EarningsData, error) {
	ctx := context.Background()

	crumb, err := defaultClient.getCrumb(ctx)
	if err != nil {
		return nil, fmt.Errorf("fetch summary data for %s: %w", ticker, err)
	}

	endpoint := fmt.Sprintf("%s/v10/finance/quoteSummary/%s?modules=%s&crumb=%s",
		yahooFinanceBaseURL,
		url.PathEscape(ticker),
		url.QueryEscape("financialData,earnings"),
		url.QueryEscape(crumb))

	body, err := defaultClient.get(ctx, endpoint)
	if err != nil {
		return nil, fmt.Errorf("fetch summary data for %s: %w", ticker, err)
	}

	return parseQuoteSummary(body)
}

// FetchNews retrieves recent news for a ticker. The old tickerNews feed returns
// HTTP 404, so this uses the search endpoint instead.
//
// The search endpoint gives a headline, a publisher and a link, but no article
// summary. Sentiment analysis on a headline alone classifies almost everything
// as neutral, so this function then fills the summaries from the RSS feed.
func FetchNews(ticker string) ([]*models.NewsItem, error) {
	endpoint := fmt.Sprintf("%s/v1/finance/search?q=%s&newsCount=10&quotesCount=0",
		yahooFinanceBaseURL, url.QueryEscape(ticker))

	body, err := defaultClient.get(context.Background(), endpoint)
	if err != nil {
		return nil, fmt.Errorf("fetch news for %s: %w", ticker, err)
	}

	newsItems, err := parseSearchNews(body)
	if err != nil {
		return nil, err
	}

	// A summary improves the report but is not required for it. A failure here
	// leaves the summaries empty and keeps the headlines.
	summaries, err := fetchNewsSummaries(ticker)
	if err != nil {
		log.Printf("warning: failed to fetch news summaries: %v", err)
		return newsItems, nil
	}
	applySummaries(newsItems, summaries)

	return newsItems, nil
}

// fetchNewsSummaries retrieves the RSS headline feed, which carries a one
// sentence description for each article. The result maps a normalised headline
// to its description.
func fetchNewsSummaries(ticker string) (map[string]string, error) {
	endpoint := fmt.Sprintf("%s?s=%s&region=US&lang=en-US",
		yahooRSSHeadlineURL, url.QueryEscape(ticker))

	body, err := defaultClient.get(context.Background(), endpoint)
	if err != nil {
		return nil, fmt.Errorf("fetch news summaries for %s: %w", ticker, err)
	}

	return parseRSSDescriptions(body)
}

// applySummaries copies a description onto each item whose headline matches.
// The two feeds do not always carry the same articles, so an item without a
// match keeps its empty summary.
func applySummaries(newsItems []*models.NewsItem, summaries map[string]string) {
	for _, item := range newsItems {
		if item.Summary != "" {
			continue
		}
		if summary, ok := summaries[normaliseHeadline(item.Headline)]; ok {
			item.Summary = summary
		}
	}
}
