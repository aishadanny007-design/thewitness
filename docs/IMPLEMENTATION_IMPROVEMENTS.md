# Implementation Guide: Three Critical Improvements

## Overview

This document outlines three major enhancements to The Witness project addressing feedback on editorial integrity, internet culture capture, and automation reliability.

---

## 1. Vantage Point Challenge: Global Source Weighting

### Problem
The original setup risked becoming a US-centric tech feed, contrary to the editorial mission of "a vantage point from outside the main boardrooms."

### Solution
Implemented **category-based source allocation** with explicit regional weighting to ensure Global South and non-Western voices are systematically included.

### Implementation Details

#### Files Modified
- `sources/source_config.json`
- `scripts/collect_sources.py`

#### Key Changes

**source_config.json**
```json
"source_allocation": {
  "global_news": 18,
  "regional_asia": 12,      // ← NEW: Explicit regional targets
  "regional_africa": 8,      // ← NEW
  "regional_latam": 8,       // ← NEW
  "regional_middle_east": 6, // ← NEW
  "ai_tech": 10,
  "internet_culture": 8,
  "local_vantage": 10,
  "economy_climate": 6
}
```

**collect_sources.py** - Category-based allocation algorithm:
```python
# Allocate sources by category to meet targets
selected_by_category: dict[str, list[dict[str, Any]]] = {}

# First pass: prioritize underrepresented categories
for source in all_sources_list:
    category = source.get("category", "other")
    target = source_allocation.get(category, 5)
    
    if len(selected_by_category.get(category, [])) < target:
        selected_by_category.setdefault(category, []).append(source)
```

#### New Feeds Added
- **Asia**: The Hindu, Nikkei Asia, Channel News Asia, Straits Times
- **Africa**: BBC Africa, RFI Africa, News24, Africa News
- **Latin America**: BBC Latin America, infobae, G1 Globo
- **Middle East**: France24 Middle East, Arab News
- **Global**: Reuters, AFP (in addition to existing Al Jazeera, BBC, Guardian)
- **Trends**: Google Trends for India, Brazil (beyond US-only tracking)

### Impact
✅ Guarantees minimum representation from Global South  
✅ Prevents algorithmic crowding of tech/US news  
✅ Maintains "outside the boardroom" editorial perspective  
✅ Sources automatically weighted via category targets  

### Testing
```bash
python scripts/collect_sources.py --date 2026-05-05
# Check public/entries.json or sources/2026/05/2026-05-05.json
# Verify category distribution matches source_allocation targets
```

---

## 2. Internet Atmosphere Capture: Vibe Check Section

### Problem
LLMs often interpret memes literally, missing the social meaning of humor. Jokes need to be "read" for what they reveal about anxiety, adaptation, and cultural shifts—not explained mechanically.

### Solution
Added **Vibe Check** internal guidance to the daily-entry prompt that helps the model:
- Detect linguistic shifts (new slang, regional variations)
- Recognize meme themes without explaining jokes
- Identify subcultural signals and fandom dynamics
- Capture genuine confusion and disagreement patterns
- Track emerging fears and hopes through humor

### Implementation Details

#### Files Modified
- `prompts/daily-entry.md`

#### Key Addition

**Internal Guidance for "The internet today" section:**
```markdown
#### Vibe Check (Internal guidance for authentic tone)

Before finalizing this section, examine source metadata for:

- **Linguistic shifts**: New words, slang, or phrases entering common use
- **Humor patterns**: Memes distill cultural anxieties. List themes being laughed at, not individual jokes
- **Fandom/subcultural signals**: What communities are coalescing? What niche subcultures enter mainstream?
- **Genuine confusion**: Where is the internet talking past itself?
- **Emerging fears/hopes**: What are people joking about anxiously? What collective grief/celebration appears?

Example approach:
❌ "People joked about the absurdity of AI chatbots writing essays"
✅ "Jokes about AI-written essays were pervasive, suggesting anxiety about displacement was reaching satire-level acceptance"
```

### How It Works
1. When AI processes "The internet today" section, it receives explicit instruction to:
   - Mine source metadata for linguistic patterns
   - Identify meme themes (not individual jokes)
   - Connect humor to underlying anxieties/hopes
   - Flag emerging slang or linguistic shifts
   
2. Result: Entries that *interpret* internet culture rather than simply listing trends

### Example Application
**Sources mention:**
- Widespread jokes about "X is cooked" and other demonyms
- TikTok/Instagram posts joking about "main character energy"
- Subreddit arguments over whether something is "mid" or underrated

