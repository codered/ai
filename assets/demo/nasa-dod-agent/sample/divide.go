package sample

// Divide returns a / b.
//
// P0: no check for a zero divisor before dividing. Divide(10, 0) panics at
// runtime — exactly the kind of unguarded operation NASA/DOD review flags
// as a crash risk.
func Divide(a, b int) int {
	return a / b
}
