package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"

	"company-analysis/internal/fetcher"
	"company-analysis/internal/models"
	"company-analysis/internal/simulator"
)

func main() {
	ticker := flag.String("ticker", "", "Company ticker symbol (e.g., AAPL, TSLA)")
	flag.Parse()

	if *ticker == "" {
		log.Fatal("ticker argument is required")
	}

	// Price data is mandatory. The simulations below multiply the price, so a
	// substitute value would produce a report that looks correct but is not.
	priceChanges, currentPrice, err := fetcher.FetchPriceData(*ticker)
	if err != nil {
		outputError(*ticker, err.Error())
	}
	if currentPrice <= 0 {
		outputError(*ticker, fmt.Sprintf("price is %v, which is not usable", currentPrice))
	}

	// Fetch summary and earnings data
	earningsData, err := fetcher.FetchSummaryData(*ticker)
	if err != nil {
		log.Printf("warning: failed to fetch summary data: %v, using defaults", err)
		earningsData = &models.EarningsData{}
	}

	// Fetch news
	newsItems, err := fetcher.FetchNews(*ticker)
	if err != nil {
		log.Printf("warning: failed to fetch news: %v, using empty list", err)
		newsItems = nil
	}

	// Run simulations
	quantities := []int{5, 10, 25}
	// Use a hypothetical +10% price change for simulation purposes
	sellPrice := currentPrice * 1.10
	simulationResults := simulator.CalculateSimulations(quantities, currentPrice, sellPrice)

	// Build analysis data
	analysisData := &models.AnalysisData{
		Ticker:       *ticker,
		CurrentPrice: currentPrice,
		PriceChanges: priceChanges,
		EarningsData: earningsData,
		News:         newsItems,
		Simulations:  simulationResults,
	}

	// Output JSON
	outputJSON(analysisData)
}

func outputJSON(data *models.AnalysisData) {
	jsonBytes, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		log.Fatalf("failed to marshal JSON: %v", err)
	}
	fmt.Println(string(jsonBytes))
}

func outputError(ticker, msg string) {
	errorData := &models.AnalysisData{
		Ticker: ticker,
		Error:  msg,
	}
	jsonBytes, err := json.MarshalIndent(errorData, "", "  ")
	if err != nil {
		log.Fatalf("failed to marshal error JSON: %v", err)
	}
	fmt.Println(string(jsonBytes))
	os.Exit(1)
}
