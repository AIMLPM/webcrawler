// Colly benchmark crawler — fetches pages and saves raw HTML for markdownify conversion.
// Usage: go run main.go -url URL -out DIR -max N [-urls FILE]
//
// When -urls FILE is provided, reads URLs from the file (one per line) and fetches those.
// Otherwise, crawls from -url following links up to -max pages.
package main

import (
	"flag"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"sync/atomic"

	"github.com/gocolly/colly/v2"
)

func safeFilename(rawURL string) string {
	s := strings.ReplaceAll(rawURL, "://", "_")
	s = strings.ReplaceAll(s, "/", "_")
	if len(s) > 80 {
		s = s[:80]
	}
	return s
}

func main() {
	baseURL := flag.String("url", "", "Base URL to crawl")
	outDir := flag.String("out", "./colly_output", "Output directory")
	maxPages := flag.Int("max", 50, "Maximum pages to fetch")
	urlsFile := flag.String("urls", "", "File with URLs to fetch (one per line)")
	flag.Parse()

	if *baseURL == "" {
		fmt.Fprintln(os.Stderr, "Usage: go run main.go -url URL -out DIR -max N [-urls FILE]")
		os.Exit(1)
	}

	os.MkdirAll(*outDir, 0755)

	var pageCount int64

	c := colly.NewCollector(
		colly.MaxDepth(3),
		colly.Async(false),
	)

	// Respect robots.txt
	c.AllowURLRevisit = false

	parsedBase, _ := url.Parse(*baseURL)
	baseDomain := parsedBase.Hostname()

	c.OnResponse(func(r *colly.Response) {
		current := atomic.LoadInt64(&pageCount)
		if current >= int64(*maxPages) {
			return
		}

		contentType := r.Headers.Get("Content-Type")
		if !strings.Contains(contentType, "text/html") {
			return
		}

		// Save raw HTML
		filename := safeFilename(r.Request.URL.String()) + ".html"
		htmlPath := filepath.Join(*outDir, filename)
		os.WriteFile(htmlPath, r.Body, 0644)

		atomic.AddInt64(&pageCount, 1)
	})

	if *urlsFile == "" {
		// Discovery mode — follow links
		c.OnHTML("a[href]", func(e *colly.HTMLElement) {
			current := atomic.LoadInt64(&pageCount)
			if current >= int64(*maxPages) {
				return
			}
			link := e.Request.AbsoluteURL(e.Attr("href"))
			if link == "" {
				return
			}
			parsed, err := url.Parse(link)
			if err != nil {
				return
			}
			if parsed.Hostname() == baseDomain {
				e.Request.Visit(link)
			}
		})

		c.Visit(*baseURL)
	} else {
		// Fixed URL list mode
		data, err := os.ReadFile(*urlsFile)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error reading URLs file: %v\n", err)
			os.Exit(1)
		}
		lines := strings.Split(string(data), "\n")
		for _, line := range lines {
			line = strings.TrimSpace(line)
			if line != "" {
				c.Visit(line)
			}
		}
	}

	c.Wait()
	fmt.Printf("%d\n", atomic.LoadInt64(&pageCount))
}
