# Task Recipes (V2 Clean Architecture)

Step-by-step guides for common development tasks following Clean Architecture principles.

---

## Recipe 1: Add a New Field to Coin Entity

**Goal:** Add `diameter_max_mm` field to support irregular flan coins.

### Step 1: Backup Database (MANDATORY)

```bash
cd backend
cp coinstack_v2.db backups/coinstack_$(date +%Y%m%d_%H%M%S).db
```

**Why**: Required before any schema change. See [08-CRITICAL-RULES.md](08-CRITICAL-RULES.md).

### Step 2: Update Domain Entity

Edit `backend/src/domain/coin.py`:

```python
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal

@dataclass
class Coin:
    """Coin aggregate root."""

    # ... existing fields ...

    # Physical characteristics
    weight_g: Optional[Decimal]
    diameter_mm: Optional[Decimal]
    diameter_max_mm: Optional[Decimal]  # NEW - for irregular flans
    die_axis: Optional[int]
```

**Note**: Domain entity has no dependencies on SQLAlchemy or Pydantic.

### Step 3: Update ORM Model

Edit `backend/src/infrastructure/persistence/orm.py`:

```python
from sqlalchemy import Integer, String, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from decimal import Decimal

class CoinModel(Base):
    """ORM model (separate from domain entity)."""
    __tablename__ = "coins_v2"

    # ... existing fields ...

    # Physical measurements
    weight_g: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    diameter_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    diameter_max_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)  # NEW
    die_axis: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
```

**Important**: Use SQLAlchemy 2.0 `Mapped[T]` syntax (see [08-CRITICAL-RULES.md](08-CRITICAL-RULES.md)).

### Step 4: Update Repository Mapping

Edit `backend/src/infrastructure/repositories/coin_repository.py`:

```python
class SqlAlchemyCoinRepository:

    def _to_domain(self, orm_coin: CoinModel) -> Coin:
        """Convert ORM model to domain entity."""
        return Coin(
            id=orm_coin.id,
            # ... existing fields ...
            weight_g=orm_coin.weight_g,
            diameter_mm=orm_coin.diameter_mm,
            diameter_max_mm=orm_coin.diameter_max_mm,  # NEW
            die_axis=orm_coin.die_axis,
        )

    def _to_orm(self, coin: Coin) -> CoinModel:
        """Convert domain entity to ORM model."""
        return CoinModel(
            id=coin.id,
            # ... existing fields ...
            weight_g=coin.weight_g,
            diameter_mm=coin.diameter_mm,
            diameter_max_mm=coin.diameter_max_mm,  # NEW
            die_axis=coin.die_axis,
        )
```

### Step 5: Run Database Migration

```bash
cd backend

# Option 1: Using Python directly
python -c "
from sqlalchemy import text
from src.infrastructure.persistence.database import engine

with engine.connect() as conn:
    conn.execute(text('ALTER TABLE coins_v2 ADD COLUMN diameter_max_mm DECIMAL(10,2)'))
    conn.commit()
print('Column added successfully')
"

# Option 2: Check with SQLite CLI
sqlite3 coinstack_v2.db "ALTER TABLE coins_v2 ADD COLUMN diameter_max_mm DECIMAL(10,2);"
sqlite3 coinstack_v2.db "PRAGMA table_info(coins_v2);" | grep diameter_max
```

### Step 6: Update Frontend TypeScript Types

Edit `frontend/src/domain/schemas.ts`:

```typescript
// Mirror backend domain entity
export interface Coin {
  id: number | null
  // ... existing fields ...

  // Physical characteristics
  weight_g: number | null
  diameter_mm: number | null
  diameter_max_mm: number | null  // NEW
  die_axis: number | null
}
```

### Step 7: Update Frontend Form

Edit `frontend/src/components/coins/CoinForm.tsx`:

