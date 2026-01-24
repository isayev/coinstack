# Task Recipes

Step-by-step guides for common development tasks.

---

## Recipe 1: Add a New Field to Coin Model

**Goal:** Add `diameter_max_mm` field to support irregular flan coins.

### Step 1: Update SQLAlchemy Model

Edit `backend/app/models/coin.py`:

```python
class Coin(Base):
    # ... existing fields ...
    
    # Physical measurements
    weight_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    diameter_mm: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    diameter_max_mm: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))  # NEW
    die_axis: Mapped[int | None]
```

### Step 2: Update Pydantic Schemas

Edit `backend/app/schemas/coin.py`:

```python
# In CoinBase or appropriate base class
class CoinBase(BaseModel):
    # ... existing fields ...
    diameter_mm: Decimal | None = None
    diameter_max_mm: Decimal | None = None  # NEW

# Ensure it's in CoinCreate
class CoinCreate(CoinBase):
    # ... 
    diameter_max_mm: Decimal | None = None  # NEW

# Ensure it's in CoinUpdate  
class CoinUpdate(BaseModel):
    # ... 
    diameter_max_mm: Decimal | None = None  # NEW

# Ensure it's in CoinDetail (if not inherited)
class CoinDetail(CoinBase):
    # ...
    diameter_max_mm: Decimal | None = None  # NEW
```

### Step 3: Create Database Migration

If using Alembic (recommended for production):

```bash
cd backend
alembic revision --autogenerate -m "Add diameter_max_mm to coins"
alembic upgrade head
```

Or manually update SQLite (development):

```python
# Run once in Python console
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE coins ADD COLUMN diameter_max_mm DECIMAL(5,2)"))
    conn.commit()
```

### Step 4: Update TypeScript Types

Edit `frontend/src/types/coin.ts`:

```typescript
interface CoinDetail extends CoinListItem {
  // ... existing fields ...
  diameter_mm: number | null
  diameter_max_mm: number | null  // NEW
  die_axis: number | null
}
```

### Step 5: Update Form Component

Edit `frontend/src/components/coins/CoinForm.tsx`:

```typescript
// In Physical tab section
<div className="grid grid-cols-3 gap-4">
  <div>
    <Label>Weight (g)</Label>
    <Input type="number" step="0.001" {...form.register('weight_g')} />
  </div>
  <div>
    <Label>Diameter (mm)</Label>
    <Input type="number" step="0.1" {...form.register('diameter_mm')} />
  </div>
  <div>
    <Label>Max Diameter (mm)</Label>  {/* NEW */}
    <Input type="number" step="0.1" {...form.register('diameter_max_mm')} />
  </div>
</div>
```

### Step 6: Update Detail Display

Edit `frontend/src/pages/CoinDetailPage.tsx`:

```typescript
// In Physical section
<div className="grid grid-cols-4 gap-4">
  <Stat label="Weight" value={coin.weight_g ? `${coin.weight_g}g` : '-'} />
  <Stat label="Diameter" value={coin.diameter_mm ? `${coin.diameter_mm}mm` : '-'} />
  <Stat label="Max Diameter" value={coin.diameter_max_mm ? `${coin.diameter_max_mm}mm` : '-'} />  {/* NEW */}
  <Stat label="Die Axis" value={coin.die_axis ? `${coin.die_axis}h` : '-'} />
</div>
```

### Step 7: Test

1. Restart backend: `uv run uvicorn app.main:app --reload`
2. Check Swagger UI: `http://localhost:8000/docs`
3. Verify field appears in POST/PUT schemas
4. Create/edit a coin with the new field
5. Verify it displays in detail view

---

## Recipe 2: Add a New API Endpoint

**Goal:** Add endpoint to get price history for a coin.

### Step 1: Define Schema

Create or edit `backend/app/schemas/price.py`:

```python
from pydantic import BaseModel
from datetime import date
from decimal import Decimal

class PriceHistoryItem(BaseModel):
    auction_date: date
    hammer_price: Decimal
    auction_house: str
    grade: str | None = None

class PriceHistoryResponse(BaseModel):
    coin_id: int
    reference: str | None
    history: list[PriceHistoryItem]
    avg_price: Decimal | None
    price_trend: str  # "rising", "stable", "falling"
```