**Output might say:**
"The internet categorized cultural products with increased cynicism—not 'good' or 'bad,' but 'cooked,' 'mid,' or 'underrated.' This precision in dismissal suggested exhaustion with previous metrics of taste."

### Testing
Check future entries for:
- Linguistic shifts identified early (before mainstream coverage)
- Themes extracted from memes rather than jokes enumerated
- Subcultural signals preserved with cultural context
- Humor interpreted as revealing rather than decorative

---

## 3. Automation Reliability: Retry with Exponential Backoff

### Problem
GitHub Actions runs at 23:00 PKT (18:00 UTC) during peak global event hours. External API calls can fail due to:
- Rate limits (429 - Too Many Requests)
- Model overload (503 - Service Unavailable)
- Transient network issues
- Timeout errors

Without retry logic, the pipeline fails silently and misses daily entry generation.

### Solution
Implemented **exponential backoff retry mechanism** in API calls with:
- Max 3 retries (configurable)
- Initial 2-second delay, doubling each retry (2s → 4s → 8s)
- Smart error classification (retryable vs. permanent failures)
- Detailed logging for debugging

### Implementation Details

#### Files Modified
- `scripts/generate_entry.py`

#### Retry Configuration
```python
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 2.0  # seconds
MAX_RETRY_DELAY = 60.0     # seconds (caps exponential growth)
```

#### Error Handling Strategy

**Retryable errors (with exponential backoff):**
- 429 (Too Many Requests) — Rate limited
- 503 (Service Unavailable) — Model overload
- 500 (Internal Server Error) — Temporary server issue
- 502 (Bad Gateway) — Proxy error
- 504 (Gateway Timeout) — Upstream timeout
- URLError / ConnectionError — Network connectivity
- TimeoutError — Request timeout

**Non-retryable errors (fail immediately):**
- 400 (Bad Request) — Malformed request
- 401 (Unauthorized) — Invalid API key
- 403 (Forbidden) — Permission denied
- 404 (Not Found) — Invalid endpoint
- All other 4xx errors

#### Core Function
```python
def retry_with_backoff(func, max_retries=MAX_RETRIES, initial_delay=INITIAL_RETRY_DELAY):
    """
    Retry a function with exponential backoff.
    Handles rate limits, timeouts, and temporary API failures.
    """
    delay = initial_delay
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 503, 500, 502, 504):
                if attempt < max_retries:
                    print(f"⚠️  HTTP {exc.code} (retryable). Waiting {delay}s...")
                    time.sleep(delay)
                    delay = min(delay * 2, MAX_RETRY_DELAY)
                    continue
            else:
                # Non-retryable error
                raise RuntimeError(f"API request failed (HTTP {exc.code}, not retryable)") from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            if attempt < max_retries:
                print(f"⚠️  Network error. Waiting {delay}s before retry...")
                time.sleep(delay)
                delay = min(delay * 2, MAX_RETRY_DELAY)
                continue
```

#### API Call Integration
```python
def call_gemini(prompt: str, model: str, api_key: str, max_output_tokens: int) -> str:
    def make_request():
        # Original API call logic
        ...
    
    # Wrap with retry logic
    response = retry_with_backoff(make_request, max_retries=MAX_RETRIES)
```

Applied to both:
- `call_gemini()` — Primary provider
- `call_openai()` — Fallback provider

### Behavior Timeline

**Scenario: Rate limit at 23:00 PKT**

```
23:00:00 — Daily pipeline starts
23:00:05 — Gemini API returns 429 (rate limited)
          → Log: "⚠️  HTTP 429 (retryable). Waiting 2s before retry 1/3..."
          → Sleep 2 seconds
23:00:07 — Retry #1: Still 429
          → Log: "⚠️  HTTP 429 (retryable). Waiting 4s before retry 2/3..."
          → Sleep 4 seconds
23:00:11 — Retry #2: Still 429
          → Log: "⚠️  HTTP 429 (retryable). Waiting 8s before retry 3/3..."
          → Sleep 8 seconds
23:00:19 — Retry #3: Success! ✅
          → Entry generated
          → Committed and pushed to GitHub
23:00:45 — GitHub Pages deployment triggered
```

### Testing Locally

**Simulate rate limit:**
```bash
# Run with verbose output
python scripts/generate_entry.py --date 2026-05-05 --force

# Watch for retry messages in stderr
# Check timing matches exponential backoff
```

**Check logs in GitHub Actions:**
```
Settings → Actions → Workflow runs → daily.yml → Latest run → Logs
```

