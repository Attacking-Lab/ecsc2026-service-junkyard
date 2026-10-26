package main

import (
	"fmt"
	"os"
	"time"
)

// main is ignored in the c-shared library. As executable, it precomputes the dictionary index:
//
//	go run . build-index <language dir> <index file>
func main() {
	if len(os.Args) != 4 || os.Args[1] != "build-index" {
		fmt.Fprintln(os.Stderr, "usage: spellchecker build-index <language dir> <index file>")
		os.Exit(2)
	}
	start := time.Now()
	languages, err := BuildIndex(os.Args[2], os.Args[3])
	if err != nil {
		fmt.Fprintln(os.Stderr, "build-index failed:", err)
		os.Exit(1)
	}
	fmt.Printf("Built %s with %d languages in %.2f seconds\n", os.Args[3], len(languages), time.Since(start).Seconds())
}