### Step 2: Add CRUD Function

Edit `backend/app/crud/auction.py`:

```python
from sqlalchemy import select, func
from app.models.auction_data import AuctionData
from app.models.coin import Coin

def get_price_history(db: Session, coin_id: int) -> list[AuctionData]:
    """Get price history for a coin based on similar auctions."""
    # Get coin to find reference
    coin = db.execute(select(Coin).where(Coin.id == coin_id)).scalar_one_or_none()
    if not coin:
        return []
    
    # Find comparable auctions
    stmt = (
        select(AuctionData)
        .where(AuctionData.ruler.ilike(f"%{coin.issuing_authority}%"))
        .where(AuctionData.denomination == coin.denomination)
        .where(AuctionData.hammer_price.isnot(None))
        .order_by(AuctionData.auction_date.desc())
        .limit(50)
    )
    
    return list(db.execute(stmt).scalars().all())
```

### Step 3: Add Service Logic

Create `backend/app/services/price_analyzer.py`:

```python
from decimal import Decimal
from statistics import mean
from app.models.auction_data import AuctionData

class PriceAnalyzer:
    def analyze(self, auctions: list[AuctionData]) -> dict:
        if not auctions:
            return {"avg_price": None, "price_trend": "unknown"}
        
        prices = [a.hammer_price for a in auctions if a.hammer_price]
        if not prices:
            return {"avg_price": None, "price_trend": "unknown"}
        
        avg_price = Decimal(str(mean(prices)))
        
        # Simple trend analysis
        if len(prices) >= 3:
            recent = mean(prices[:3])
            older = mean(prices[-3:])
            if recent > older * 1.1:
                trend = "rising"
            elif recent < older * 0.9:
                trend = "falling"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        return {"avg_price": avg_price, "price_trend": trend}
```

### Step 4: Add Router Endpoint

Edit `backend/app/routers/coins.py`:

```python
from app.schemas.price import PriceHistoryResponse, PriceHistoryItem
from app.crud.auction import get_price_history
from app.services.price_analyzer import PriceAnalyzer

@router.get("/{coin_id}/price-history", response_model=PriceHistoryResponse)
def get_coin_price_history(coin_id: int, db: Session = Depends(get_db)):
    """Get price history and trend for a coin."""
    # Get coin
    coin = crud_coin.get_coin(db, coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    
    # Get auction history
    auctions = get_price_history(db, coin_id)
    
    # Analyze prices
    analyzer = PriceAnalyzer()
    analysis = analyzer.analyze(auctions)
    
    # Build response
    history = [
        PriceHistoryItem(
            auction_date=a.auction_date,
            hammer_price=a.hammer_price,
            auction_house=a.auction_house,
            grade=a.grade,
        )
        for a in auctions
        if a.hammer_price
    ]
    
    # Get primary reference
    reference = None
    if coin.references:
        ref = coin.references[0]
        reference = f"{ref.system} {ref.volume or ''} {ref.number}".strip()
    
    return PriceHistoryResponse(
        coin_id=coin_id,
        reference=reference,
        history=history,
        avg_price=analysis["avg_price"],
        price_trend=analysis["price_trend"],
    )
```

### Step 5: Add Frontend Hook

Edit `frontend/src/hooks/useCoins.ts`:

```typescript
interface PriceHistoryItem {
  auction_date: string
  hammer_price: number
  auction_house: string
  grade: string | null
}

interface PriceHistory {
  coin_id: number
  reference: string | null
  history: PriceHistoryItem[]
  avg_price: number | null
  price_trend: 'rising' | 'stable' | 'falling' | 'unknown'
}

export function usePriceHistory(coinId: number) {
  return useQuery({
    queryKey: ['coin', coinId, 'price-history'],
    queryFn: async (): Promise<PriceHistory> => {
      const response = await api.get(`/coins/${coinId}/price-history`)
      return response.data
    },
    enabled: !!coinId,
  })
}
```