```typescript
// In Physical characteristics section
<div className="grid grid-cols-2 md:grid-cols-3 gap-4">
  <div>
    <Label htmlFor="weight_g">Weight (g)</Label>
    <Input
      id="weight_g"
      type="number"
      step="0.01"
      {...register('weight_g', { valueAsNumber: true })}
    />
  </div>

  <div>
    <Label htmlFor="diameter_mm">Diameter (mm)</Label>
    <Input
      id="diameter_mm"
      type="number"
      step="0.1"
      {...register('diameter_mm', { valueAsNumber: true })}
    />
  </div>

  <div>
    <Label htmlFor="diameter_max_mm">Max Diameter (mm)</Label>  {/* NEW */}
    <Input
      id="diameter_max_mm"
      type="number"
      step="0.1"
      {...register('diameter_max_mm', { valueAsNumber: true })}
    />
    <p className="text-xs text-muted-foreground mt-1">
      For irregular flans
    </p>
  </div>
</div>
```

### Step 8: Update Detail View

Edit `frontend/src/features/collection/CoinDetailV3.tsx`:

```typescript
// In Physical section
<dl className="grid grid-cols-2 gap-4">
  <div>
    <dt className="text-sm text-muted-foreground">Weight</dt>
    <dd className="font-medium">
      {coin.weight_g ? `${coin.weight_g.toFixed(2)}g` : '—'}
    </dd>
  </div>

  <div>
    <dt className="text-sm text-muted-foreground">Diameter</dt>
    <dd className="font-medium">
      {coin.diameter_mm ? `${coin.diameter_mm.toFixed(1)}mm` : '—'}
      {coin.diameter_max_mm && coin.diameter_max_mm !== coin.diameter_mm && (
        <span className="text-muted-foreground ml-1">
          - {coin.diameter_max_mm.toFixed(1)}mm
        </span>
      )}
    </dd>
  </div>

  <div>
    <dt className="text-sm text-muted-foreground">Die Axis</dt>
    <dd className="font-medium">
      {coin.die_axis ? `${coin.die_axis}h` : '—'}
    </dd>
  </div>
</dl>
```

### Step 9: Test End-to-End

1. **Backend**:
   ```bash
   cd backend
   python -m uvicorn src.infrastructure.web.main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. **Check Swagger UI**: http://localhost:8000/docs
   - Verify `diameter_max_mm` appears in POST `/api/v2/coins` schema
   - Verify it appears in GET `/api/v2/coins/{id}` response

3. **Frontend**:
   ```bash
   cd frontend
   npm run dev  # Port 3000
   ```

4. **Manual Test**:
   - Navigate to "Add Coin"
   - Fill in physical fields including new "Max Diameter"
   - Save coin
   - View coin detail page
   - Verify max diameter displays correctly

5. **Run Tests**:
   ```bash
   # Backend
   cd backend
   pytest tests/unit/domain/test_coin_domain.py -v

   # Frontend
   cd frontend
   npm run test
   ```

---

## Recipe 2: Add a New API Endpoint (Clean Architecture)

**Goal:** Add endpoint to get price statistics for a coin using Clean Architecture patterns.

### Step 1: Create Domain Service (if needed)

Edit `backend/src/domain/services/price_analyzer.py`:

```python
from decimal import Decimal
from statistics import mean
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class PriceAnalysis:
    """Value object for price analysis results."""
    avg_price: Optional[Decimal]
    min_price: Optional[Decimal]
    max_price: Optional[Decimal]
    price_trend: str  # "rising", "stable", "falling", "unknown"
    sample_size: int

class PriceAnalyzer:
    """Domain service for price analysis (no dependencies)."""

    def analyze(self, prices: List[Decimal]) -> PriceAnalysis:
        """Analyze price history and return statistics."""
        if not prices:
            return PriceAnalysis(
                avg_price=None,
                min_price=None,
                max_price=None,
                price_trend="unknown",
                sample_size=0
            )

        avg = Decimal(str(mean(prices)))

        # Calculate trend
        trend = "stable"
        if len(prices) >= 6:
            recent = mean(prices[:3])
            older = mean(prices[-3:])
            if recent > older * Decimal("1.15"):
                trend = "rising"
            elif recent < older * Decimal("0.85"):
                trend = "falling"

        return PriceAnalysis(
            avg_price=avg,
            min_price=min(prices),
            max_price=max(prices),
            price_trend=trend,
            sample_size=len(prices)
        )
