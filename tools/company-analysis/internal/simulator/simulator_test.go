package simulator

import (
	"testing"

	"company-analysis/internal/models"
)

func TestCalculateSimulations(t *testing.T) {
	currentPrice := 150.0

	// Test cases for quantities 5, 10, 25
	quantities := []int{5, 10, 25}

	// Simulate a hypothetical price change or holding period return.
	// For the simulation, we assume a hypothetical +10% price change at sell time.
	sellPrice := currentPrice * 1.10

	results := CalculateSimulations(quantities, currentPrice, sellPrice)

	if len(results) == 0 {
		t.Fatal("expected non-empty simulation results")
	}

	// Verify a result for quantity 5 with Robinhood/Vanguard fee scenario and Short-term tax
	var result5RobinhoodShort *models.SimulationResult
	for _, r := range results {
		if r.Quantity == 5 && r.FeeScenario == "Robinhood/Vanguard" && r.TaxScenario == "Short-term" {
			result5RobinhoodShort = r
			break
		}
	}

	if result5RobinhoodShort == nil {
		t.Fatal("expected Robinhood/Vanguard Short-term result for quantity 5")
	}

	// Calculate expected values manually:
	// Buy cost = 5 * 150.0 = 750.0
	// Sell revenue = 5 * 165.0 = 825.0
	// Gross profit = 825.0 - 750.0 = 75.0
	// Fees (Robinhood) = 0.0
	// Taxes (Short-term 24%) = 75.0 * 0.24 = 18.0
	// Net profit = 75.0 - 0.0 - 18.0 = 57.0

	expectedPurchaseCost := 750.0
	expectedGrossProfit := 75.0
	expectedFees := 0.0
	expectedTaxes := 75.0 * 0.24
	expectedNetProfit := 75.0 - 0.0 - expectedTaxes

	if result5RobinhoodShort.PurchaseCost != expectedPurchaseCost {
		t.Errorf("expected purchase cost %v, got %v", expectedPurchaseCost, result5RobinhoodShort.PurchaseCost)
	}

	if result5RobinhoodShort.GrossProfit != expectedGrossProfit {
		t.Errorf("expected gross profit %v, got %v", expectedGrossProfit, result5RobinhoodShort.GrossProfit)
	}

	if result5RobinhoodShort.Fees != expectedFees {
		t.Errorf("expected fees %v, got %v", expectedFees, result5RobinhoodShort.Fees)
	}

	if result5RobinhoodShort.Taxes != expectedTaxes {
		t.Errorf("expected taxes %v, got %v", expectedTaxes, result5RobinhoodShort.Taxes)
	}

	if result5RobinhoodShort.NetProfit != expectedNetProfit {
		t.Errorf("expected net profit %v, got %v", expectedNetProfit, result5RobinhoodShort.NetProfit)
	}
}
