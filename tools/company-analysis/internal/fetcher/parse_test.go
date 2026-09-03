package fetcher

import (
	"fmt"
	"os"
	"strings"
	"testing"
	"time"

	"company-analysis/internal/models"
)

func readFixture(t *testing.T, name string) []byte {
	t.Helper()
	body, err := os.ReadFile("testdata/" + name)
	if err != nil {
		t.Fatalf("read fixture %s: %v", name, err)
	}
	return body
}

func TestParseChartReadsPriceFromMeta(t *testing.T) {
	changes, price, err := parseChart(readFixture(t, "chart_aapl.json"))
	if err != nil {
		t.Fatalf("parseChart returned an error: %v", err)
	}
	if price <= 0 {
		t.Errorf("price = %v, want a positive number", price)
	}
	if changes == nil {
		t.Fatal("changes is nil")
	}
	if changes.OneDay == 0 {
		t.Errorf("OneDay = 0, want the value from regularMarketChangePercent")
	}
	// The fixture covers one year of daily closes, so every interval resolves.
	if changes.OneWeek == 0 || changes.ThreeM == 0 || changes.YTD == 0 {
		t.Errorf("intervals = %+v, want all non zero from the live series", changes)
	}
}

func TestParseChartRejectsFlatResponse(t *testing.T) {
	// The old parser looked for a top level "result" key. Confirm that shape
	// is now reported as an error instead of being read as valid data.
	if _, _, err := parseChart([]byte(`{"result":[{"meta":{"regularMarketPrice":1}}]}`)); err == nil {
		t.Error("parseChart accepted a response with no 'chart' object")
	}
}

func TestParseChartReportsAPIError(t *testing.T) {
	body := []byte(`{"chart":{"result":null,"error":{"code":"Not Found","description":"No data found"}}}`)
	_, _, err := parseChart(body)
	if err == nil {
		t.Fatal("parseChart accepted an API error response")
	}
}

func TestParseQuoteSummaryReadsEarnings(t *testing.T) {
	earnings, err := parseQuoteSummary(readFixture(t, "quotesummary_aapl.json"))
	if err != nil {
		t.Fatalf("parseQuoteSummary returned an error: %v", err)
	}
	if earnings.EpsActual == 0 {
		t.Errorf("EpsActual = 0, want the latest quarterly actual")
	}
	if earnings.EarningsDate == "" {
		t.Errorf("EarningsDate is empty, want a date")
	}
}

func TestParseQuoteSummaryReportsCrumbFailure(t *testing.T) {
	body := []byte(`{"finance":{"result":null,"error":{"code":"Unauthorized","description":"Invalid Crumb"}}}`)
	_, err := parseQuoteSummary(body)
	if err == nil {
		t.Fatal("parseQuoteSummary accepted an unauthorized response")
	}
}

func TestParseSearchNewsReadsArticles(t *testing.T) {
	items, err := parseSearchNews(readFixture(t, "search_aapl.json"))
	if err != nil {
		t.Fatalf("parseSearchNews returned an error: %v", err)
	}
	if len(items) == 0 {
		t.Fatal("no news items parsed")
	}
	for i, item := range items {
		if item.Headline == "" {
			t.Errorf("item %d has an empty headline", i)
		}
		if item.PublishTime == "" {
			t.Errorf("item %d (%q) has an empty publish time", i, item.Headline)
		}
		if item.Url == "" {
			t.Errorf("item %d (%q) has an empty url", i, item.Headline)
		}
	}
}

func TestNumberAtAcceptsBothNumberForms(t *testing.T) {
	container := map[string]interface{}{
		"plain":  12.5,
		"nested": map[string]interface{}{"raw": 7.25, "fmt": "7.25"},
		"text":   "not a number",
	}

	cases := []struct {
		key  string
		want float64
		ok   bool
	}{
		{"plain", 12.5, true},
		{"nested", 7.25, true},
		{"text", 0, false},
		{"missing", 0, false},
	}

	for _, tc := range cases {
		got, ok := numberAt(container, tc.key)
		if got != tc.want || ok != tc.ok {
			t.Errorf("numberAt(%q) = (%v, %v), want (%v, %v)", tc.key, got, ok, tc.want, tc.ok)
		}
	}
}

// unixOf returns the UTC unix timestamp for a calendar date.
func unixOf(t *testing.T, date string) int64 {
	t.Helper()
	parsed, err := time.Parse("2006-01-02", date)
	if err != nil {
		t.Fatalf("parse date %s: %v", date, err)
	}
	return parsed.Unix()
}