```

**Note**: Domain service has NO dependencies on infrastructure.

### Step 2: Create Use Case

Create `backend/src/application/commands/analyze_coin_price.py`:

```python
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from src.domain.repositories import ICoinRepository, IAuctionDataRepository
from src.domain.services.price_analyzer import PriceAnalyzer, PriceAnalysis

@dataclass
class AnalyzeCoinPriceResult:
    """DTO for use case output."""
    coin_id: int
    analysis: PriceAnalysis
    comparable_count: int

class AnalyzeCoinPriceUseCase:
    """Use case: Analyze coin price based on auction history."""

    def __init__(
        self,
        coin_repo: ICoinRepository,  # Interface, not implementation
        auction_repo: IAuctionDataRepository
    ):
        self.coin_repo = coin_repo
        self.auction_repo = auction_repo
        self.analyzer = PriceAnalyzer()

    def execute(self, coin_id: int) -> AnalyzeCoinPriceResult:
        """Execute price analysis for coin."""
        # Get coin (validate it exists)
        coin = self.coin_repo.get_by_id(coin_id)
        if not coin:
            raise ValueError(f"Coin {coin_id} not found")

        # Get comparable auctions
        comparables = self.auction_repo.get_comparables(
            coin_id=coin_id,
            limit=50
        )

        # Extract prices
        prices = [
            lot.price_realized
            for lot in comparables
            if lot.price_realized
        ]

        # Analyze with domain service
        analysis = self.analyzer.analyze(prices)

        return AnalyzeCoinPriceResult(
            coin_id=coin_id,
            analysis=analysis,
            comparable_count=len(comparables)
        )
```

**Note**: Use case depends on repository **interfaces** (Protocols), not implementations.

### Step 3: Add Repository Method (if needed)

Edit `backend/src/infrastructure/repositories/auction_data_repository.py`:

```python
from sqlalchemy.orm import Session
from typing import List
from src.domain.auction import AuctionLot
from src.domain.repositories import IAuctionDataRepository
from src.infrastructure.persistence.orm import AuctionDataModel, CoinModel

class SqlAlchemyAuctionDataRepository:
    """Concrete implementation of auction repository."""

    def __init__(self, session: Session):
        self.session = session

    def get_comparables(self, coin_id: int, limit: int = 10) -> List[AuctionLot]:
        """Get comparable auction lots for a coin."""
        # Get coin to find matching attributes
        coin = self.session.query(CoinModel).filter(
            CoinModel.id == coin_id
        ).first()

        if not coin:
            return []

        # Find similar auctions
        query = self.session.query(AuctionDataModel).filter(
            AuctionDataModel.category == coin.category,
            AuctionDataModel.denomination == coin.denomination,
            AuctionDataModel.issuing_authority.ilike(f"%{coin.issuing_authority}%")
        ).order_by(
            AuctionDataModel.sale_date.desc()
        ).limit(limit)

        orm_lots = query.all()
        return [self._to_domain(lot) for lot in orm_lots]

    def _to_domain(self, orm_lot: AuctionDataModel) -> AuctionLot:
        """Convert ORM to domain entity."""
        return AuctionLot(
            url=orm_lot.url,
            auction_house=orm_lot.auction_house,
            price_realized=orm_lot.price_realized,
            # ... map all fields
        )
```

### Step 4: Add Web Router Endpoint

Edit `backend/src/infrastructure/web/routers/v2.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.application.commands.analyze_coin_price import (
    AnalyzeCoinPriceUseCase,
    AnalyzeCoinPriceResult
)
from src.domain.repositories import ICoinRepository, IAuctionDataRepository
from src.infrastructure.web.dependencies import (
    get_coin_repository,
    get_auction_repository
)

router = APIRouter()

# Response schema (Pydantic for web layer)
class PriceAnalysisResponse(BaseModel):
    coin_id: int
    avg_price: float | None
    min_price: float | None
    max_price: float | None
    price_trend: str
    sample_size: int
    comparable_count: int

