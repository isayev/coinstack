<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# include ebay, biddr and all links I have in xls file. Update your recommndaiton

Perfect! I have your CSV. Now I'll map all auction houses with your exact links and provide a unified scraping architecture:

## Multi-Source Auction Scraper Architecture

**Your CSV contains:**

- **Heritage** (~20 coins): ha.com
- **CNG** (~5 coins): auctions.cngcoins.com
- **Biddr** (~30 coins): biddr.com (Savoca, Nummitra, RexNumis, Agora, Coin Cabinet)
- **eBay** (~25 coins): ebay.com/itm
- **Agora** (~2 coins): agoraauctions.com

**Total: ~82 auction sources across 5 platforms.**

***

## Optimal Multi-Source Strategy

### 1. **Scraper Service Architecture**

```python
# scraper/base.py
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright
from pydantic import BaseModel

class LotData(BaseModel):
    lot_id: str
    house: str  # "Heritage", "CNG", "Biddr", "eBay", "Agora"
    hammer_price: float | None
    estimate_low: float | None
    estimate_high: float | None
    auction_date: str | None
    grade: str | None
    photos: list[str]  # CDN URLs
    description: str
    sold: bool
    url: str

class AuctionScraperBase(ABC):
    def __init__(self, proxy_url: str | None = None):
        self.proxy_url = proxy_url
        
    @abstractmethod
    async def extract_lot(self, url: str) -> LotData:
        """Parse auction page → structured data"""
        pass

# scraper/heritage.py
class HeritageScraper(AuctionScraperBase):
    selectors = {
        "hammer": ".bid-realized, [data-testid='hammer-price']",
        "estimate": "[data-testid='estimate-low']",
        "grade": ".certificate-grade, .grade-label",
        "photos": ".lot-image img",
        "title": ".lot-title",
        "date": "[data-testid='auction-date']"
    }
    
    async def extract_lot(self, url: str) -> LotData:
        page = await self.browser.new_page()
        await page.goto(url, wait_until="networkidle")
        
        # Let JS render (Heritage is SPA)
        await page.wait_for_selector(self.selectors["hammer"], timeout=5000)
        
        hammer = await page.evaluate(f"""
            () => {{
                const text = document.querySelector('{self.selectors["hammer"]}')?.textContent || '';
                return parseFloat(text.replace(/[$,]/g, ''));
            }}
        """)
        
        photos = []
        for img in await page.locator(self.selectors["photos"]).all():
            src = await img.get_attribute("src")
            if src and "placeholder" not in src:
                photos.append(src)
        
        return LotData(
            house="Heritage",
            hammer_price=hammer,
            photos=photos,
            # ... more fields
        )

# scraper/cng.py
class CNGScraper(AuctionScraperBase):
    selectors = {
        "hammer": ".price-realized, .hammer-price",
        "photos": ".lightbox-thumb img",
        "grade": ".grading-info",
    }
    
    async def extract_lot(self, url: str) -> LotData:
        page = await self.browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        # CNG pages load faster (mostly server-rendered)
        # ... similar extraction

# scraper/ebay.py
class EBayScraper(AuctionScraperBase):
    """eBay is JS-heavy; use iframe extraction"""
    
    async def extract_lot(self, url: str) -> LotData:
        page = await self.browser.new_page()
        await page.goto(url, wait_until="networkidle")
        
        # Sold price (after auction closes)
        sold_price = await page.evaluate("""
            () => {
                const text = document.querySelector('[data-testid="vi-VR-cvipPrice"]')?.textContent || '';
                return parseFloat(text.replace(/[$,]/g, ''));
            }
        """)
        
        photos = []
        for img in await page.locator(".vi_hl_pic_panel img").all():
            photos.append(await img.get_attribute("src"))
        
        return LotData(house="eBay", hammer_price=sold_price, photos=photos)

# scraper/biddr.py
class BiddrScraper(AuctionScraperBase):
    """Biddr hosts multiple sub-auctions (Savoca, Nummitra, RexNumis)"""
    
    async def extract_lot(self, url: str) -> LotData:
        page = await self.browser.new_page()
        await page.goto(url)
        
        # Biddr's generic structure
        hammer = await page.query_selector_eval(".lot-hammer", "el => el.textContent")
        
        # Determine sub-house from URL
        if "savoca" in url:
            house = "Biddr/Savoca"
        elif "nummitra" in url:
            house = "Biddr/Nummitra"
        else:
            house = "Biddr"
        
        return LotData(house=house, hammer_price=float(hammer.replace("$", "")))
```