### Step 6: Add UI Component

Create `frontend/src/components/coins/PriceHistory.tsx`:

```typescript
import { usePriceHistory } from '@/hooks/useCoins'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatCurrency } from '@/lib/utils'

interface PriceHistoryProps {
  coinId: number
}

export function PriceHistory({ coinId }: PriceHistoryProps) {
  const { data, isLoading } = usePriceHistory(coinId)
  
  if (isLoading) return <div>Loading price history...</div>
  if (!data) return null
  
  const trendIcon = {
    rising: '↑',
    falling: '↓',
    stable: '→',
    unknown: '?',
  }[data.price_trend]
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Price History</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex gap-4 mb-4">
          <div>
            <span className="text-sm text-muted-foreground">Average</span>
            <p className="text-lg font-medium">
              {data.avg_price ? formatCurrency(data.avg_price) : '-'}
            </p>
          </div>
          <div>
            <span className="text-sm text-muted-foreground">Trend</span>
            <p className="text-lg font-medium">
              {trendIcon} {data.price_trend}
            </p>
          </div>
        </div>
        
        <div className="space-y-2">
          {data.history.slice(0, 10).map((item, i) => (
            <div key={i} className="flex justify-between text-sm">
              <span>{item.auction_house}</span>
              <span>{formatCurrency(item.hammer_price)}</span>
              <span className="text-muted-foreground">{item.auction_date}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
```

### Step 7: Integrate into Detail Page

Edit `frontend/src/pages/CoinDetailPage.tsx`:

```typescript
import { PriceHistory } from '@/components/coins/PriceHistory'

// In the component JSX
<div className="grid grid-cols-3 gap-6">
  {/* ... other sections ... */}
  
  <div className="col-span-1">
    <PriceHistory coinId={coin.id} />
  </div>
</div>
```

---

## Recipe 3: Create a New Scraper

**Goal:** Add scraper for Roma Numismatics.

### Step 1: Create Scraper File

Create `backend/app/services/scrapers/roma.py`:

