# Source Strategy

The diary should use a mixed source diet so it does not become a mirror of one platform, country, ideology, or algorithm.

## Approximate daily balance

- 45% global news and historical events
- 20% AI, technology, science, and internet infrastructure
- 15% internet culture and platform life
- 10% economy and ordinary-life indicators
- 5% local vantage point
- 5% archival oddities, human details, and recurring observations

These are guidelines, not quotas.

## Source categories

### Global news

Use a mix of wire services, international outlets, and regional sources. Cross-check major claims across at least two sources when practical.

Examples:

- Reuters
- Associated Press
- BBC
- Al Jazeera
- Financial Times
- The Guardian
- regional and local outlets relevant to the day's events

### Official and primary sources

Prefer primary sources for high-stakes or numerical claims:

- government statistics agencies
- central banks
- courts and election bodies
- UN, WHO, IMF, World Bank
- NASA, NOAA, climate agencies
- company filings and official product announcements
- legislative and regulatory documents

### AI and technology

Track both official announcements and independent reporting:

- OpenAI, Anthropic, Google DeepMind, Meta, Microsoft, Apple, NVIDIA, and other official blogs
- arXiv and major research labs
- GitHub Trending and open-source releases
- Hugging Face
- The Verge, Ars Technica, Wired, TechCrunch, Financial Times tech coverage
- Hacker News and specialist communities as signals, not final authorities

### Internet culture

Use carefully because these sources are noisy and ephemeral:

- platform trending pages where available
- YouTube/TikTok/Spotify charts
- Reddit communities
- Hacker News
- Google Trends
- Know Your Meme
- creator newsletters and public posts

### Local vantage sources

Use sparingly to establish “from here” texture:

- local weather
- exchange rate and fuel/electricity/inflation signals
- local news when globally or culturally relevant
- cricket, exams, Eid/Ramadan, monsoon, power, freelancing, WhatsApp culture, language texture

## Source metadata schema

Each daily source JSON should store:

```json
{
  "date": "YYYY-MM-DD",
  "generated_at": "ISO-8601 timestamp",
  "sources": [
    {
      "id": "stable-id-or-hash",
      "title": "Source title",
      "url": "https://example.com/article",
      "publisher": "Publisher",
      "author": "Author if available",
      "published_at": "ISO-8601 if available",
      "accessed_at": "ISO-8601",
      "category": "global_news | ai_tech | internet_culture | official | local_vantage | economy | other",
      "summary": "Brief original summary, not full article text",
      "archive_url": "Wayback/archive link if available",
      "reliability_note": "Optional note about uncertainty, bias, or cross-checking"
    }
  ]
}
```

## Archival rules

- Save source metadata daily.
- Save article summaries, not full copyrighted text.
- Prefer archive links for fragile pages.
- Preserve access dates.
- Export yearly source indexes.
- Keep plain-text/Markdown/JSON as the canonical long-term formats.