### 2. **Unified Orchestrator**

```python
# orchestrator.py
class AuctionOrchestrator:
    def __init__(self):
        self.scrapers = {
            "ha.com": HeritageScraper,
            "cngcoins.com": CNGScraper,
            "ebay.com": EBayScraper,
            "biddr.com": BiddrScraper,
            "agoraauctions.com": BiddrScraper  # Similar structure
        }
        self.db = PostgresDB()
    
    async def fetch_owned_coins(self, csv_rows: list[dict]):
        """Backfill your CSV links"""
        for row in csv_rows:
            url = row["Link"]
            house = self._detect_house(url)
            scraper = self.scrapers[house]()
            
            try:
                lot_data = await scraper.extract_lot(url)
                await self.db.upsert_auction_data(
                    coin_id=row["id"],
                    auction_data=lot_data
                )
            except Exception as e:
                self.logger.warning(f"Failed {url}: {e}")
    
    async def monitor_refs(self, ref_list: list[str]):
        """Price monitoring: NumisBids aggregator"""
        for ref in ref_list:
            comps = await self._fetch_numisbids_comps(ref)  # Generic scrape
            prices = [c["hammer"] for c in comps]
            
            await self.db.insert_price_history(
                ref=ref,
                median=statistics.median(prices),
                count=len(prices),
                date=date.today()
            )
    
    def _detect_house(self, url: str) -> str:
        for domain, _ in self.scrapers.items():
            if domain in url:
                return domain
        raise ValueError(f"Unknown auction house: {url}")
```


### 3. **Database Schema**

```python
# models.py
class AuctionData(Base):
    __tablename__ = "auction_data"
    
    id = Column(Integer, primary_key=True)
    coin_id = Column(Integer, ForeignKey("coins.id"))
    house = Column(String(50))       # "Heritage", "CNG", "Biddr/Savoca", "eBay"
    lot_id = Column(String(100))
    url = Column(String(500), unique=True)
    hammer_price = Column(Float)     # Realized price
    estimate_low = Column(Float)
    estimate_high = Column(Float)
    auction_date = Column(Date)
    grade = Column(String(20))       # "AU", "VF", "XF"
    photos = Column(JSON)            # [{"url": "...", "side": "obv"}, ...]
    description = Column(Text)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    next_check = Column(DateTime)    # For re-scraping (prices may update)

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True)
    coin_id = Column(Integer, ForeignKey("coins.id"))
    ref = Column(String(50))         # "RIC I 207", "Crawford 335/1c"
    median_hammer = Column(Float)    # Across all recent comps
    low_hammer = Column(Float)
    high_hammer = Column(Float)
    count = Column(Integer)          # # of comps in this period
    date = Column(Date)
    
    __table_args__ = (Index("idx_ref_date", "ref", "date"),)
```


### 4. **Cron Jobs**

```python
# tasks.py
@scheduler.scheduled_job('cron', id='backfill_owned', hour=2)
async def backfill_csv_links():
    """One-time: backfill all ~82 links from CSV"""
    csv_data = load_csv("collection-v1.csv")
    await AuctionOrchestrator().fetch_owned_coins(csv_data)
    logger.info(f"✓ Backfilled {len(csv_data)} coins")

@scheduler.scheduled_job('cron', id='monitor_prices', hour=3)
async def monitor_market_prices():
    """Daily: Top 20 refs → NumisBids comps"""
    top_refs = db.query("SELECT ref FROM coins GROUP BY ref ORDER BY amount_paid DESC LIMIT 20")
    await AuctionOrchestrator().monitor_refs([r["ref"] for r in top_refs])

@scheduler.scheduled_job('cron', id='refresh_owned', day_of_week='mon')
async def refresh_owned_lots():
    """Weekly: Re-check owned coins for price updates (if still active)"""
    owned = db.query("SELECT url FROM auction_data WHERE fetched_at < NOW() - INTERVAL 7 DAY")
    # Re-scrape to capture any post-sale updates
```