@router.get("/coins/{coin_id}/price-analysis", response_model=PriceAnalysisResponse)
def get_coin_price_analysis(
    coin_id: int,
    coin_repo: ICoinRepository = Depends(get_coin_repository),
    auction_repo: IAuctionDataRepository = Depends(get_auction_repository)
):
    """Get price analysis for a coin (thin adapter to use case)."""
    # Create use case with injected dependencies
    use_case = AnalyzeCoinPriceUseCase(coin_repo, auction_repo)

    try:
        # Execute use case
        result = use_case.execute(coin_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Map to web response schema
    return PriceAnalysisResponse(
        coin_id=result.coin_id,
        avg_price=float(result.analysis.avg_price) if result.analysis.avg_price else None,
        min_price=float(result.analysis.min_price) if result.analysis.min_price else None,
        max_price=float(result.analysis.max_price) if result.analysis.max_price else None,
        price_trend=result.analysis.price_trend,
        sample_size=result.analysis.sample_size,
        comparable_count=result.comparable_count
    )
```

**Note**: Router is a thin adapter. Business logic is in use case.

### Step 5: Add Frontend Hook

Edit `frontend/src/api/v2.ts`:

```typescript
import { useQuery } from '@tanstack/react-query'
import { apiClient } from './client'

export interface PriceAnalysis {
  coin_id: number
  avg_price: number | null
  min_price: number | null
  max_price: number | null
  price_trend: 'rising' | 'stable' | 'falling' | 'unknown'
  sample_size: number
  comparable_count: number
}

export function usePriceAnalysis(coinId: number) {
  return useQuery({
    queryKey: ['coins', coinId, 'price-analysis'],
    queryFn: async () => {
      const { data } = await apiClient.get<PriceAnalysis>(
        `/api/v2/coins/${coinId}/price-analysis`
      )
      return data
    },
    enabled: coinId > 0,
    staleTime: 5 * 60 * 1000  // 5 minutes
  })
}
```

### Step 6: Add UI Component

Create `frontend/src/components/coins/PriceAnalysisCard.tsx`:

```typescript
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { usePriceAnalysis } from '@/api/v2'

interface Props {
  coinId: number
}

export function PriceAnalysisCard({ coinId }: Props) {
  const { data: analysis, isLoading } = usePriceAnalysis(coinId)

  if (isLoading) {
    return <div>Loading price analysis...</div>
  }

  if (!analysis || analysis.sample_size === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Price Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">No comparable auctions found</p>
        </CardContent>
      </Card>
    )
  }

  const trendIcon = {
    rising: <TrendingUp className="w-4 h-4 text-green-500" />,
    falling: <TrendingDown className="w-4 h-4 text-red-500" />,
    stable: <Minus className="w-4 h-4 text-yellow-500" />,
    unknown: <Minus className="w-4 h-4 text-gray-400" />
  }[analysis.price_trend]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Price Analysis
          <Badge variant="outline" className="flex items-center gap-1">
            {trendIcon}
            {analysis.price_trend}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-2 gap-4">
          <div>
            <dt className="text-sm text-muted-foreground">Average</dt>
            <dd className="text-lg font-semibold">
              {analysis.avg_price ? `$${analysis.avg_price.toFixed(2)}` : '—'}
            </dd>
          </div>

          <div>
            <dt className="text-sm text-muted-foreground">Range</dt>
            <dd className="text-lg font-semibold">
              {analysis.min_price && analysis.max_price
                ? `$${analysis.min_price.toFixed(0)} - $${analysis.max_price.toFixed(0)}`
                : '—'}
            </dd>
          </div>
        </dl>

        <p className="text-xs text-muted-foreground mt-4">
          Based on {analysis.comparable_count} comparable auction{analysis.comparable_count !== 1 ? 's' : ''}
        </p>
      </CardContent>
    </Card>
  )
}
```

### Step 7: Test

1. **Unit Test Domain Service** (`backend/tests/unit/domain/test_price_analyzer.py`):
   ```python
   from decimal import Decimal
   from src.domain.services.price_analyzer import PriceAnalyzer

   def test_price_analyzer_calculates_average():
       analyzer = PriceAnalyzer()
       prices = [Decimal("100"), Decimal("200"), Decimal("300")]

       result = analyzer.analyze(prices)

       assert result.avg_price == Decimal("200")
       assert result.min_price == Decimal("100")
       assert result.max_price == Decimal("300")
       assert result.sample_size == 3
   ```

2. **Unit Test Use Case** (with mock repositories):
   ```python
   from unittest.mock import Mock
   from src.application.commands.analyze_coin_price import AnalyzeCoinPriceUseCase

   def test_analyze_coin_price_use_case():
       # Mock repositories
       coin_repo = Mock()
       auction_repo = Mock()

       # Setup mocks
       coin_repo.get_by_id.return_value = Mock(id=1)
       auction_repo.get_comparables.return_value = [
           Mock(price_realized=Decimal("100")),
           Mock(price_realized=Decimal("200"))
       ]

       # Execute use case
       use_case = AnalyzeCoinPriceUseCase(coin_repo, auction_repo)
       result = use_case.execute(1)

       assert result.coin_id == 1
       assert result.analysis.avg_price == Decimal("150")
   ```

3. **Integration Test Endpoint**:
   ```bash
   curl http://localhost:8000/api/v2/coins/1/price-analysis
   ```

4. **Frontend Manual Test**:
   - Navigate to coin detail page
   - Verify price analysis card displays
   - Check trend indicator (up/down/stable arrows)

---

## Recipe 3: Add a New Scraper

**Goal:** Add scraper for a new auction house following V2 patterns.

### Step 1: Create Scraper Implementation

Create `backend/src/infrastructure/scrapers/example/scraper.py`:

```python
from typing import Optional
from src.domain.auction import AuctionLot
from src.infrastructure.scrapers.base_playwright import BaseScraper

