package simulator

import (
	"company-analysis/internal/models"
)

const (
	FeeRobinhood     = 0.0
	FeeTraditional   = 4.95
	TaxShortTerm     = 0.24
	TaxLongTerm      = 0.15
)

// CalculateSimulations generates simulation results for given quantities and price points
func CalculateSimulations(quantities []int, currentPrice float64, sellPrice float64) []*models.SimulationResult {
	var results []*models.SimulationResult

	feeScenarios := []struct {
		Name string
		Fee  float64
	}{
		{"Robinhood/Vanguard", FeeRobinhood},
		{"Traditional Broker", FeeTraditional},
	}

	taxScenarios := []struct {
		Name string
		Rate float64
	}{
		{"Short-term", TaxShortTerm},
		{"Long-term", TaxLongTerm},
	}

	for _, qty := range quantities {
		buyCost := float64(qty) * currentPrice
		sellRevenue := float64(qty) * sellPrice
		grossProfit := sellRevenue - buyCost

		for _, fs := range feeScenarios {
			// Fee is applied to both buy and sell transactions
			fees := fs.Fee * 2.0

			for _, ts := range taxScenarios {
				taxes := 0.0
				if grossProfit > 0 {
					taxes = grossProfit * ts.Rate
				}

				netProfit := grossProfit - fees - taxes

				results = append(results, &models.SimulationResult{
					Quantity:    qty,
					FeeScenario: fs.Name,
					TaxScenario: ts.Name,
					GrossProfit: grossProfit,
					Fees:        fees,
					Taxes:       taxes,
					NetProfit:   netProfit,
				})
			}
		}
	}

	return results
}