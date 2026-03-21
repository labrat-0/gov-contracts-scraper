# Government Contracts Scraper

Search federal contract opportunities, awards, and agencies from SAM.gov -- structured, filterable, and ready for analysis. MCP-ready for AI agent integration.

## What does it do?

Government Contracts Scraper pulls structured data from the SAM.gov public API, the official source for all U.S. federal contracting opportunities. You provide a free SAM.gov API key and search filters, and it returns clean, structured contract data. Returns consistent JSON -- ready for analysis, GovTech pipelines, or consumption by AI agents via MCP.

**Use cases:**

- **Government contracting** -- find open solicitations matching your capabilities, NAICS codes, or set-aside categories
- **Competitive intelligence** -- track which agencies are awarding contracts and to whom
- **Market research** -- analyze federal spending patterns by agency, industry code, or region
- **Business development** -- identify upcoming opportunities before competitors
- **Policy research** -- study procurement trends, small business set-asides, and agency spending
- **AI agent tooling** -- expose as an MCP tool so AI agents can search federal contracts, track awards, and monitor procurement activity in real time

## Features

- **3 modes:** search opportunities, search awards, and federal entity lookup
- **Rich filtering:** keyword, NAICS code, PSC code, set-aside type, state, ZIP, agency, date ranges, solicitation number
- **9 procurement types:** solicitations, pre-solicitations, combined synopsis, sources sought, awards, special notices, and more
- **14 small business set-aside filters:** 8(a), HUBZone, SDVOSB, WOSB, EDWOSB, and more
- **Contact extraction:** primary contact name, email, and phone from each opportunity
- **Place of performance** data (city, state, ZIP, country)
- **Award details** for contract awards (awardee name, amount, date, UEI)
- **Automatic pagination** through SAM.gov results (up to 10,000 records)
- **Rate limiting** built in (1-second interval between requests)
- **Retry logic** with exponential backoff on failures
- **State persistence** -- survives Apify actor migrations mid-run
- **No proxies needed** -- SAM.gov is a government API with no anti-bot measures

## Prerequisites

You need a free SAM.gov public API key:

1. Go to [sam.gov](https://sam.gov) and create an account (or sign in)
2. Navigate to your Account Details page
3. Request a **Public API Key** (instant, no approval needed)
4. Paste the key into the scraper's `apiKey` input field

## What data does it extract?

**Opportunities and Awards:**

| Field | Description |
|-------|-------------|
| `type` | Procurement type (Solicitation, Pre-solicitation, Award Notice, etc.) |
| `noticeId` | SAM.gov notice ID |
| `title` | Opportunity title |
| `solicitationNumber` | Solicitation/contract number |
| `department` | Full agency path (e.g. "DEPT OF DEFENSE.DEPT OF THE ARMY...") |
| `agency` | Most specific agency name |
| `postedDate` | Date posted |
| `responseDeadline` | Response/offer deadline |
| `archiveDate` | Archive date |
| `active` | Whether the opportunity is currently active |
| `naicsCode` | NAICS industry code |
| `classificationCode` | Product Service Code (PSC) |
| `setAside` | Small business set-aside description |
| `placeOfPerformance` | City, state, ZIP, country |
| `contactName` | Primary point of contact name |
| `contactEmail` | Contact email |
| `contactPhone` | Contact phone |
| `officeAddress` | Contracting office city, state, ZIP |
| `descriptionUrl` | Link to full description |
| `uiLink` | Direct link to SAM.gov listing |
| `awardDate` | Award date (award notices only) |
| `awardNumber` | Award contract number (award notices only) |
| `awardAmount` | Award dollar amount (award notices only) |
| `awardeeName` | Winning contractor name (award notices only) |
| `awardeeUei` | Winning contractor UEI (award notices only) |

**Organizations (Entity Lookup mode):**

| Field | Description |
|-------|-------------|
| `type` | Always `"organization"` |
| `orgKey` | Organization key |
| `name` | Organization name |
| `code` | Organization code (use this in search filters) |
| `level` | Hierarchy level |
| `parentName` | Parent organization name |
| `parentCode` | Parent organization code |
| `description` | Organization description |
| `cgac` | CGAC code |

---

## 👥 Who Uses This

### 🏢 GovCon Business Development Teams

BD teams at small and mid-sized contractors live on SAM.gov. The problem is that monitoring it manually — checking daily, filtering by your NAICS codes and set-asides, tracking response deadlines — is tedious and error-prone. This actor automates that pipeline.

- Pull all new solicitations in your NAICS code posted in the last 7 days, filtered to your target state
- Monitor specific agencies by `organizationCode` to catch releases the moment they post
- Filter to your set-aside category (SBA, 8(a), SDVOSB) to see only opps your business qualifies for
- Feed results into a CRM or BD tracker automatically via the Apify API

```json
{
    "apiKey": "YOUR_SAM_GOV_API_KEY",
    "mode": "search_opportunities",
    "naicsCode": "541512",
    "setAside": "SBA",
    "state": "VA",
    "postedFrom": "03/14/2026",
    "postedTo": "03/21/2026",
    "maxResults": 200
}
```

### 📋 Proposal & Capture Managers

Before you write a proposal, you need to know who you're competing against and what the government has paid for similar work. Award notices tell you exactly that.

- Research who won past awards on similar contracts — awardee name, UEI, award amount
- Identify which agencies are actively awarding in your space and what they paid
- Find the contracting officers and POC emails to make warm calls before the next solicitation
- Track a specific contract vehicle or solicitation number through its lifecycle

```json
{
    "apiKey": "YOUR_SAM_GOV_API_KEY",
    "mode": "search_awards",
    "keyword": "cloud infrastructure",
    "naicsCode": "541519",
    "postedFrom": "01/01/2025",
    "postedTo": "03/21/2026",
    "maxResults": 500
}
```

### 🏷️ Small Business Set-Aside Seekers

If your business has an 8(a) certification, SDVOSB status, or HUBZone designation, set-aside contracts are your competitive advantage. Finding them shouldn't require constant manual SAM.gov sessions.

- Filter exclusively to your set-aside category so every result is an opp you qualify for
- Stack filters: set-aside + NAICS + state to get a highly targeted shortlist
- Monitor response deadlines to build a prioritized action queue
- Compare award amounts across similar set-aside contracts to calibrate your pricing

```json
{
    "apiKey": "YOUR_SAM_GOV_API_KEY",
    "mode": "search_opportunities",
    "setAside": "SDVOSBC",
    "naicsCode": "541611",
    "maxResults": 300
}
```

### 🔍 GovCon Consultants & BD Advisors

Consultants tracking pipelines for multiple clients need to run different searches for each client's NAICS codes, certifications, and target agencies — and do it consistently. One actor call per client, scheduled via the Apify API.

- Run per-client searches by NAICS + set-aside combination and export results separately
- Use Entity Lookup mode to find the correct agency `organizationCode` for targeted searches
- Track award activity in a client's vertical to benchmark win rates and pricing
- Pull sources sought notices early — the best capture happens before a solicitation drops

```json
{
    "apiKey": "YOUR_SAM_GOV_API_KEY",
    "mode": "entity_lookup",
    "organizationName": "Air Force",
    "maxResults": 50
}
```

### 📊 Market Researchers & Policy Analysts

Federal procurement data is one of the richest public datasets for understanding government spending priorities, regional economic activity, and small business policy outcomes.

- Analyze award volumes by agency and NAICS code to map where federal IT, services, or construction spending is concentrated
- Track small business set-aside usage across agencies to study policy compliance
- Study procurement type distribution (solicitations vs. sole-source justifications) in a specific industry
- Monitor multi-year spending trends by filtering date ranges and aggregating award amounts

```json
{
    "apiKey": "YOUR_SAM_GOV_API_KEY",
    "mode": "search_awards",
    "naicsCode": "336411",
    "postedFrom": "01/01/2024",
    "postedTo": "03/21/2026",
    "maxResults": 1000
}
```

---

## 🔗 Related Actors

Other actors from the same portfolio that complement federal procurement research:

| Actor | What It Does |
|---|---|
| [Clinical Trial Site Contact Finder](https://apify.com/labrat011/clinical-trial-site-contact-finder) | Find PI contacts from ClinicalTrials.gov — useful for health agency contracts |
| [NPI Provider Contact Finder](https://apify.com/labrat011/npi-provider-contact-finder) | Healthcare provider contacts from NPPES — pairs with VA and HHS contract research |
| [SEC EDGAR Scraper](https://apify.com/labrat011/sec-edgar-scraper) | Financial filings for researching awardee companies before teaming or bidding |
| [PubMed Scraper](https://apify.com/labrat011/pubmed-scraper) | Biomedical literature — useful alongside NIH and DoD health research contracts |

---

## Input

Choose a scraping mode and provide your SAM.gov API key along with any search filters.

### Mode 1: Search Opportunities

Search for open contract opportunities (solicitations, pre-solicitations, sources sought, etc.).

```json
{
    "apiKey": "YOUR_SAM_GOV_API_KEY",
    "mode": "search_opportunities",
    "keyword": "cybersecurity",
    "maxResults": 100
}
```

Filter by NAICS code and set-aside type:

```json
{
    "apiKey": "YOUR_SAM_GOV_API_KEY",
    "mode": "search_opportunities",
    "keyword": "cloud migration",
    "naicsCode": "541512",
    "setAside": "SBA",
    "state": "VA",
    "maxResults": 200
}
```

### Mode 2: Search Awards

Search for contract award notices to see who won and for how much.

```json
{
    "apiKey": "YOUR_SAM_GOV_API_KEY",
    "mode": "search_awards",
    "keyword": "artificial intelligence",
    "maxResults": 100
}
```

### Mode 3: Entity Lookup

Look up federal agencies and organizations. Useful for finding organization codes to use as search filters.

```json
{
    "apiKey": "YOUR_SAM_GOV_API_KEY",
    "mode": "entity_lookup",
    "organizationName": "Department of Defense"
}
```

### Search Filters

All filters apply to Mode 1 and Mode 2. Leave blank for no filtering.

| Parameter | Description |
|-----------|-------------|
| `keyword` | Search keyword for opportunity titles and descriptions |
| `solicitationNumber` | Search by specific solicitation number |
| `procurementType` | Filter by type: Solicitation, Pre-solicitation, Combined Synopsis, Sources Sought, Award Notice, Special Notice, Sale of Surplus, Justification, Intent to Bundle |
| `naicsCode` | NAICS industry code (up to 6 digits, e.g. `541512` for Computer Systems Design) |
| `classificationCode` | Product Service Code / PSC (e.g. `7030` for ADP Software) |
| `setAside` | Small business set-aside type (SBA, 8(a), HUBZone, SDVOSB, WOSB, EDWOSB, etc.) |
| `state` | 2-letter state code for place of performance (e.g. `VA`, `CA`, `TX`) |
| `zip` | ZIP code for place of performance |
| `organizationCode` | Federal agency/organization code (use Entity Lookup mode to find codes) |
| `postedFrom` | Start date for posted range (MM/dd/yyyy). Defaults to 30 days ago |
| `postedTo` | End date for posted range (MM/dd/yyyy). Defaults to today |
| `responseDeadlineFrom` | Filter by response deadline start (MM/dd/yyyy) |
| `responseDeadlineTo` | Filter by response deadline end (MM/dd/yyyy) |

### Additional Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `maxResults` | `100` | Maximum results to return (max 10,000). Free users are limited to 25 per run. |

---

## Output

Results are saved to the default dataset. Download them in JSON, CSV, Excel, or XML format from the Output tab.

### Example: Opportunity output

```json
{
    "type": "Solicitation",
    "noticeId": "abc123def456",
    "title": "Cybersecurity Assessment Services",
    "solicitationNumber": "W911NF-26-R-0042",
    "department": "DEPT OF DEFENSE.DEPT OF THE ARMY.ACC-APG NATICK",
    "agency": "ACC-APG NATICK",
    "postedDate": "2026-02-01",
    "responseDeadline": "2026-03-15",
    "archiveDate": "2026-04-15",
    "active": "Yes",
    "naicsCode": "541512",
    "classificationCode": "D310",
    "setAside": "Total Small Business Set-Aside",
    "setAsideCode": "SBA",
    "placeOfPerformance": {
        "city": "Natick",
        "state": "MA",
        "zip": "01760",
        "country": "US"
    },
    "contactName": "Jane Smith",
    "contactEmail": "jane.smith@army.mil",
    "contactPhone": "508-555-0199",
    "officeAddress": {
        "city": "Natick",
        "state": "MA",
        "zip": "01760"
    },
    "descriptionUrl": "https://sam.gov/api/prod/opps/v3/opportunities/resources/...",
    "resourceLinks": [],
    "uiLink": "https://sam.gov/opp/abc123def456/view",
    "awardDate": "",
    "awardNumber": "",
    "awardAmount": "",
    "awardeeName": "",
    "awardeeUei": ""
}
```

### Example: Award output

```json
{
    "type": "Award Notice",
    "noticeId": "xyz789ghi012",
    "title": "Cloud Infrastructure Modernization",
    "solicitationNumber": "FA8750-26-C-0001",
    "department": "DEPT OF DEFENSE.DEPT OF THE AIR FORCE.AFMC",
    "agency": "AFMC",
    "postedDate": "2026-01-20",
    "responseDeadline": "",
    "archiveDate": "2026-04-20",
    "active": "Yes",
    "naicsCode": "541519",
    "classificationCode": "7030",
    "setAside": "",
    "setAsideCode": "",
    "placeOfPerformance": {
        "city": "Rome",
        "state": "NY",
        "zip": "13441",
        "country": "US"
    },
    "contactName": "John Doe",
    "contactEmail": "john.doe@us.af.mil",
    "contactPhone": "",
    "officeAddress": {
        "city": "Rome",
        "state": "NY",
        "zip": "13441"
    },
    "descriptionUrl": "",
    "resourceLinks": [],
    "uiLink": "https://sam.gov/opp/xyz789ghi012/view",
    "awardDate": "2026-01-15",
    "awardNumber": "FA8750-26-C-0001",
    "awardAmount": "4500000",
    "awardeeName": "Acme Federal Solutions LLC",
    "awardeeUei": "ABC1DEF2GHI3"
}
```

### Example: Organization output

```json
{
    "type": "organization",
    "orgKey": "100000000",
    "name": "DEPARTMENT OF DEFENSE",
    "code": "097",
    "level": "1",
    "parentOrgKey": "",
    "parentName": "",
    "parentCode": "",
    "description": "",
    "startDate": "",
    "endDate": "",
    "cgac": "097",
    "fpdsOrgId": "9700",
    "fhOrgId": "300000000"
}
```

---

## Cost

This actor uses **pay-per-event (PPE) pricing**. You pay only for the results you get.

- **$0.50 per 1,000 results** ($0.0005 per result)
- **No proxy costs** -- SAM.gov is a government API, no proxies needed
- Free tier: **25 results per run** (no subscription required)

SAM.gov API requests are fast. A typical run fetching 100 opportunities completes in under a minute.

---

## Technical details

- Uses the SAM.gov public Opportunities API (`api.sam.gov/opportunities/v2/search`)
- Federal Hierarchy API for entity lookup (`api.sam.gov/prod/federalorganizations/v1/orgs`)
- API key passed as query parameter (standard SAM.gov authentication)
- Rate limited to 1 request/second (respects government API guidelines)
- Automatic retry with exponential backoff on failures
- Offset-based pagination (up to 1,000 results per page, 10,000 max depth)
- Results pushed in batches of 25 for efficiency
- Actor state persisted across migrations
- No proxies, no browser, no cookies -- direct API access

---

## Limitations

- SAM.gov requires the `postedFrom` and `postedTo` date range to be within 1 year. The scraper defaults to the last 30 days if no dates are provided.
- Maximum pagination depth is 10,000 results per run.
- The SAM.gov API occasionally returns empty pages; the scraper tolerates up to 2 consecutive empty pages before stopping.
- Entity Lookup mode returns a maximum of 100 organizations per query.
- You need your own SAM.gov API key (free, but requires registration).

---

## FAQ

### How do I get a SAM.gov API key?

Go to [sam.gov](https://sam.gov), create a free account, then navigate to Account Details and request a Public API Key. It is issued instantly.

### Is this data public?

Yes. All data returned by this scraper comes from the SAM.gov public API, which is the U.S. government's official system for posting federal contracting opportunities. This data is publicly available by law.

### What is a NAICS code?

NAICS (North American Industry Classification System) codes categorize businesses by industry. Common examples: 541512 (Computer Systems Design), 541511 (Custom Computer Programming), 541519 (Other Computer Related Services). You can search by code to find contracts in your industry.

### What are set-aside types?

The federal government reserves certain contracts for small businesses. Set-aside types include Small Business (SBA), 8(a) for disadvantaged businesses, HUBZone for businesses in historically underutilized areas, SDVOSB for service-disabled veteran-owned businesses, WOSB for women-owned businesses, and more.

### Why are some fields empty in award notices?

Award notices may not include all fields that solicitations have (like response deadlines), and solicitations will not have award-specific fields (like award amount or awardee name). This is normal -- the fields are only populated when relevant.

### Can I use this with the Apify API?

Yes. Call the actor via the Apify API and retrieve results programmatically in JSON, CSV, or other formats. Works with the Apify Python and JavaScript clients.

---

## MCP Integration

This actor works as an MCP tool through Apify's hosted MCP server. No custom server needed.

- **Endpoint:** `https://mcp.apify.com?tools=labrat011/gov-contracts-scraper`
- **Auth:** `Authorization: Bearer <APIFY_TOKEN>`
- **Transport:** Streamable HTTP
- **Works with:** Claude Desktop, Cursor, VS Code, Windsurf, Warp, Gemini CLI

**Example MCP config (Claude Desktop / Cursor):**

```json
{
    "mcpServers": {
        "gov-contracts-scraper": {
            "url": "https://mcp.apify.com?tools=labrat011/gov-contracts-scraper",
            "headers": {
                "Authorization": "Bearer <APIFY_TOKEN>"
            }
        }
    }
}
```

AI agents can use this actor to search federal contract opportunities, track award notices, look up agencies, and monitor procurement activity -- all as a callable MCP tool.

---

## Feedback

Found a bug or have a feature request? Open an issue on the actor's Issues tab in Apify Console.
