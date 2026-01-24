# Heritage Auctions (HA.com) Scraper

Production-ready scraper for Heritage Auctions ancient coin data with full NGC/PCGS grade support.

## Site Analysis

Heritage is the largest numismatic auction house in the world. Their site uses **server-rendered HTML** (not SPA), making parsing straightforward but requiring careful rate limiting.

### Key Differences from CNG

| Feature | Heritage | CNG |
|---------|----------|-----|
| Rendering | Server HTML | Auction Mobility (JSON-LD) |
| Grading | Mostly NGC/PCGS slabs | Mostly raw coins |
| Prices | Login required | Visible |
| Rate Limiting | Aggressive | Moderate |
| Images | heritagestatic CDN + NGC PhotoVision | auctionmobility CDN |
| Historical Content | Extensive narratives | Minimal |

## URL Patterns

```
Lot Page (SEO-friendly):
https://coins.ha.com/itm/{category}/{subcategory}/{slug}/a/{auction_id}-{lot_number}.s

Lot Page (direct):
https://coins.ha.com/c/item.zx?saleNo={auction_id}&lotIdNo={lot_number}

Search:
https://coins.ha.com/c/search.zx?N=790+231&Ntt={query}&type=archive

Auction Home:
https://coins.ha.com/c/auction-home.zx?saleNo={auction_id}

Images (CDN):
https://dyn1.heritagestatic.com/ha?p={params}&it=product

NGC PhotoVision (slabbed coins):
Embedded from ngccoin.com, high-quality standardized images
```

### URL Examples

```
# Raw coin (not slabbed)
https://coins.ha.com/itm/ancients/roman-imperial/roman-imperial-domitian-as-augustus-ad-81-96-ae-as-28mm-1094-gm-5h-choice-vf-altered-surface/a/61519-25289.s

# NGC slabbed coin
https://coins.ha.com/itm/ancients/roman-imperial/roman-imperial-gallienus-sole-reign-ad-253-268-bi-antoninianus-22mm-362-gm-7h-ngc-ms-4-5-4-5/a/61519-25316.s

# Gold coin
https://coins.ha.com/itm/ancients/roman-provincial/roman-provincial-scythia-geto-dacians-coson-ca-after-54-bc-av-stater-18mm-853-gm-12h-ngc-choice-au-5-5-4-5/a/3125-35124.s
```

## Data Extracted

### Title Parsing

Heritage titles follow this format:
```
{Category}: {Ruler}, {Title} ({Reign}). {Metal} {Denomination} ({Physical}). {Grade}.
```

Examples:
```
Roman Imperial: Domitian, as Augustus (AD 81-96). AE as (28mm, 10.94 gm, 5h). Choice VF, altered surface.

Roman Imperial: Gallienus, Sole Reign (AD 253-268). BI antoninianus (22mm, 3.62 gm, 7h). NGC MS 4/5 - 4/5.
```

### Field Extraction

| Field | Source | Example |
|-------|--------|---------|
| **category** | URL path | "Roman Imperial" |
| **ruler** | Title | "Domitian" |
| **ruler_title** | Title | "as Augustus" |
| **reign_dates** | Title | "AD 81-96" |
| **denomination** | Title | "as", "antoninianus" |
| **metal** | Title | AE, BI, AR, AV |
| **diameter_mm** | Title | 28 |
| **weight_gm** | Title | 10.94 (Heritage uses "gm") |
| **die_axis** | Title | 5h (150°) |
| **mint** | Description | "Rome" |
| **mint_date** | Description | "AD 92-94" |
| **obverse_legend** | Description | "IMP CAES DOMIT AVG GERM-COS XVI CENS PER P P" |
| **obverse_desc** | Description | "laureate head of Domitian right" |
| **reverse_legend** | Description | "MONETA-AVGVSTI" |
| **reverse_desc** | Description | "Moneta standing facing, head left..." |
| **references** | Description | ["RIC II.1 756"] |
| **grade** | Title | "Choice VF" or "NGC MS 4/5 - 4/5" |
| **surface_issues** | Title | "altered surface", "tooled" |
| **condition_notes** | Description | "Deep kaitoke green patina" |
| **provenance** | Description | "From the Merrill A. Gibson Collection" |
| **historical_notes** | Description | Extended narrative about ruler |

### NGC/PCGS Grade Parsing

Heritage predominantly sells NGC-slabbed ancient coins. The grade format:

