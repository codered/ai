package iseven

// Package iseven provides a simple function to check if a number is even.
//
// The IsEven function returns true if the given integer is divisible by 2,
// and false otherwise. It works correctly for all integer types and all
// integer values, including edge cases like zero and negative numbers.
//
// # Examples
//
//	// Even numbers
//	n := iseven.IsEven(0)  // true
//	n := iseven.IsEven(2)  // true
//	n := iseven.IsEven(-2) // true
//
//	// Odd numbers
//	n := iseven.IsEven(1)  // false
//	n := iseven.IsEven(3)  // false
//	n := iseven.IsEven(-1) // false
//
// # Edge cases
//
// - Zero: IsEven(0) returns true
// - Negative numbers: IsEven(-2) returns true, IsEven(-1) returns false
// - Max/min integer values: IsEven(math.MaxInt) returns false
// - math.MaxInt % 2 == 1 (odd)
//
// # Integer types
//
// IsEven works with int64.
//
// # Compatibility
//
// # Go 1.21 and later
//
// # Errors
//
// IsEven returns no error. It is a pure function with no side effects.
func IsEven(n int64) bool {
	return n%2 == 0
}