class ExampleAuctionScraper(BaseScraper):
    """Scraper for Example Auction House."""

    def can_handle(self, url: str) -> bool:
        """Check if this scraper handles the URL."""
        return "exampleauctions.com" in url

    async def scrape(self, url: str) -> AuctionLot:
        """Scrape auction lot from URL."""
        # Fetch HTML with Playwright
        html = await self._fetch_html(url)

        # Parse HTML (using BeautifulSoup or custom parser)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Extract data
        lot_number = soup.select_one('.lot-number').text.strip()
        title = soup.select_one('h1.title').text.strip()
        price_text = soup.select_one('.price').text.strip()

        # Clean and convert price
        price = self._parse_price(price_text)

        # Create domain entity
        return AuctionLot(
            url=url,
            auction_house="Example Auctions",
            lot_number=lot_number,
            title=title,
            price_realized=price,
            # ... extract all relevant fields
        )

    def _parse_price(self, price_text: str) -> Optional[Decimal]:
        """Parse price from text like '$1,234.56'."""
        import re
        from decimal import Decimal

        # Remove currency symbols and commas
        cleaned = re.sub(r'[^\d.]', '', price_text)
        if not cleaned:
            return None

        return Decimal(cleaned)
```

### Step 2: Register Scraper

Edit `backend/src/infrastructure/web/routers/scrape_v2.py`:

```python
from src.infrastructure.scrapers.example.scraper import ExampleAuctionScraper
from src.domain.services.scraper_orchestrator import ScraperOrchestrator

# Register all scrapers
scrapers = [
    HeritageScraper(),
    CNGScraper(),
    BiddrScraper(),
    EBayScraper(),
    ExampleAuctionScraper(),  # NEW
]

orchestrator = ScraperOrchestrator(scrapers)
```

### Step 3: Test Scraper

Create `backend/tests/unit/infrastructure/scrapers/test_example_scraper.py`:

```python
import pytest
from src.infrastructure.scrapers.example.scraper import ExampleAuctionScraper

