package fetcher

import (
	"encoding/json"
	"encoding/xml"
	"fmt"
	"strings"
	"time"
	"unicode"

	"company-analysis/internal/models"
)

// numberAt reads a numeric field. Yahoo returns some numbers as plain JSON
// numbers and others as {"raw": <number>, "fmt": "<text>"}. Both forms occur in
// the same response, so every read goes through this function.
func numberAt(container map[string]interface{}, key string) (float64, bool) {
	switch value := container[key].(type) {
	case float64:
		return value, true
	case map[string]interface{}:
		raw, ok := value["raw"].(float64)
		return raw, ok
	default:
		return 0, false
	}
}

func stringAt(container map[string]interface{}, key string) string {
	text, _ := container[key].(string)
	return text
}

func mapAt(container map[string]interface{}, key string) map[string]interface{} {
	child, _ := container[key].(map[string]interface{})
	return child
}

func sliceAt(container map[string]interface{}, key string) []interface{} {
	child, _ := container[key].([]interface{})
	return child
}

// parseChart reads the v8 chart response. The payload nests as
// chart.result[0].meta, and the price is a number inside meta.
func parseChart(body []byte) (*models.PriceChanges, float64, error) {
	var payload map[string]interface{}
	if err := json.Unmarshal(body, &payload); err != nil {
		return nil, 0, fmt.Errorf("parse chart JSON: %w", err)
	}

	chart := mapAt(payload, "chart")
	if chart == nil {
		return nil, 0, fmt.Errorf("chart response has no 'chart' object")
	}
	if apiErr := mapAt(chart, "error"); apiErr != nil {
		return nil, 0, fmt.Errorf("chart API error: %s", stringAt(apiErr, "description"))
	}

	results := sliceAt(chart, "result")
	if len(results) == 0 {
		return nil, 0, fmt.Errorf("chart response has no results")
	}
	first, ok := results[0].(map[string]interface{})
	if !ok {
		return nil, 0, fmt.Errorf("chart result is not an object")
	}

	meta := mapAt(first, "meta")
	if meta == nil {
		return nil, 0, fmt.Errorf("chart result has no 'meta' object")
	}

	price, ok := numberAt(meta, "regularMarketPrice")
	if !ok {
		return nil, 0, fmt.Errorf("chart meta has no regularMarketPrice")
	}

	changes := &models.PriceChanges{}

	// The 1d change is authoritative in meta, so read it directly.
	if oneDay, ok := numberAt(meta, "regularMarketChangePercent"); ok {
		changes.OneDay = oneDay
	}

	// The longer intervals come from the daily close series. A caller that
	// requests a short range gets no series, which leaves those fields at zero.
	history := extractSeries(first)
	if len(history.times) > 0 {
		asOf := time.Unix(int64(secondsOr(meta, "regularMarketTime", float64(time.Now().Unix()))), 0).UTC()

		if past, ok := history.closeAtOrBefore(asOf.AddDate(0, 0, -7).Unix()); ok {
			changes.OneWeek = percentChange(price, past)
		}
		if past, ok := history.closeAtOrBefore(asOf.AddDate(0, -3, 0).Unix()); ok {
			changes.ThreeM = percentChange(price, past)
		}
		// Year to date measures from the final close of the previous year.
		startOfYear := time.Date(asOf.Year(), time.January, 1, 0, 0, 0, 0, time.UTC)
		if past, ok := history.closeAtOrBefore(startOfYear.Unix() - 1); ok {
			changes.YTD = percentChange(price, past)
		}
	}

	return changes, price, nil
}

// priceSeries holds daily closes paired with their timestamps, oldest first.
// Entries whose close is null in the response are dropped.
type priceSeries struct {
	times  []int64
	closes []float64
}

// closeAtOrBefore returns the most recent close at or before cutoff.
func (s priceSeries) closeAtOrBefore(cutoff int64) (float64, bool) {
	for i := len(s.times) - 1; i >= 0; i-- {
		if s.times[i] <= cutoff {
			return s.closes[i], true
		}
	}
	return 0, false
}

// extractSeries reads the timestamp array and the matching close array from one
// chart result. It returns an empty series when either array is absent.
func extractSeries(result map[string]interface{}) priceSeries {
	timestamps := sliceAt(result, "timestamp")
	quotes := sliceAt(mapAt(result, "indicators"), "quote")
	if len(timestamps) == 0 || len(quotes) == 0 {
		return priceSeries{}
	}
	firstQuote, ok := quotes[0].(map[string]interface{})
	if !ok {
		return priceSeries{}
	}
	closes := sliceAt(firstQuote, "close")

	count := len(timestamps)
	if len(closes) < count {
		count = len(closes)
	}

	series := priceSeries{}
	for i := 0; i < count; i++ {
		stamp, ok := timestamps[i].(float64)
		if !ok {
			continue
		}
		// A market holiday or a halted session gives a null close.
		close, ok := closes[i].(float64)
		if !ok {
			continue
		}
		series.times = append(series.times, int64(stamp))
		series.closes = append(series.closes, close)
	}

	return series
}

