package fetcher

import (
	"context"
	"fmt"
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
func FetchNews(ticker string) ([]*models.NewsItem, error) {
	endpoint := fmt.Sprintf("%s/v1/finance/search?q=%s&newsCount=10&quotesCount=0",
		yahooFinanceBaseURL, url.QueryEscape(ticker))

	body, err := defaultClient.get(context.Background(), endpoint)
	if err != nil {
		return nil, fmt.Errorf("fetch news for %s: %w", ticker, err)
	}

	return parseSearchNews(body)
}