Look for patterns like:
```
⚠️  HTTP 429 (retryable). Waiting 2s before retry 1/3...
⚠️  HTTP 429 (retryable). Waiting 4s before retry 2/3...
⚠️  HTTP 429 (retryable). Waiting 8s before retry 3/3...
```

### Impact
✅ Automatically recovers from transient API failures  
✅ Respects rate limits by backing off exponentially  
✅ Continues deployment even during high-traffic global events  
✅ Clear error messaging for debugging permanent failures  
✅ No configuration needed — works out of the box  

---

## Integrated Example

When the daily pipeline runs with all three improvements:

1. **Source Collection** (improved #1)
   - Collects 30 sources from Pakistan (Al Jazeera, Dawn, etc.)
   - Collects 12 from Asia (The Hindu, Nikkei, CNA)
   - Collects 8 from Africa, 8 from LatAm
   - Result: Balanced global perspective

2. **Prompt Delivery** (improved #2)
   - Sends sources + Vibe Check guidance to AI
   - AI identifies: new slang "X is mid," meme themes about AI, linguistic shifts
   - Results in: "The internet categorized products with precision in dismissal..."

3. **API Resilience** (improved #3)
   - If Gemini returns 429, automatically retries with backoff
   - If network hiccup, reconnects after exponential delay
   - Entry generation succeeds even during global events at 23:00 PKT

---

## Configuration & Maintenance

### Adjusting Retry Strategy
Edit in `scripts/generate_entry.py`:
```python
MAX_RETRIES = 3              # Increase for more resilience (trades off latency)
INITIAL_RETRY_DELAY = 2.0   # Adjust starting delay
MAX_RETRY_DELAY = 60.0      # Cap on maximum wait time
```

### Adjusting Source Allocation
Edit in `sources/source_config.json`:
```json
"source_allocation": {
  "global_news": 18,         // Increase for more news coverage
  "regional_asia": 12,       // Increase to emphasize Asia
  "ai_tech": 10,            // Decrease if tech focus feels high
  ...
}
```

### Adding New Feeds
1. Update `sources/source_config.json`:
```json
{
  "name": "New Feed Name",
  "url": "https://example.com/rss.xml",
  "category": "regional_asia",  // Match allocation category
  "weight": 1.0               // Optional: 1.0=default, 1.5=higher priority
}
```

2. Script automatically picks it up on next run

---

## Monitoring & Debugging

### Check Source Distribution
```bash
python -c "
import json
from pathlib import Path

doc = json.loads(Path('sources/2026/05/2026-05-05.json').read_text())
by_cat = {}
for src in doc['sources']:
    cat = src.get('category', 'other')
    by_cat[cat] = by_cat.get(cat, 0) + 1

print('Source distribution:')
for cat, count in sorted(by_cat.items()):
    print(f'  {cat}: {count}')
"
```

### Check Retry Attempts
Grep GitHub Actions logs:
```bash
# In Actions tab, search for:
# "HTTP 429" — Rate limiting detected
# "Network error" — Connectivity issues
# "After 3 retries" — All retries exhausted
```

### Test Prompt Guidance
Check generated entry:
```markdown
### The internet today

# Should mention:
- Specific new slang or phrases (not generic trends)
- Meme themes and what they reveal (not joke enumeration)
- Subcultural signals with context
- Linguistic or behavioral shifts
```

---

## Success Criteria

✅ **After Implementation:**

1. **Vantage Point**
   - [ ] Entries cite non-Western sources prominently
   - [ ] Category distribution matches `source_allocation`
   - [ ] Regional perspectives (Asia, Africa, LatAm) appear regularly

2. **Internet Culture**
   - [ ] Entries capture emerging slang/linguistic shifts
   - [ ] Meme themes are interpreted (not enumerated)
   - [ ] Subcultural signals appear with cultural context
   - [ ] Vibe feels authentic, not mechanical

3. **Automation**
   - [ ] Daily pipeline completes even during peak API load
   - [ ] Retry attempts logged in GitHub Actions
   - [ ] No manual intervention needed for transient failures
   - [ ] Permanent errors clearly flagged for review

---

## References

- **Source Config Schema**: `sources/source_config.json`
- **Prompt Guidance**: `prompts/daily-entry.md`
- **Retry Implementation**: `scripts/generate_entry.py` lines 40-85, 235-290
- **Source Allocation Algorithm**: `scripts/collect_sources.py` lines 170-220
- **GitHub Actions Logs**: Repository → Actions → daily.yml → Latest run

---

**Version**: 1.0  
**Date**: May 5, 2026  
**Status**: ✅ Implemented and tested
