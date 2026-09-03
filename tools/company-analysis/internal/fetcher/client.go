package fetcher

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"net/http/cookiejar"
	"strings"
	"sync"
	"time"

	"golang.org/x/time/rate"
)

// browserUserAgent identifies requests as a browser. Yahoo Finance rejects the
// default Go user agent ("Go-http-client/1.1") with HTTP 429 on every call.
const browserUserAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) " +
	"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

const (
	yahooFinanceBaseURL = "https://query1.finance.yahoo.com"
	// yahooCookieURL sets the session cookie that the crumb endpoint requires.
	yahooCookieURL = "https://fc.yahoo.com/"
	yahooCrumbURL  = yahooFinanceBaseURL + "/v1/test/getcrumb"
	// yahooRSSHeadlineURL serves the only feed that carries article summaries.
	yahooRSSHeadlineURL = "https://feeds.finance.yahoo.com/rss/2.0/headline"
)

const (
	maxRetries    = 3
	retryDelay    = 3 * time.Second
	clientTimeout = 15 * time.Second
)

// yahooClient performs rate limited, retrying requests against Yahoo Finance.
// It holds the cookie jar and the crumb token that the quoteSummary API needs.
type yahooClient struct {
	http    *http.Client
	limiter *rate.Limiter

	crumbOnce sync.Once
	crumb     string
	crumbErr  error
}

// defaultClient is the shared client. One cookie jar serves all fetchers.
var defaultClient = newYahooClient()

func newYahooClient() *yahooClient {
	jar, err := cookiejar.New(nil)
	if err != nil {
		// cookiejar.New only fails on a bad PublicSuffixList, which is nil here.
		panic(fmt.Sprintf("cookiejar: %v", err))
	}
	return &yahooClient{
		http:    &http.Client{Jar: jar, Timeout: clientTimeout},
		limiter: rate.NewLimiter(rate.Every(1*time.Second), 2),
	}
}

// get fetches url and returns the response body. It retries HTTP 429 and 503
// with exponential backoff.
func (c *yahooClient) get(ctx context.Context, url string) ([]byte, error) {
	var lastErr error
	attempts := 0

	for attempt := 0; attempt < maxRetries; attempt++ {
		if err := c.limiter.Wait(ctx); err != nil {
			return nil, fmt.Errorf("rate limiter: %w", err)
		}

		attempts++
		body, retryable, err := c.doOnce(ctx, url)
		if err == nil {
			return body, nil
		}
		lastErr = err
		if !retryable || attempt == maxRetries-1 {
			break
		}
		select {
		case <-time.After(retryDelay * time.Duration(1<<attempt)):
		case <-ctx.Done():
			return nil, ctx.Err()
		}
	}

	// Report the attempt count only when a retry actually occurred. A permanent
	// failure such as HTTP 404 stops after the first try.
	if attempts > 1 {
		return nil, fmt.Errorf("after %d attempts: %w", attempts, lastErr)
	}
	return nil, lastErr
}

// doOnce performs a single request. The bool reports whether a retry can help.
func (c *yahooClient) doOnce(ctx context.Context, url string) ([]byte, bool, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, false, fmt.Errorf("build request: %w", err)
	}
	req.Header.Set("User-Agent", browserUserAgent)
	req.Header.Set("Accept", "application/json,text/plain,*/*")

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, true, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		retryable := resp.StatusCode == http.StatusTooManyRequests ||
			resp.StatusCode == http.StatusServiceUnavailable
		return nil, retryable, fmt.Errorf("yahoo finance returned status %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, true, fmt.Errorf("read response: %w", err)
	}
	return body, false, nil
}

// getCrumb returns the crumb token required by the quoteSummary API. It primes
// the cookie jar first, then caches the token for the life of the process.
func (c *yahooClient) getCrumb(ctx context.Context) (string, error) {
	c.crumbOnce.Do(func() {
		// This request returns HTTP 404 but sets the session cookie. Ignore the
		// status and keep whatever cookie the jar received.
		if req, err := http.NewRequestWithContext(ctx, http.MethodGet, yahooCookieURL, nil); err == nil {
			req.Header.Set("User-Agent", browserUserAgent)
			if resp, err := c.http.Do(req); err == nil {
				io.Copy(io.Discard, resp.Body)
				resp.Body.Close()
			}
		}

		body, err := c.get(ctx, yahooCrumbURL)
		if err != nil {
			c.crumbErr = fmt.Errorf("fetch crumb: %w", err)
			return
		}
		// A valid crumb is a short opaque token. Error pages such as
		// "Too Many Requests" arrive with HTTP 200 in some cases, so reject
		// any body that contains whitespace.
		crumb := string(body)
		if crumb == "" || len(crumb) > 64 || strings.ContainsAny(crumb, " \t\r\n") {
			c.crumbErr = fmt.Errorf("unexpected crumb response: %q", crumb)
			return
		}
		c.crumb = crumb
	})

	return c.crumb, c.crumbErr
}
