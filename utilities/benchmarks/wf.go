// =============================================================================
// Word/log-line frequency benchmark — Go (strings.Split + map[string]int64).
// Usage: wf_go [count]
// Build: go build -o wf_go wf.go
// =============================================================================
package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"
)

func rngNext(st *uint64) uint64 {
	s := *st
	s ^= s << 13
	s ^= s >> 7
	s ^= s << 17
	*st = s
	return s
}

func main() {
	count := int64(1000000)
	if len(os.Args) > 1 {
		if v, err := strconv.ParseInt(os.Args[1], 10, 64); err == nil {
			count = v
		}
	}
	if count < 1 {
		count = 1
	}

	services := [16]string{
		"auth", "api", "billing", "cache",
		"db", "edge", "feed", "gateway",
		"ingest", "jobs", "kv", "logs",
		"metrics", "notify", "proxy", "search",
	}
	levels := [3]string{"INFO", "WARN", "ERR"}

	st := uint64(0x9E3779B97F4A7C15)
	rngNext(&st); rngNext(&st); rngNext(&st)

	counts := make(map[string]int64)
	t0 := time.Now()

	for i := int64(0); i < count; i++ {
		r1 := rngNext(&st) & 15
		r2 := (rngNext(&st) & 0x7FFFFFFF) % 3
		r3 := (rngNext(&st) & 0x7FFFFFFF) % 500

		line := services[r1] + ":" + levels[r2] + ":" + strconv.FormatUint(r3, 10)
		parts := strings.Split(line, ":")
		code, _ := strconv.ParseInt(parts[2], 10, 64)
		bucket := code & 63
		key := parts[0] + ":" + parts[1] + ":" + strconv.FormatInt(bucket, 10)
		counts[key]++
	}

	var total, maxCount int64
	for _, v := range counts {
		total += v
		if v > maxCount {
			maxCount = v
		}
	}

	ms := float64(time.Since(t0).Nanoseconds()) / 1e6
	if ms < 1.0 {
		ms = 1.0
	}
	fmt.Printf("unique=%d total=%d max=%d count=%d ms=%.0f rate=%.4e\n",
		len(counts), total, maxCount, count, ms, float64(count)/(ms/1000.0))
}