### 5. **Frontend: Alerts \& Dashboard**

```python
# alerts.py
def generate_alerts(coin_id: int) -> list[str]:
    coin = db.get_coin(coin_id)
    alerts = []
    
    # Check if price dropped
    current_value = coin.amount_paid
    median_comp = db.get_latest_median(coin.ref)
    
    if median_comp and median_comp < current_value * 0.8:
        alerts.append(f"🔴 {coin.ref}: Comps down 20% (${current_value} → ${median_comp:.0f})")
    
    # Check if new high comps
    max_comp = db.get_max_hammer(coin.ref, days=30)
    if max_comp and max_comp > current_value * 1.5:
        alerts.append(f"🟢 {coin.ref}: New high comp! ${max_comp:.0f}")
    
    return alerts

# api/dashboard.py
@app.get("/api/price-trends/{ref}")
async def price_trends(ref: str):
    history = db.query("""
        SELECT date, median_hammer, low_hammer, high_hammer, count
        FROM price_history
        WHERE ref = ?
        ORDER BY date DESC
        LIMIT 90
    """, (ref,))
    
    return {
        "ref": ref,
        "trend": history,
        "current": history[^0] if history else None,
        "alerts": generate_alerts(ref)
    }
```


***

## 6. Implementation Priority

| Phase | Work | Time |
| :-- | :-- | :-- |
| **1** | Build base scrapers (Heritage, CNG, eBay) | 2d |
| **2** | Backfill your 82 links → AuctionData | 1d (runtime) |
| **3** | Cron monitoring (NumisBids daily) | 1d |
| **4** | Alerts + dashboard UI | 2d |
| **5** | Price history analytics (Plotly/Altair charts) | 1d |


***

## 7. Key Decisions

**Why Playwright over Selenium**: JS-rendering, eBay/Heritage SPAs, parallel execution.

**Why NumisBids for monitoring**: Aggregates all houses (no scattered API calls).

**Why separate house-specific scrapers**: CSS selectors differ per site; easy to maintain.

**Photo CDN caching**: Download once → GCS/S3 for permanent record.

**Re-check frequency**: Weekly for owned (may sell); Daily for ref monitoring.

**Rate limits**: 1–2/min per house; use residential proxies for eBay (bot detection).

***

**Ready to start?** I can scaffold:

1. `AuctionScraper` base class + Heritage implementation
2. Full database migrations
3. Scheduler setup with APScheduler

Which would be most useful first? 🎯
<span style="display:none">[^1][^10][^11][^12][^13][^14][^15][^16][^2][^3][^4][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: collection-v1.csv

[^2]: https://www.reddit.com/r/coins/comments/17wt0yc/public_apis_with_access_to_accurate_coin_prices/

[^3]: https://github.com/wendyyng/Biddr

[^4]: https://www.biddr.com

[^5]: https://new.biddr.com/about/forsellers

[^6]: https://www.bidlogix.com/bidding-api

[^7]: https://github.com/Super-Fast-Buyers/auctions-scraper

[^8]: https://dev.to/tinybirdco/build-a-real-time-auction-bidding-api-with-tinybird-1gp6

[^9]: https://www.webscrapingexpert.com/auction-data-scraping/

[^10]: https://learn.microsoft.com/en-us/xandr/bidders/bidder-api-services

[^11]: https://apify.com/lexis-solutions/hibid-com-scraper

[^12]: https://www.biddr.com/about/about

[^13]: https://www.auctionmarketer.co.uk/blog/online-auction-aggregators-and-their-industry-impact

[^14]: https://www.biddr.com/about/terms

[^15]: https://datamam.com/online-auctions-scraping/

[^16]: https://new.biddr.com/about/about