```python
import httpx
from bs4 import BeautifulSoup
from decimal import Decimal
import re

from app.services.scrapers.base import AuctionScraperBase, LotData

class RomaScraper(AuctionScraperBase):
    """Scraper for Roma Numismatics (romanumismatics.com)."""
    
    DOMAIN = "romanumismatics.com"
    
    def can_handle(self, url: str) -> bool:
        """Check if URL is from Roma Numismatics."""
        return self.DOMAIN in url.lower()
    
    async def scrape(self, url: str) -> LotData:
        """Scrape a Roma Numismatics lot page."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Parse lot number from URL or page
        lot_number = self._extract_lot_number(url, soup)
        
        # Parse title
        title_elem = soup.select_one('.lot-title, h1.title')
        title = title_elem.get_text(strip=True) if title_elem else None
        
        # Parse description
        desc_elem = soup.select_one('.lot-description, .description')
        description = desc_elem.get_text(strip=True) if desc_elem else None
        
        # Parse estimate
        estimate_low, estimate_high = self._parse_estimate(soup)
        
        # Parse hammer price (if sold)
        hammer_price = self._parse_hammer(soup)
        
        # Parse physical details
        weight_g, diameter_mm = self._parse_physical(description)
        
        # Parse images
        image_urls = self._parse_images(soup)
        
        # Extract ruler from title
        ruler = self._extract_ruler(title)
        
        return LotData(
            auction_house="Roma Numismatics",
            sale_name=self._extract_sale_name(soup),
            lot_number=lot_number,
            title=title,
            description=description,
            category=self._detect_category(description),
            metal=self._detect_metal(description),
            denomination=self._extract_denomination(title, description),
            ruler=ruler,
            weight_g=weight_g,
            diameter_mm=diameter_mm,
            estimate_low=estimate_low,
            estimate_high=estimate_high,
            hammer_price=hammer_price,
            reference_text=self._extract_references(description),
            image_urls=image_urls,
            url=url,
        )
    
    def _extract_lot_number(self, url: str, soup: BeautifulSoup) -> str:
        # Try URL first
        match = re.search(r'/lot[/-](\d+)', url, re.I)
        if match:
            return match.group(1)
        
        # Try page content
        lot_elem = soup.select_one('.lot-number')
        if lot_elem:
            return lot_elem.get_text(strip=True).replace('Lot', '').strip()
        
        return "unknown"
    
    def _parse_estimate(self, soup: BeautifulSoup) -> tuple[Decimal | None, Decimal | None]:
        est_elem = soup.select_one('.estimate')
        if not est_elem:
            return None, None
        
        text = est_elem.get_text()
        # Match patterns like "£200-300" or "Estimate: $500 - $700"
        match = re.search(r'[\$£€]?([\d,]+)\s*[-–]\s*[\$£€]?([\d,]+)', text)
        if match:
            low = Decimal(match.group(1).replace(',', ''))
            high = Decimal(match.group(2).replace(',', ''))
            return low, high
        return None, None
    
    def _parse_hammer(self, soup: BeautifulSoup) -> Decimal | None:
        hammer_elem = soup.select_one('.hammer-price, .sold-price')
        if not hammer_elem:
            return None
        
        text = hammer_elem.get_text()
        match = re.search(r'[\$£€]?([\d,]+)', text)
        if match:
            return Decimal(match.group(1).replace(',', ''))
        return None
    
    def _parse_physical(self, description: str | None) -> tuple[Decimal | None, Decimal | None]:
        if not description:
            return None, None
        
        weight = None
        diameter = None
        
        # Weight: "3.82g" or "3.82 g"
        w_match = re.search(r'(\d+\.?\d*)\s*g(?:r|ram)?', description, re.I)
        if w_match:
            weight = Decimal(w_match.group(1))
        
        # Diameter: "18mm" or "18 mm"
        d_match = re.search(r'(\d+\.?\d*)\s*mm', description, re.I)
        if d_match:
            diameter = Decimal(d_match.group(1))
        
        return weight, diameter
    
    def _parse_images(self, soup: BeautifulSoup) -> list[str]:
        images = []
        for img in soup.select('.lot-image img, .gallery img'):
            src = img.get('src') or img.get('data-src')
            if src:
                if not src.startswith('http'):
                    src = f"https://romanumismatics.com{src}"
                images.append(src)
        return images
    
    def _detect_category(self, description: str | None) -> str | None:
        if not description:
            return None
        desc_lower = description.lower()
        if 'republic' in desc_lower:
            return 'republic'
        if 'byzantine' in desc_lower:
            return 'byzantine'
        if 'provincial' in desc_lower or 'greek imperial' in desc_lower:
            return 'provincial'
        if 'greek' in desc_lower:
            return 'greek'
        return 'imperial'  # Default
    
    def _detect_metal(self, description: str | None) -> str | None:
        if not description:
            return None
        desc_lower = description.lower()
        if 'av ' in desc_lower or 'gold' in desc_lower or 'aureus' in desc_lower:
            return 'gold'
        if 'ar ' in desc_lower or 'silver' in desc_lower or 'denarius' in desc_lower:
            return 'silver'
        if 'ae ' in desc_lower or 'bronze' in desc_lower:
            return 'bronze'
        if 'billon' in desc_lower:
            return 'billon'
        return None
    
    def _extract_ruler(self, title: str | None) -> str | None:
        if not title:
            return None
        # Common pattern: "AUGUSTUS. 27 BC-AD 14. AR Denarius"
        match = re.match(r'^([A-Z][A-Z\s]+?)\.?\s*\d', title)
        if match:
            return match.group(1).strip().title()
        return None
    
    def _extract_denomination(self, title: str | None, desc: str | None) -> str | None:
        text = f"{title or ''} {desc or ''}".lower()
        denominations = [
            'aureus', 'denarius', 'quinarius', 'sestertius',
            'dupondius', 'as', 'semis', 'quadrans',
            'antoninianus', 'solidus', 'siliqua', 'follis'
        ]
        for denom in denominations:
            if denom in text:
                return denom.title()
        return None
    
    def _extract_references(self, description: str | None) -> str | None:
        if not description:
            return None
        # Look for RIC, Crawford, etc.
        patterns = [
            r'RIC\s+[IVX]+\s+\d+[a-z]?',
            r'Crawford\s+\d+/\d+[a-z]?',
            r'RPC\s+[IVX]+\s+\d+',
            r'Sear\s+\d+',
        ]
        refs = []
        for pattern in patterns:
            matches = re.findall(pattern, description, re.I)
            refs.extend(matches)
        return '; '.join(refs) if refs else None
    
    def _extract_sale_name(self, soup: BeautifulSoup) -> str | None:
        sale_elem = soup.select_one('.sale-name, .auction-title')
        if sale_elem:
            return sale_elem.get_text(strip=True)
        return None
```

