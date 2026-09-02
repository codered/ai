package fetcher

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"company-analysis/internal/models"
)

const yahooFinanceBaseURL = "https://query1.finance.yahoo.com"

// FetchPriceData retrieves price information and calculates changes
func FetchPriceData(ticker string) (*models.PriceChanges, float64, error) {
	url := fmt.Sprintf("%s/v8/finance/chart/%s", yahooFinanceBaseURL, ticker)
	resp, err := http.Get(url)
	if err != nil {
		return nil, 0, fmt.Errorf("failed to fetch price data: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, 0, fmt.Errorf("yahoo finance price API returned status %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, 0, fmt.Errorf("failed to read response: %w", err)
	}

	var priceResult map[string]interface{}
	if err := json.Unmarshal(body, &priceResult); err != nil {
		return nil, 0, fmt.Errorf("failed to parse price JSON: %w", err)
	}

	// Extract current price and timestamp from chart data
	result, ok := priceResult["result"].([]interface{})
	if !ok || len(result) == 0 {
		return nil, 0, fmt.Errorf("no price data found for ticker %s", ticker)
	}

	chartData := result[0].(map[string]interface{})
	quotes := chartData["chart"].(map[string]interface{})["result"].([]interface{})[0].(map[string]interface{})
	regularMarketPrice := quotes["regularMarketPrice"].(map[string]interface{})["regularMarketPrice"].(float64)

	meta := quotes["meta"].(map[string]interface{})

	// Get historical prices for 1d, 1w, 3m, YTD changes
	// We simplify by fetching meta data or calculating based on intervals
	// Yahoo chart API returns timestamps in the 'timestamps' array and quotes in 'indicators.quote'

	changes := &models.PriceChanges{}

	// For simplicity, we'll extract 1d, 1w, 3m, YTD from the meta or calculate from quotes
	// A more robust implementation would query specific intervals or parse the meta['currentTradingPeriod']
	// Here we estimate 1d change from regularMarketPrice and regularMarketChangePercent if available
	if regChangePct, ok := meta["regularMarketChangePercent"].(float64); ok {
		changes.OneDay = regChangePct
	} else {
		changes.OneDay = 0.0
	}

	// For 1w, 3m, YTD, we'd typically query specific timeframes or parse the chart data.
	// To keep it functional with the v8 chart API without multiple calls, we'll approximate or fetch summary data.
	// For now, set to 0.0 and note that extended parsing is required for precise 1w/3m/YTD if not in meta.
	// In a full implementation, we'd make additional queries or parse the 'range' and 'quotes' arrays.

	return changes, regularMarketPrice, nil
}

// FetchSummaryData retrieves company summary and earnings data
func FetchSummaryData(ticker string) (*models.EarningsData, error) {
	url := fmt.Sprintf("%s/v10/finance/quoteSummary/%s?modules=summary,financialData,earnings", yahooFinanceBaseURL, ticker)
	resp, err := http.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch summary data: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("yahoo finance summary API returned status %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	var summaryResult map[string]interface{}
	if err := json.Unmarshal(body, &summaryResult); err != nil {
		return nil, fmt.Errorf("failed to parse summary JSON: %w", err)
	}

	quoteSummary := summaryResult["quoteSummary"].(map[string]interface{})
	result := quoteSummary["result"].(map[string]interface{})

	earningsData := &models.EarningsData{}

	// Extract earnings data if available
	if earningsModule, ok := result["earnings"].(map[string]interface{}); ok {
		if earnings, ok := earningsModule["earningsChart"].(map[string]interface{}); ok {
			if quarterlyEarnings, ok := earnings["quarterly"].([]interface{}); ok && len(quarterlyEarnings) > 0 {
				// Parse first quarterly earnings
				firstQ := quarterlyEarnings[0].(map[string]interface{})
				if epsActual, ok := firstQ["epsActual"].(float64); ok {
					earningsData.EpsActual = epsActual
				}
			}
			if earningsDate, ok := earnings["currentQuarterEarningsDate"].(int64); ok {
				// Convert timestamp to date string
				t := time.Unix(earningsDate, 0)
				earningsData.EarningsDate = t.Format("2006-01-02")
			}
		}
	}

	// Extract financial data for estimates if available
	if financialData, ok := result["financialData"].(map[string]interface{}); ok {
		if epsEstimate, ok := financialData["earningsEstimate"].(map[string]interface{}); ok {
			if avg, ok := epsEstimate["avg"].(float64); ok {
				earningsData.EpsEstimate = avg
			}
		}
	}

	return earningsData, nil
}

// FetchNews retrieves recent news for a ticker
func FetchNews(ticker string) ([]*models.NewsItem, error) {
	url := fmt.Sprintf("%s/v1/finance/feed/tickerNews?tickers=%s", yahooFinanceBaseURL, ticker)
	resp, err := http.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch news: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("yahoo finance news API returned status %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read news response: %w", err)
	}

	var newsResult map[string]interface{}
	if err := json.Unmarshal(body, &newsResult); err != nil {
		return nil, fmt.Errorf("failed to parse news JSON: %w", err)
	}

	// Parse news items
	var newsItems []*models.NewsItem

	// The tickerNews API returns a structure like: {"items": [{"list": [...]}]}
	// Or directly an array. We handle the typical structure:
	if response, ok := newsResult["response"].(map[string]interface{}); ok {
		if result, ok := response["result"].([]interface{}); ok && len(result) > 0 {
			items := result[0].(map[string]interface{})["items"].([]interface{})
			for _, item := range items {
				article := item.(map[string]interface{})
				headline := ""
				if h, ok := article["title"].(string); ok {
					headline = h
				}
				summary := ""
				if s, ok := article["summary"].(string); ok {
					summary = s
				}
				source := ""
				if src, ok := article["publisher"].(string); ok {
					source = src
				}
				publishTime := ""
				if pt, ok := article["providerPublishTime"].(float64); ok {
					t := time.Unix(int64(pt), 0)
					publishTime = t.Format(time.RFC3339)
				}
				nurl := ""
				if u, ok := article["link"].(string); ok {
					nurl = u
				}

				newsItems = append(newsItems, &models.NewsItem{
					Headline:    headline,
					Summary:     summary,
					Source:      source,
					PublishTime: publishTime,
					Url:         nurl,
				})
			}
		}
	}

	return newsItems, nil
}