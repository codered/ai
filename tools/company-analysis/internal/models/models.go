package models

// AnalysisData is the structured JSON payload output by the Go tool
type AnalysisData struct {
	Ticker         string            `json:"ticker"`
	CurrentPrice   float64           `json:"current_price"`
	PriceChanges   *PriceChanges     `json:"price_changes"`
	EarningsData   *EarningsData     `json:"earnings_data,omitempty"`
	News           []*NewsItem       `json:"news,omitempty"`
	Simulations    []*SimulationResult `json:"simulations,omitempty"`
	Error          string            `json:"error,omitempty"`
}

// PriceChanges represents stock performance metrics
type PriceChanges struct {
	OneDay  float64 `json:"1d"`
	OneWeek float64 `json:"1w"`
	ThreeM  float64 `json:"3m"`
	YTD     float64 `json:"ytd"`
}

// EarningsData represents recent earnings information
type EarningsData struct {
	EpsEstimate       float64 `json:"eps_estimate,omitempty"`
	EpsActual         float64 `json:"eps_actual,omitempty"`
	EarningsDate      string  `json:"earnings_date,omitempty"`
	RevenueEstimate   float64 `json:"revenue_estimate,omitempty"`
}

// NewsItem represents a single news article
type NewsItem struct {
	Headline    string `json:"headline"`
	Summary     string `json:"summary"`
	Source      string `json:"source"`
	PublishTime string `json:"publish_time"`
	Url         string `json:"url,omitempty"`
}

// SimulationInput represents parameters for the simulation engine
type SimulationInput struct {
	Quantity int     `json:"quantity"`
	Price    float64 `json:"price"`
}

// SimulationResult represents the outcome of a simulation scenario
type SimulationResult struct {
	Quantity       int     `json:"quantity"`
	FeeScenario    string  `json:"fee_scenario"` // "Robinhood/Vanguard" or "Traditional Broker"
	TaxScenario    string  `json:"tax_scenario"` // "Short-term" or "Long-term"
	GrossProfit    float64 `json:"gross_profit"`
	Fees           float64 `json:"fees"`
	Taxes          float64 `json:"taxes"`
	NetProfit      float64 `json:"net_profit"`
}