```
NGC {Designation?} {Grade} {Numeric?} {Strike}/{Surface}, {Extras}

Examples:
- NGC MS 4/5 - 4/5
- NGC Choice AU 5/5 - 4/5, Fine Style
- NGC Choice Fine, Scratches
```

The scraper extracts:
```python
SlabGrade(
    service=GradingService.NGC,
    grade="MS",                    # Base grade
    strike_score="4/5",            # Strike quality (NGC ancients)
    surface_score="4/5",           # Surface quality (NGC ancients)
    numeric_grade=None,            # 1-70 scale (rare for ancients)
    designation="Choice",          # Prefix designations
    certification_number="8521584005",
    verification_url="https://www.ngccoin.com/certlookup/8521584005/NGCAncients"
)
```

### Raw Grade Parsing

For unslabbed coins:
```python
RawGrade(
    grade="Choice VF",
    qualifier="altered surface"    # Surface issues
)
```

## Installation

```bash
pip install httpx beautifulsoup4 pydantic aiofiles tenacity
```

## Quick Start

```python
import asyncio
from heritage_scraper import scrape_heritage_lot, HeritageScraper

async def example():
    # Single lot
    coin = await scrape_heritage_lot(
        "https://coins.ha.com/itm/.../a/61519-25316.s"
    )
    
    print(f"Ruler: {coin.ruler}")
    print(f"Grade: {coin.grade_display}")
    
    if coin.is_slabbed:
        print(f"NGC Cert: {coin.certification_number}")
        print(f"Verify: {coin.slab_grade.verification_url}")
    
    print(f"Obverse: {coin.obverse_legend}")
    print(f"  {coin.obverse_description}")
    
    print(f"Provenance: {coin.provenance.collection_name}")

asyncio.run(example())
```

## Search & Batch Scraping

```python
async def batch_example():
    async with HeritageScraper() as scraper:
        # Search archives
        results = await scraper.search("hadrian denarius NGC")
        print(f"Found {results.total_results} lots")
        
        # Scrape all results
        async for coin in scraper.scrape_search_results(
            "augustus denarius",
            max_results=20,
            download_images=True
        ):
            print(f"{coin.heritage_lot_id}: {coin.ruler} {coin.denomination}")
            if coin.is_slabbed:
                print(f"  {coin.slab_grade.full_grade}")
```

## Integration with CoinStack

```python
from heritage_scraper import HeritageIntegration

async def import_to_coinstack(db_session, url, coin_id=None):
    async with HeritageIntegration(db_session) as integration:
        result = await integration.import_from_url(
            url=url,
            coin_id=coin_id,
            create_if_missing=True,
            verify_certification=True,  # Verify NGC cert
        )
        
        print(f"Slabbed: {result['is_slabbed']}")
        print(f"Cert Verified: {result['certification_verified']}")
        print(f"Enrichments: {len(result['enrichments'])}")
```

## Files

```
heritage_scraper/
├── __init__.py         # Package exports
├── models.py           # Pydantic schemas (HeritageCoinData, SlabGrade, etc.)
├── parser.py           # HTML parsing
├── scraper.py          # Main scraper service
├── integration.py      # CoinStack audit integration
└── README.md           # This file
```

## Rate Limiting

**Heritage is aggressive about rate limiting.** The scraper uses:

- 3 second minimum delay between requests
- 20 requests per minute maximum
- Exponential backoff on 429 errors
- HTML caching to avoid re-fetching

```python
# Rate limit settings
REQUESTS_PER_MINUTE = 20
MIN_DELAY_SECONDS = 3.0
```

If you get blocked (403), wait 24 hours or use a different IP.

## Price Data

**Sold prices require Heritage account login.** The page shows "Sign-in" instead of actual prices.

To get prices, either:
1. Pass session cookie to scraper
2. Use Heritage's paid API
3. Scrape while logged in (browser automation)

```python
# With session cookie
scraper = HeritageScraper(session_cookie="your_session_id")
```

## Image Sources

Heritage uses two image sources:

### 1. Heritage Static CDN
```
https://dyn1.heritagestatic.com/ha?p=3-2-5-4-0-32540432&it=product
```

Standard lot photos, both obverse and reverse shown.

### 2. NGC PhotoVision
```
NGC PhotoVision - NGCcoin.com (via Heritage Auctions, HA.com)
```