// percentChange returns the change from past to current as a percentage.
func percentChange(current, past float64) float64 {
	if past == 0 {
		return 0
	}
	return (current - past) / past * 100
}

// secondsOr reads a numeric field and falls back to fallback when it is absent.
func secondsOr(container map[string]interface{}, key string, fallback float64) float64 {
	if value, ok := numberAt(container, key); ok {
		return value
	}
	return fallback
}

// parseQuoteSummary reads the v10 quoteSummary response. quoteSummary.result is
// an array whose first element holds one object per requested module.
func parseQuoteSummary(body []byte) (*models.EarningsData, error) {
	var payload map[string]interface{}
	if err := json.Unmarshal(body, &payload); err != nil {
		return nil, fmt.Errorf("parse summary JSON: %w", err)
	}

	summary := mapAt(payload, "quoteSummary")
	if summary == nil {
		// An authentication failure comes back under a "finance" key instead.
		if finance := mapAt(payload, "finance"); finance != nil {
			if apiErr := mapAt(finance, "error"); apiErr != nil {
				return nil, fmt.Errorf("summary API error: %s", stringAt(apiErr, "description"))
			}
		}
		return nil, fmt.Errorf("summary response has no 'quoteSummary' object")
	}
	if apiErr := mapAt(summary, "error"); apiErr != nil {
		return nil, fmt.Errorf("summary API error: %s", stringAt(apiErr, "description"))
	}

	results := sliceAt(summary, "result")
	if len(results) == 0 {
		return nil, fmt.Errorf("summary response has no results")
	}
	modules, ok := results[0].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("summary result is not an object")
	}

	earningsData := &models.EarningsData{}

	if chart := mapAt(mapAt(modules, "earnings"), "earningsChart"); chart != nil {
		// Quarters are ordered oldest first, so the last entry is the latest.
		if quarters := sliceAt(chart, "quarterly"); len(quarters) > 0 {
			if latest, ok := quarters[len(quarters)-1].(map[string]interface{}); ok {
				if actual, ok := numberAt(latest, "actual"); ok {
					earningsData.EpsActual = actual
				}
				if estimate, ok := numberAt(latest, "estimate"); ok {
					earningsData.EpsEstimate = estimate
				}
			}
		}
		// The forward estimate, when present, is the more useful figure.
		if estimate, ok := numberAt(chart, "currentQuarterEstimate"); ok {
			earningsData.EpsEstimate = estimate
		}
		if dates := sliceAt(chart, "earningsDate"); len(dates) > 0 {
			if entry, ok := dates[0].(map[string]interface{}); ok {
				if raw, ok := entry["raw"].(float64); ok {
					earningsData.EarningsDate = time.Unix(int64(raw), 0).UTC().Format("2006-01-02")
				}
			}
		}
	}

	return earningsData, nil
}

// parseSearchNews reads the v1 search response, which carries news articles in a
// top level "news" array.
func parseSearchNews(body []byte) ([]*models.NewsItem, error) {
	var payload map[string]interface{}
	if err := json.Unmarshal(body, &payload); err != nil {
		return nil, fmt.Errorf("parse news JSON: %w", err)
	}

	var newsItems []*models.NewsItem
	for _, entry := range sliceAt(payload, "news") {
		article, ok := entry.(map[string]interface{})
		if !ok {
			continue
		}

		item := &models.NewsItem{
			Headline: stringAt(article, "title"),
			Summary:  stringAt(article, "summary"),
			Source:   stringAt(article, "publisher"),
			Url:      stringAt(article, "link"),
		}
		if published, ok := numberAt(article, "providerPublishTime"); ok {
			item.PublishTime = time.Unix(int64(published), 0).UTC().Format(time.RFC3339)
		}
		if item.Headline == "" {
			continue
		}
		newsItems = append(newsItems, item)
	}

	return newsItems, nil
}

// rssFeed models the parts of the Yahoo Finance RSS headline feed that this
// tool reads. The feed is the only Yahoo endpoint that carries an article
// description.
type rssFeed struct {
	Items []struct {
		Title       string `xml:"title"`
		Description string `xml:"description"`
	} `xml:"channel>item"`
}

// parseRSSDescriptions maps each normalised headline in the feed to its
// description. An item without both fields is skipped.
func parseRSSDescriptions(body []byte) (map[string]string, error) {
	var feed rssFeed
	if err := xml.Unmarshal(body, &feed); err != nil {
		return nil, fmt.Errorf("parse news RSS: %w", err)
	}

	descriptions := make(map[string]string, len(feed.Items))
	for _, item := range feed.Items {
		title := normaliseHeadline(item.Title)
		description := strings.TrimSpace(item.Description)
		if title == "" || description == "" {
			continue
		}
		descriptions[title] = description
	}

	return descriptions, nil
}

// normaliseHeadline reduces a headline to a comparison key. The search endpoint
// and the RSS feed punctuate the same headline differently, so the key keeps
// letters and digits only, in lower case.
func normaliseHeadline(headline string) string {
	var builder strings.Builder
	for _, r := range strings.ToLower(headline) {
		if unicode.IsLetter(r) || unicode.IsDigit(r) {
			builder.WriteRune(r)
		}
	}
	return builder.String()
}