### Step 2: Register Scraper

Edit `backend/app/services/scrapers/orchestrator.py`:

```python
from app.services.scrapers.roma import RomaScraper

class AuctionOrchestrator:
    def __init__(self):
        self.scrapers = [
            HeritageScraper(),
            CNGScraper(),
            BiddrScraper(),
            EbayScraper(),
            RomaScraper(),  # NEW
        ]
```

### Step 3: Test

```python
# In Python console
import asyncio
from app.services.scrapers.roma import RomaScraper

scraper = RomaScraper()
url = "https://romanumismatics.com/auction/lot/12345"

result = asyncio.run(scraper.scrape(url))
print(result)
```

---

## Recipe 4: Add a New Filter

**Goal:** Add "has images" filter to collection view.

### Step 1: Update Backend Query

Edit `backend/app/crud/coin.py`:

```python
def get_coins(
    db: Session,
    # ... existing params ...
    has_images: bool | None = None,  # NEW
) -> tuple[list[Coin], int]:
    stmt = select(Coin)
    
    # ... existing filters ...
    
    # NEW: Filter by has images
    if has_images is True:
        stmt = stmt.where(Coin.images.any())
    elif has_images is False:
        stmt = stmt.where(~Coin.images.any())
    
    # ... rest of function ...
```

### Step 2: Update Router

Edit `backend/app/routers/coins.py`:

```python
@router.get("", response_model=PaginatedCoins)
def list_coins(
    # ... existing params ...
    has_images: bool | None = Query(None, description="Filter by has images"),  # NEW
    db: Session = Depends(get_db),
):
    coins, total = crud_coin.get_coins(
        db,
        # ... existing params ...
        has_images=has_images,  # NEW
    )
    # ...
```

### Step 3: Update Filter Store

Edit `frontend/src/stores/filterStore.ts`:

```typescript
interface FilterState {
  // ... existing fields ...
  hasImages: boolean | null  // NEW
  
  // ... existing methods ...
}

const initialState = {
  // ... existing fields ...
  hasImages: null,  // NEW
}

export const useFilterStore = create<FilterState>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      toParams: () => {
        const state = get()
        const params: Record<string, unknown> = {
          // ... existing params ...
        }
        if (state.hasImages !== null) params.has_images = state.hasImages  // NEW
        return params
      },
      
      getActiveFilterCount: () => {
        const state = get()
        let count = 0
        // ... existing counts ...
        if (state.hasImages !== null) count++  // NEW
        return count
      },
    }),
    { name: 'coinstack-filters' }
  )
)
```

### Step 4: Update Filter UI

Edit `frontend/src/components/coins/CoinFilters.tsx`:

```typescript
import { useFilterStore } from '@/stores/filterStore'
import { Select } from '@/components/ui/select'

export function CoinFilters() {
  const { hasImages, setFilter } = useFilterStore()
  
  return (
    <div className="space-y-4">
      {/* ... existing filters ... */}
      
      {/* NEW: Has Images Filter */}
      <div>
        <Label>Images</Label>
        <Select
          value={hasImages === null ? '' : hasImages ? 'yes' : 'no'}
          onValueChange={(v) => 
            setFilter('hasImages', v === '' ? null : v === 'yes')
          }
        >
          <option value="">Any</option>
          <option value="yes">Has Images</option>
          <option value="no">No Images</option>
        </Select>
      </div>
    </div>
  )
}
```