@pytest.mark.unit
def test_example_scraper_can_handle():
    scraper = ExampleAuctionScraper()

    assert scraper.can_handle("https://exampleauctions.com/lot/12345")
    assert not scraper.can_handle("https://othersite.com/lot/12345")

@pytest.mark.integration
async def test_example_scraper_live():
    scraper = ExampleAuctionScraper()
    url = "https://exampleauctions.com/lot/test-coin"

    lot = await scraper.scrape(url)

    assert lot.url == url
    assert lot.auction_house == "Example Auctions"
    assert lot.lot_number is not None
```

**Run tests**:
```bash
pytest tests/unit/infrastructure/scrapers/test_example_scraper.py -v
```

---

## Recipe 4: Add Controlled Vocabulary Term

**Goal:** Add new issuing authority to controlled vocabulary.

### Step 1: Create Domain Entity

Vocabulary is already defined in `src/domain/vocab.py`:

```python
@dataclass
class VocabTerm:
    id: Optional[int]
    term_type: str  # "issuer", "mint", "ruler"
    canonical_name: str
    display_name: Optional[str]
    variants: List[str] = field(default_factory=list)
    category: Optional[str]
    start_year: Optional[int]
    end_year: Optional[int]
    coin_count: int = 0
```

### Step 2: Use Vocabulary API

**Add via API** (POST to `/api/v2/vocab/issuers`):

```bash
curl -X POST http://localhost:8000/api/v2/vocab/issuers \
  -H "Content-Type: application/json" \
  -d '{
    "canonical_name": "Trajan",
    "display_name": "Marcus Ulpius Traianus",
    "variants": ["Traianus", "M. Ulpius Traianus"],
    "category": "imperial",
    "start_year": 98,
    "end_year": 117
  }'
```

**Or add programmatically**:

```python
from src.domain.vocab import VocabTerm
from src.infrastructure.repositories.vocab_repository import SqlAlchemyVocabRepository
from src.infrastructure.persistence.database import SessionLocal

# Create term
term = VocabTerm(
    id=None,
    term_type="issuer",
    canonical_name="Trajan",
    display_name="Marcus Ulpius Traianus",
    variants=["Traianus", "M. Ulpius Traianus"],
    category="imperial",
    start_year=98,
    end_year=117,
    coin_count=0
)

# Save via repository
db = SessionLocal()
repo = SqlAlchemyVocabRepository(db)
saved_term = repo.save(term)
db.commit()
db.close()

print(f"Created vocabulary term: {saved_term.canonical_name}")
```

### Step 3: Use in Autocomplete

The frontend `VocabAutocomplete` component automatically uses vocabulary:

```typescript
// frontend/src/components/coins/VocabAutocomplete.tsx
<VocabAutocomplete
  termType="issuer"
  value={issuingAuthority}
  onChange={setIssuingAuthority}
  placeholder="Search issuers..."
/>
```

Vocabulary terms are fetched from `/api/v2/vocab/issuers?search={query}`.

---

## Key Principles (V2)

### 1. Clean Architecture Flow

```
User Input (Web)
    ↓
Router (thin adapter)
    ↓
Use Case (application logic)
    ↓
Repository Interface (domain)
    ↓
Repository Implementation (infrastructure)
    ↓
ORM Model (infrastructure)
    ↓
Database
```

### 2. Dependency Rule

- Domain depends on NOTHING
- Application depends on Domain only
- Infrastructure depends on both

### 3. Repository Pattern

- Use cases depend on **interfaces** (Protocols)
- Repositories use `flush()`, not `commit()`
- Transaction managed by `get_db()` dependency

### 4. Database Safety

**ALWAYS backup before schema changes**:
```bash
cp backend/coinstack_v2.db backend/backups/coinstack_$(date +%Y%m%d_%H%M%S).db
```

See [08-CRITICAL-RULES.md](08-CRITICAL-RULES.md) for full requirements.

---

**Previous:** [08-CODING-PATTERNS.md](08-CODING-PATTERNS.md) - Coding patterns
**Next:** [06-FILE-LOCATIONS.md](06-FILE-LOCATIONS.md) - File location reference
