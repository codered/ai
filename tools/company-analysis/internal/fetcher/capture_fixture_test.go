package fetcher

import (
	"context"
	"fmt"
	"net/url"
	"os"
	"testing"
)

// TestCaptureFixtures refreshes testdata from the live API. It is skipped
// unless CAPTURE_FIXTURES is set, so the normal test run stays offline.
func TestCaptureFixtures(t *testing.T) {
	if os.Getenv("CAPTURE_FIXTURES") == "" {
		t.Skip("set CAPTURE_FIXTURES to refresh testdata")
	}
	ctx := context.Background()

	chart, err := defaultClient.get(ctx, yahooFinanceBaseURL+"/v8/finance/chart/AAPL?range=1y&interval=1d")
	if err != nil {
		t.Fatalf("chart: %v", err)
	}
	os.WriteFile("testdata/chart_aapl.json", chart, 0o644)

	news, err := defaultClient.get(ctx, yahooFinanceBaseURL+"/v1/finance/search?q=AAPL&newsCount=10&quotesCount=0")
	if err != nil {
		t.Fatalf("search: %v", err)
	}
	os.WriteFile("testdata/search_aapl.json", news, 0o644)

	rss, err := defaultClient.get(ctx, yahooRSSHeadlineURL+"?s=AAPL&region=US&lang=en-US")
	if err != nil {
		t.Fatalf("rss: %v", err)
	}
	os.WriteFile("testdata/rss_aapl.xml", rss, 0o644)

	crumb, err := defaultClient.getCrumb(ctx)
	if err != nil {
		t.Fatalf("crumb: %v", err)
	}
	summary, err := defaultClient.get(ctx, fmt.Sprintf(
		"%s/v10/finance/quoteSummary/AAPL?modules=financialData,earnings&crumb=%s",
		yahooFinanceBaseURL, url.QueryEscape(crumb)))
	if err != nil {
		t.Fatalf("summary: %v", err)
	}
	os.WriteFile("testdata/quotesummary_aapl.json", summary, 0o644)
}