For NGC-slabbed coins, high-quality standardized images from NGC's PhotoVision service are embedded. These show:
- Coin images (obverse/reverse)
- Slab holder photos (front/back)

## Description Structure

Heritage descriptions follow this pattern:

```
{Ruler}, {Title} ({Reign}). {Metal} {Denomination} ({Physical}). {Grade}.

{Mint}, {Date}. {Obverse Legend}, {obverse description} / {Reverse Legend}, {reverse description}. {Reference}. {Condition notes}.

From the {Collection Name}. Ex {Previous Owner/Auction}.

{Extended historical narrative about the ruler...}
```

### Example:
```
Domitian, as Augustus (AD 81-96). AE as (28mm, 10.94 gm, 5h). Choice VF, altered surface.

Rome, AD 92-94. IMP CAES DOMIT AVG GERM-COS XVI CENS PER P P, laureate head of
Domitian right / MONETA-AVGVSTI, Moneta standing facing, head left, scales in
outstretched right hand, cornucopia cradled in left arm; S-C across fields (S
within scales). RIC II.1 756. Deep kaitoke green patina. Altered surface, thus
ineligible for encapsulation.

From the Merrill A. Gibson Collection of Ancient Coins. Ex Apollo Numismatics,
private sale with old dealer's tag included.

Domitian, often remembered as a controversial figure in Roman history, lived a
complex life marked by both admirable achievements and a dark reputation...
```

## Trust Level for Audit

Heritage is a **HIGH TRUST** source:

| Field | Trust Level | Notes |
|-------|-------------|-------|
| Physical (weight, diameter) | HIGH | Professional measurement |
| Grade (NGC/PCGS) | AUTHORITATIVE | Third-party certified |
| Grade (raw) | HIGH | Professional assessment |
| References | HIGH | Expert cataloging |
| Legends | HIGH | Professional transcription |
| Provenance | HIGH | Verified collections |
| Images | AUTHORITATIVE | Professional photography |
| Prices | AUTHORITATIVE | Actual sale records |

### Special Handling

- **NGC/PCGS grades are authoritative** - Always trust over user-entered grades
- **Certification numbers can be verified** - Link to NGC/PCGS lookup
- **Named collections are valuable** - "Merrill A. Gibson Collection" etc.
- **Surface issues are disclosed** - "altered surface", "tooled"

## Comparison: Heritage vs CNG

| Aspect | Heritage | CNG |
|--------|----------|-----|
| **Primary Market** | US collectors | International |
| **Coin Types** | 70% NGC/PCGS slabs | 90% raw coins |
| **Grade Format** | NGC MS 4/5-4/5 | VF, EF (traditional) |
| **Weight Unit** | "gm" | "g" |
| **Provenance** | Named collections | Auction chains |
| **Historical Content** | Extensive | Minimal |
| **Images** | CDN + NGC PhotoVision | Single CDN |
| **Rate Limits** | Strict | Moderate |

## Error Handling

```python
from heritage_scraper import HeritageScraper
import logging

logging.basicConfig(level=logging.INFO)

async with HeritageScraper() as scraper:
    try:
        coin = await scraper.scrape_url(url)
    except Exception as e:
        if "Rate limited" in str(e):
            print("Wait 60 seconds and retry")
        elif "Blocked" in str(e):
            print("IP blocked - wait 24 hours")
        else:
            print(f"Error: {e}")
```

## NGC Verification

For NGC-slabbed coins, verify the certification:

```python
async with HeritageScraper() as scraper:
    coin = await scraper.scrape_url(url)
    
    if coin.certification_number:
        verification = await scraper.verify_ngc_cert(coin.certification_number)
        if verification and verification['verified']:
            print(f"✓ NGC cert {coin.certification_number} verified")
```

## Common Issues

### 1. Missing Prices
Prices require login. Without authentication, `sold_price_usd` will be `None`.

### 2. Rate Limiting (429)
Heritage blocks aggressive scraping. Solution: increase delays, use caching.

### 3. IP Blocking (403)
If blocked, wait 24 hours or use a different IP address.

### 4. Grade Parsing Edge Cases
Some grades have unusual formats:
- "Near Mint State" → Need to map to MS
- "Extremely Fine" → Map to EF/XF
- "About Uncirculated" → Map to AU

The parser handles common variations but may need extension for rare cases.

### 5. Missing NGC Links
Not all NGC coins have verification links. Check `slab_grade.verification_url`.
