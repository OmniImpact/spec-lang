// =============================================================================
// Binary-trees benchmark — Go (goroutines + sync.WaitGroup).
// Usage: bt_go <threads> <max_depth>
// Build: go build -o bt_go bt.go
// =============================================================================
package main

import (
	"fmt"
	"os"
	"strconv"
	"sync"
	"time"
)

type Node struct {
	left, right *Node
}

func makeTree(depth int) *Node {
	if depth <= 0 {
		return &Node{}
	}
	return &Node{left: makeTree(depth - 1), right: makeTree(depth - 1)}
}

func checkTree(n *Node) int64 {
	if n.left == nil {
		return 1
	}
	return 1 + checkTree(n.left) + checkTree(n.right)
}

func main() {
	t := 1
	maxDepth := 18
	if len(os.Args) > 1 {
		if v, err := strconv.Atoi(os.Args[1]); err == nil {
			t = v
		}
	}
	if len(os.Args) > 2 {
		if v, err := strconv.Atoi(os.Args[2]); err == nil {
			maxDepth = v
		}
	}
	if t < 1 {
		t = 1
	}
	const minDepth = 4
	if maxDepth < minDepth+2 {
		maxDepth = minDepth + 2
	}

	t0 := time.Now()
	var totalChecks int64

	stretch := makeTree(maxDepth + 1)
	totalChecks += checkTree(stretch)
	stretch = nil

	longLived := makeTree(maxDepth)

	for d := minDepth; d <= maxDepth; d += 2 {
		iterations := int64(1) << (maxDepth - d + minDepth)
		if t <= 1 {
			for i := int64(0); i < iterations; i++ {
				tree := makeTree(d)
				totalChecks += checkTree(tree)
			}
		} else {
			sums := make([]int64, t)
			base := iterations / int64(t)
			rem := iterations % int64(t)
			var wg sync.WaitGroup
			wg.Add(t)
			for i := 0; i < t; i++ {
				cnt := base
				if int64(i) < rem {
					cnt++
				}
				go func(idx int, c int64, depth int) {
					defer wg.Done()
					var ls int64
					for k := int64(0); k < c; k++ {
						ls += checkTree(makeTree(depth))
					}
					sums[idx] = ls
				}(i, cnt, d)
			}
			wg.Wait()
			for _, s := range sums {
				totalChecks += s
			}
		}
	}

	totalChecks += checkTree(longLived)

	ms := float64(time.Since(t0).Nanoseconds()) / 1e6
	if ms < 1.0 {
		ms = 1.0
	}
	fmt.Printf("checksum=%d threads=%d depth=%d ms=%.0f rate=%.4e\n",
		totalChecks, t, maxDepth, ms, float64(totalChecks)/(ms/1000.0))
}
