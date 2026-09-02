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

	// Fetch price data
	priceChanges, currentPrice, err := fetcher.FetchPriceData(*ticker)
	if err != nil {
		outputError(fmt.Sprintf("failed to fetch price data: %v", err))
		return
	}

	// Fetch summary and earnings data
	earningsData, err := fetcher.FetchSummaryData(*ticker)
	if err != nil {
		log.Printf("warning: failed to fetch summary data: %v", err)
		// Continue without earnings data
	}

	// Fetch news
	newsItems, err := fetcher.FetchNews(*ticker)
	if err != nil {
		log.Printf("warning: failed to fetch news: %v", err)
		// Continue without news
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

func outputError(msg string) {
	errorData := &models.AnalysisData{
		Error: msg,
	}
	jsonBytes, err := json.MarshalIndent(errorData, "", "  ")
	if err != nil {
		log.Fatalf("failed to marshal error JSON: %v", err)
	}
	fmt.Println(string(jsonBytes))
	os.Exit(1)
}