// buildChart writes a chart response with a known close series. The null close
// simulates a market holiday.
func buildChart(t *testing.T, asOf int64, price float64, stamps []int64, closes []string) []byte {
	t.Helper()
	stampText := make([]string, len(stamps))
	for i, stamp := range stamps {
		stampText[i] = fmt.Sprintf("%d", stamp)
	}
	return []byte(fmt.Sprintf(`{"chart":{"result":[{
		"meta":{"regularMarketPrice":%v,"regularMarketChangePercent":1.5,"regularMarketTime":%d},
		"timestamp":[%s],
		"indicators":{"quote":[{"close":[%s]}]}
	}],"error":null}}`,
		price, asOf, strings.Join(stampText, ","), strings.Join(closes, ",")))
}

func TestParseChartComputesLongerIntervals(t *testing.T) {
	asOf := unixOf(t, "2026-09-02")
	stamps := []int64{
		unixOf(t, "2025-12-31"), // year end close, the YTD baseline
		unixOf(t, "2026-06-01"), // at or before the 3 month cutoff
		unixOf(t, "2026-08-25"), // at or before the 1 week cutoff
		unixOf(t, "2026-08-28"), // a holiday, so no close
		asOf,
	}
	closes := []string{"50", "100", "88", "null", "110"}

	changes, price, err := parseChart(buildChart(t, asOf, 110, stamps, closes))
	if err != nil {
		t.Fatalf("parseChart returned an error: %v", err)
	}
	if price != 110 {
		t.Fatalf("price = %v, want 110", price)
	}

	cases := []struct {
		name string
		got  float64
		want float64
	}{
		{"OneDay", changes.OneDay, 1.5},
		{"OneWeek", changes.OneWeek, 25}, // 110 against 88
		{"ThreeM", changes.ThreeM, 10},   // 110 against 100
		{"YTD", changes.YTD, 120},        // 110 against 50
	}
	for _, tc := range cases {
		if tc.got != tc.want {
			t.Errorf("%s = %v, want %v", tc.name, tc.got, tc.want)
		}
	}
}

func TestParseChartLeavesIntervalsZeroWithoutHistory(t *testing.T) {
	// A short range carries no usable series. The intervals stay at zero rather
	// than reporting a change computed from missing data.
	body := []byte(`{"chart":{"result":[{"meta":{"regularMarketPrice":110,"regularMarketChangePercent":1.5}}],"error":null}}`)
	changes, _, err := parseChart(body)
	if err != nil {
		t.Fatalf("parseChart returned an error: %v", err)
	}
	if changes.OneWeek != 0 || changes.ThreeM != 0 || changes.YTD != 0 {
		t.Errorf("intervals = %+v, want all zero", changes)
	}
}

func TestPercentChangeHandlesZeroBaseline(t *testing.T) {
	if got := percentChange(110, 0); got != 0 {
		t.Errorf("percentChange(110, 0) = %v, want 0", got)
	}
	if got := percentChange(110, 100); got != 10 {
		t.Errorf("percentChange(110, 100) = %v, want 10", got)
	}
}

func TestParseRSSDescriptionsReadsSummaries(t *testing.T) {
	descriptions, err := parseRSSDescriptions(readFixture(t, "rss_aapl.xml"))
	if err != nil {
		t.Fatalf("parseRSSDescriptions returned an error: %v", err)
	}
	if len(descriptions) == 0 {
		t.Fatal("descriptions is empty, want one entry per feed item")
	}
	for headline, summary := range descriptions {
		if headline == "" || summary == "" {
			t.Errorf("entry %q -> %q, want both parts non empty", headline, summary)
		}
	}
}

func TestParseRSSDescriptionsRejectsNonXML(t *testing.T) {
	if _, err := parseRSSDescriptions([]byte("Too Many Requests")); err == nil {
		t.Error("expected an error for a body that is not XML")
	}
}

func TestNormaliseHeadlineIgnoresPunctuationAndCase(t *testing.T) {
	// The search endpoint and the RSS feed punctuate the same headline
	// differently, so both forms must reduce to one key.
	fromSearch := normaliseHeadline("Zscaler’s Next Earnings Report: Here's Why.")
	fromRSS := normaliseHeadline("Zscaler's Next Earnings Report - Here's Why")
	if fromSearch != fromRSS {
		t.Errorf("keys differ: %q vs %q", fromSearch, fromRSS)
	}
}

func TestApplySummariesFillsOnlyEmptySummaries(t *testing.T) {
	items := []*models.NewsItem{
		{Headline: "Shares Are Falling"},
		{Headline: "Unmatched Headline"},
		{Headline: "Already Set", Summary: "keep me"},
	}
	applySummaries(items, map[string]string{
		normaliseHeadline("Shares Are Falling"): "The stock dropped after hours.",
		normaliseHeadline("Already Set"):        "overwrite me",
	})

	if items[0].Summary != "The stock dropped after hours." {
		t.Errorf("item 0 summary = %q, want the feed description", items[0].Summary)
	}
	if items[1].Summary != "" {
		t.Errorf("item 1 summary = %q, want empty for an unmatched headline", items[1].Summary)
	}
	if items[2].Summary != "keep me" {
		t.Errorf("item 2 summary = %q, want the existing value kept", items[2].Summary)
	}
}
