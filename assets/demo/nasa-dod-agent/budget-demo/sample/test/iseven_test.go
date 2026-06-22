package test

import (
	"fmt"
	"math"
	"testing"

	"github.com/user/iseven"
)

func TestIsEven_basicEven(t *testing.T) {
	tests := []int64{0, 2, 4, 6, 8, 10}
	for _, n := range tests {
		t.Run(fmt.Sprintf("IsEven(%d)", n), func(t *testing.T) {
			if !iseven.IsEven(n) {
				t.Errorf("IsEven(%d) = %v, want true", n, iseven.IsEven(n))
			}
		})
	}
}

func TestIsEven_basicOdd(t *testing.T) {
	tests := []int64{1, 3, 5, 7, 9}
	for _, n := range tests {
		t.Run(fmt.Sprintf("IsEven(%d)", n), func(t *testing.T) {
			if iseven.IsEven(n) {
				t.Errorf("IsEven(%d) = %v, want false", n, iseven.IsEven(n))
			}
		})
	}
}

func TestIsEven_zero(t *testing.T) {
	if !iseven.IsEven(0) {
		t.Errorf("IsEven(0) = %v, want true", iseven.IsEven(0))
	}
}

func TestIsEven_negativeEven(t *testing.T) {
	tests := []int64{-2, -4, -6, -8, -10}
	for _, n := range tests {
		t.Run(fmt.Sprintf("IsEven(%d)", n), func(t *testing.T) {
			if !iseven.IsEven(n) {
				t.Errorf("IsEven(%d) = %v, want true", n, iseven.IsEven(n))
			}
		})
	}
}

func TestIsEven_negativeOdd(t *testing.T) {
	tests := []int64{-1, -3, -5, -7, -9}
	for _, n := range tests {
		t.Run(fmt.Sprintf("IsEven(%d)", n), func(t *testing.T) {
			if iseven.IsEven(n) {
				t.Errorf("IsEven(%d) = %v, want false", n, iseven.IsEven(n))
			}
		})
	}
}

func TestIsEven_negativeLarge(t *testing.T) {
	tests := []int64{-100, -200, -1000, -10000}
	for _, n := range tests {
		t.Run(fmt.Sprintf("IsEven(%d)", n), func(t *testing.T) {
			if !iseven.IsEven(n) {
				t.Errorf("IsEven(%d) = %v, want true", n, iseven.IsEven(n))
			}
		})
	}
}

func TestIsEven_maxInt(t *testing.T) {
	// math.MaxInt - 1 is even (9223372036854775807 - 1 = 9223372036854775806 % 2 == 0)
	if !iseven.IsEven(math.MaxInt - 1) {
		t.Errorf("IsEven(math.MaxInt - 1) = %v, want true", iseven.IsEven(math.MaxInt-1))
	}
}

func TestIsEven_minInt(t *testing.T) {
	if !iseven.IsEven(math.MinInt64) {
		t.Errorf("IsEven(math.MinInt) = %v, want true", iseven.IsEven(math.MinInt))
	}
}

func TestIsEven_maxInt_minus_1(t *testing.T) {
	// math.MaxInt - 1 is even (2147483647 - 1 = 2147483646 % 2 == 0)
	if !iseven.IsEven(math.MaxInt - 1) {
		t.Errorf("IsEven(math.MaxInt - 1) = %v, want true", iseven.IsEven(math.MaxInt-1))
	}
}

func TestIsEven_minInt_plus_1(t *testing.T) {
	// math.MinInt + 1 is odd (2147483648 + 1 = 2147483649 % 2 == 1)
	if iseven.IsEven(math.MinInt + 1) {
		t.Errorf("IsEven(math.MinInt + 1) = %v, want false", iseven.IsEven(math.MinInt+1))
	}
}

func TestIsEven_maxUint(t *testing.T) {
	// MaxUint is odd (4294967295 % 2 == 1)
	const MaxUint = 4294967295
	actual := iseven.IsEven(MaxUint)
	if iseven.IsEven(MaxUint) {
		t.Errorf("IsEven(%d) = %v, want false", MaxUint, actual)
	}
}

func TestIsEven_minUint(t *testing.T) {
	// 0 is even (0 % 2 == 0)
	if !iseven.IsEven(0) {
		t.Errorf("IsEven(0) = %v, want true", iseven.IsEven(0))
	}
}

func TestIsEven_uint(t *testing.T) {
	tests := []uint{0, 2, 4, 6, 8, 10, 100, 1000, 10000}
	for _, n := range tests {
		t.Run(fmt.Sprintf("IsEven(uint(%d))", n), func(t *testing.T) {
			if !iseven.IsEven(int(n)) {
				t.Errorf("IsEven(uint(%d)) = %v, want true", n, true)
			}
		})
	}
}

func TestIsEven_maxUint(t *testing.T) {
	// math.MaxUint is always odd
	if iseven.IsEven(math.MaxUint) {
		t.Errorf("IsEven(math.MaxUint) = %v, want false", iseven.IsEven(math.MaxUint))
	}
}
