// =============================================================================
// Monte Carlo pi benchmark — Go (std only), same algorithm as mc_pi.c
// (xorshift64, identical constants, identical per-point work). Goroutines +
// WaitGroup keep the fan-out + join shape; the xorshift is inlined in the hot
// loop so no closure-call overhead is charged to the loop.
//
// Usage: go run mc_pi.go <threads> <points>   (or go build)
// =============================================================================
package main

import (
	"fmt"
	"os"
	"strconv"
	"sync"
	"time"
)

func main() {
	T := 8
	N := int64(200000000)
	if len(os.Args) > 1 {
		if v, err := strconv.Atoi(os.Args[1]); err == nil && v > 0 {
			T = v
		}
	}
	if len(os.Args) > 2 {
		if v, err := strconv.ParseInt(os.Args[2], 10, 64); err == nil && v > 0 {
			N = v
		}
	}
	hits := make([]int64, T)
	var wg sync.WaitGroup
	start := time.Now()
	for i := 0; i < T; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			per := N / int64(T)
			if int64(idx) < N%int64(T) {
				per++
			}
			st := uint64(0x9E3779B97F4A7C15) ^
				(uint64(idx)*0xBF58476D1CE4E5B9 + 0x94D049BB133111EB)
			if st == 0 {
				st = 1
			}
			st ^= st << 13
			st ^= st >> 7
			st ^= st << 17 // three discarded warm-up draws
			st ^= st << 13
			st ^= st >> 7
			st ^= st << 17
			st ^= st << 13
			st ^= st >> 7
			st ^= st << 17
			var h int64
			const scale = 1.0 / 9007199254740992.0
			for k := int64(0); k < per; k++ {
				st ^= st << 13
				st ^= st >> 7
				st ^= st << 17
				x := float64(st>>11) * scale
				st ^= st << 13
				st ^= st >> 7
				st ^= st << 17
				y := float64(st>>11) * scale
				if x*x+y*y <= 1.0 {
					h++
				}
			}
			hits[idx] = h
		}(i)
	}
	wg.Wait()
	ms := float64(time.Since(start).Nanoseconds()) / 1e6
	var H int64
	for _, v := range hits {
		H += v
	}
	fmt.Printf("pi=%.5f threads=%d points=%d ms=%.0f rate=%.4e\n",
		4.0*float64(H)/float64(N), T, N, ms, float64(N)/(ms/1000.0))
}