---

## Recipe 5: Add a Design System Component

**Goal:** Create a `CategoryBadge` component.

### Step 1: Define Colors

Edit `frontend/src/index.css`:

```css
:root {
  /* Category colors */
  --category-republic: 220 14% 35%;    /* Muted steel */
  --category-imperial: 270 50% 40%;    /* Royal purple */
  --category-provincial: 160 40% 35%;  /* Antique teal */
  --category-byzantine: 35 80% 45%;    /* Byzantine gold */
  --category-greek: 210 60% 40%;       /* Aegean blue */
  --category-other: 0 0% 50%;          /* Neutral gray */
}
```

### Step 2: Create Component

Create `frontend/src/components/design-system/CategoryBadge.tsx`:

```typescript
import { Category } from '@/types/coin'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface CategoryBadgeProps {
  category: Category
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const categoryConfig: Record<Category, { label: string; className: string }> = {
  [Category.republic]: {
    label: 'Republic',
    className: 'bg-[hsl(var(--category-republic))] text-white',
  },
  [Category.imperial]: {
    label: 'Imperial',
    className: 'bg-[hsl(var(--category-imperial))] text-white',
  },
  [Category.provincial]: {
    label: 'Provincial',
    className: 'bg-[hsl(var(--category-provincial))] text-white',
  },
  [Category.byzantine]: {
    label: 'Byzantine',
    className: 'bg-[hsl(var(--category-byzantine))] text-white',
  },
  [Category.greek]: {
    label: 'Greek',
    className: 'bg-[hsl(var(--category-greek))] text-white',
  },
  [Category.other]: {
    label: 'Other',
    className: 'bg-[hsl(var(--category-other))] text-white',
  },
}

const sizeClasses = {
  sm: 'text-xs px-1.5 py-0.5',
  md: 'text-sm px-2 py-0.5',
  lg: 'text-base px-2.5 py-1',
}

export function CategoryBadge({ category, size = 'md', className }: CategoryBadgeProps) {
  const config = categoryConfig[category]
  
  return (
    <Badge
      className={cn(
        config.className,
        sizeClasses[size],
        'font-medium',
        className
      )}
    >
      {config.label}
    </Badge>
  )
}
```

### Step 3: Export from Index

Edit `frontend/src/components/design-system/index.ts`:

```typescript
export { MetalBadge } from './MetalBadge'
export { GradeBadge } from './GradeBadge'
export { RarityIndicator } from './RarityIndicator'
export { CategoryBadge } from './CategoryBadge'  // NEW
```

### Step 4: Use in Components

```typescript
import { CategoryBadge } from '@/components/design-system'

// In CoinCard or other component
<CategoryBadge category={coin.category} size="sm" />
```

---

## Quick Reference: File Modification Checklist

### Adding a Field

- [ ] `models/*.py` - SQLAlchemy model
- [ ] Database migration (Alembic or manual)
- [ ] `schemas/*.py` - Pydantic schemas
- [ ] `types/*.ts` - TypeScript types
- [ ] `CoinForm.tsx` - Form input
- [ ] `CoinDetailPage.tsx` - Display

### Adding an Endpoint

- [ ] `schemas/*.py` - Request/response schemas
- [ ] `crud/*.py` - Database operations
- [ ] `services/*.py` - Business logic (if needed)
- [ ] `routers/*.py` - API endpoint
- [ ] `hooks/*.ts` - TanStack Query hook
- [ ] Component to consume the hook

### Adding a Scraper

- [ ] `services/scrapers/*.py` - Scraper class
- [ ] `services/scrapers/orchestrator.py` - Register scraper
- [ ] Test with sample URLs

### Adding a Filter

- [ ] `crud/*.py` - Query filter logic
- [ ] `routers/*.py` - Query parameter
- [ ] `stores/filterStore.ts` - Store state + toParams
- [ ] `CoinFilters.tsx` - UI control

---

**Previous:** [08-CODING-PATTERNS.md](08-CODING-PATTERNS.md) - Coding conventions  
**Back to:** [README.md](README.md) - Index
