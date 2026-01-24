# Coding Patterns and Conventions

## Python/Backend Conventions

### File Organization

```
app/
├── models/          # One file per entity or related group
│   ├── coin.py      # Coin model + related enums
│   └── audit.py     # Audit-related models grouped
├── schemas/         # Mirror model structure
│   └── coin.py      # Pydantic schemas for coin
├── routers/         # One file per API domain
│   └── coins.py     # All /api/coins/* endpoints
├── crud/            # One file per main entity
│   └── coin.py      # Coin database operations
└── services/        # Business logic, can have subdirs
    └── audit/       # Complex feature gets a folder
```

### Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| Files | snake_case | `coin_reference.py` |
| Classes | PascalCase | `CoinReference` |
| Functions | snake_case | `get_coin_by_id` |
| Variables | snake_case | `coin_list` |
| Constants | UPPER_SNAKE | `DEFAULT_PAGE_SIZE` |
| Enums | PascalCase class, lowercase values | `class Metal(str, Enum): gold = "gold"` |

### Type Hints

Always use type hints for function signatures:

```python
# Good
def get_coin(db: Session, coin_id: int) -> Coin | None:
    ...

def get_coins(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    filters: CoinFilters | None = None,
) -> tuple[list[Coin], int]:
    ...

# Bad - missing types
def get_coin(db, coin_id):
    ...
```

### SQLAlchemy Model Pattern

```python
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Coin(Base):
    __tablename__ = "coins"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Required field
    category: Mapped[str] = mapped_column(String(50))
    
    # Optional field (nullable)
    denomination: Mapped[str | None] = mapped_column(String(100))
    
    # Foreign key
    mint_id: Mapped[int | None] = mapped_column(ForeignKey("mints.id"))
    
    # Relationships
    mint: Mapped["Mint"] = relationship(back_populates="coins")
    references: Mapped[list["CoinReference"]] = relationship(
        back_populates="coin",
        cascade="all, delete-orphan"
    )
```

### Pydantic Schema Pattern

```python
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date

# Base with shared fields
class CoinBase(BaseModel):
    category: Category
    denomination: str | None = None
    metal: Metal | None = None

# Create schema - required fields for creation
class CoinCreate(CoinBase):
    # Override to make required
    category: Category = Category.imperial

# Update schema - all fields optional
class CoinUpdate(BaseModel):
    category: Category | None = None
    denomination: str | None = None
    metal: Metal | None = None

# Response schema - includes computed fields
class CoinDetail(CoinBase):
    id: int
    created_at: datetime
    mint: MintSchema | None = None
    references: list[CoinReferenceSchema] = []
    
    model_config = ConfigDict(from_attributes=True)
```

### Router Pattern

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.coin import CoinCreate, CoinDetail, PaginatedCoins
from app.crud import coin as crud_coin

router = APIRouter(prefix="/api/coins", tags=["coins"])

@router.get("", response_model=PaginatedCoins)
def list_coins(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Category | None = None,
    metal: Metal | None = None,
):
    """List coins with optional filters."""
    filters = CoinFilters(category=category, metal=metal)
    coins, total = crud_coin.get_coins(
        db, skip=(page - 1) * per_page, limit=per_page, filters=filters
    )
    return PaginatedCoins(
        items=coins,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )

@router.get("/{coin_id}", response_model=CoinDetail)
def get_coin(coin_id: int, db: Session = Depends(get_db)):
    """Get a single coin by ID."""
    coin = crud_coin.get_coin(db, coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    return coin

@router.post("", response_model=CoinDetail, status_code=201)
def create_coin(coin: CoinCreate, db: Session = Depends(get_db)):
    """Create a new coin."""
    return crud_coin.create_coin(db, coin)
```

### CRUD Pattern

```python
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload
from app.models.coin import Coin
from app.schemas.coin import CoinCreate, CoinUpdate

def get_coin(db: Session, coin_id: int) -> Coin | None:
    """Get single coin with relationships."""
    stmt = (
        select(Coin)
        .options(
            selectinload(Coin.mint),
            selectinload(Coin.references),
            selectinload(Coin.images),
        )
        .where(Coin.id == coin_id)
    )
    return db.execute(stmt).scalar_one_or_none()

def get_coins(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    filters: CoinFilters | None = None,
) -> tuple[list[Coin], int]:
    """Get paginated coins with filters."""
    stmt = select(Coin)
    
    if filters:
        if filters.category:
            stmt = stmt.where(Coin.category == filters.category)
        if filters.metal:
            stmt = stmt.where(Coin.metal == filters.metal)
    
    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar_one()
    
    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)
    coins = db.execute(stmt).scalars().all()
    
    return list(coins), total

def create_coin(db: Session, coin_data: CoinCreate) -> Coin:
    """Create new coin."""
    coin = Coin(**coin_data.model_dump(exclude_unset=True))
    db.add(coin)
    db.commit()
    db.refresh(coin)
    return coin

def update_coin(db: Session, coin_id: int, coin_data: CoinUpdate) -> Coin | None:
    """Update existing coin."""
    coin = get_coin(db, coin_id)
    if not coin:
        return None
    
    update_data = coin_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(coin, field, value)
    
    db.commit()
    db.refresh(coin)
    return coin
```

### Service Pattern

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class CatalogResult:
    """Result from catalog lookup."""
    found: bool
    source: str
    data: dict | None = None

class CatalogService(ABC):
    """Abstract base for catalog services."""
    
    @abstractmethod
    async def lookup(self, reference: str) -> CatalogResult | None:
        """Look up a reference in the catalog."""
        pass
    
    @abstractmethod
    def can_handle(self, system: str) -> bool:
        """Check if service handles this reference system."""
        pass

class OCREService(CatalogService):
    """OCRE catalog service for RIC references."""
    
    BASE_URL = "http://numismatics.org/ocre/"
    
    def can_handle(self, system: str) -> bool:
        return system.upper() == "RIC"
    
    async def lookup(self, reference: str) -> CatalogResult | None:
        # Parse reference
        parsed = self._parse_reference(reference)
        if not parsed:
            return None
        
        # Call external API
        url = f"{self.BASE_URL}id/{parsed['id']}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code != 200:
                return CatalogResult(found=False, source="OCRE")
            
            data = self._parse_response(response.json())
            return CatalogResult(found=True, source="OCRE", data=data)
    
    def _parse_reference(self, reference: str) -> dict | None:
        # Implementation...
        pass
```

### Error Handling

```python
from fastapi import HTTPException

# In routers - use HTTPException
@router.get("/{id}")
def get_item(id: int, db: Session = Depends(get_db)):
    item = crud.get_item(db, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# In services - use custom exceptions
class CatalogLookupError(Exception):
    """Error looking up catalog reference."""
    pass

class ScraperError(Exception):
    """Error during scraping."""
    pass

# Catch in router
@router.post("/scrape")
def scrape_url(url: str, db: Session = Depends(get_db)):
    try:
        result = scraper_service.scrape(url)
    except ScraperError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result
```

---

## TypeScript/Frontend Conventions

### File Organization

```
src/
├── pages/           # One file per route
│   └── CollectionPage.tsx
├── components/
│   ├── ui/          # Generic UI components (shadcn)
│   ├── layout/      # App structure components
│   └── coins/       # Feature-specific components
├── hooks/           # One file per data domain
│   └── useCoins.ts
├── stores/          # One file per store
│   └── filterStore.ts
├── types/           # Type definitions
│   └── coin.ts
└── lib/             # Utilities
    └── utils.ts
```

### Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| Files (components) | PascalCase | `CoinCard.tsx` |
| Files (hooks) | camelCase with use prefix | `useCoins.ts` |
| Files (stores) | camelCase with Store suffix | `filterStore.ts` |
| Components | PascalCase | `CoinCard` |
| Hooks | camelCase with use prefix | `useCoins` |
| Stores | camelCase with use prefix | `useFilterStore` |
| Interfaces | PascalCase, I prefix optional | `CoinDetail` or `ICoinDetail` |
| Types | PascalCase | `CoinFilters` |
| Constants | UPPER_SNAKE | `DEFAULT_PAGE_SIZE` |

### Component Pattern

```typescript
import { useState } from 'react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { MetalBadge } from '@/components/design-system/MetalBadge'
import { CoinListItem } from '@/types/coin'

interface CoinCardProps {
  coin: CoinListItem
  onClick?: () => void
  className?: string
}

export function CoinCard({ coin, onClick, className }: CoinCardProps) {
  const [isHovered, setIsHovered] = useState(false)
  
  return (
    <Card 
      className={cn('cursor-pointer transition-shadow', className)}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <CardHeader>
        <img 
          src={coin.primary_image_url || '/placeholder.jpg'} 
          alt={coin.denomination || 'Coin'}
          className="w-full h-40 object-cover rounded"
        />
      </CardHeader>
      <CardContent>
        <h3 className="font-medium">{coin.issuing_authority}</h3>
        <p className="text-sm text-muted-foreground">{coin.denomination}</p>
        <div className="flex gap-2 mt-2">
          {coin.metal && <MetalBadge metal={coin.metal} />}
        </div>
      </CardContent>
    </Card>
  )
}
```

### Hook Pattern (TanStack Query)

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { CoinDetail, CoinCreate, CoinUpdate, PaginatedCoins } from '@/types/coin'
import { useFilterStore } from '@/stores/filterStore'

// Query keys - use factory pattern
const coinKeys = {
  all: ['coins'] as const,
  lists: () => [...coinKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...coinKeys.lists(), filters] as const,
  details: () => [...coinKeys.all, 'detail'] as const,
  detail: (id: number) => [...coinKeys.details(), id] as const,
}

// List query
export function useCoins() {
  const filters = useFilterStore((s) => s.toParams())
  
  return useQuery({
    queryKey: coinKeys.list(filters),
    queryFn: async (): Promise<PaginatedCoins> => {
      const response = await api.get('/coins', { params: filters })
      return response.data
    },
  })
}

// Detail query
export function useCoin(id: number) {
  return useQuery({
    queryKey: coinKeys.detail(id),
    queryFn: async (): Promise<CoinDetail> => {
      const response = await api.get(`/coins/${id}`)
      return response.data
    },
    enabled: !!id,
  })
}

// Create mutation
export function useCreateCoin() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data: CoinCreate): Promise<CoinDetail> => {
      const response = await api.post('/coins', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: coinKeys.lists() })
    },
  })
}

// Update mutation
export function useUpdateCoin() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: CoinUpdate }): Promise<CoinDetail> => {
      const response = await api.put(`/coins/${id}`, data)
      return response.data
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: coinKeys.lists() })
      queryClient.invalidateQueries({ queryKey: coinKeys.detail(id) })
    },
  })
}

// Delete mutation
export function useDeleteCoin() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (id: number): Promise<void> => {
      await api.delete(`/coins/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: coinKeys.lists() })
    },
  })
}
```

### Store Pattern (Zustand)

```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { Category, Metal, Rarity } from '@/types/coin'

interface FilterState {
  // State
  category: Category | null
  metal: Metal | null
  rarity: Rarity | null
  search: string
  sortBy: string
  sortDir: 'asc' | 'desc'
  page: number
  perPage: number
  
  // Actions
  setFilter: <K extends keyof FilterState>(key: K, value: FilterState[K]) => void
  setSort: (field: string, dir?: 'asc' | 'desc') => void
  setPage: (page: number) => void
  reset: () => void
  
  // Computed
  toParams: () => Record<string, unknown>
  getActiveFilterCount: () => number
}

const initialState = {
  category: null,
  metal: null,
  rarity: null,
  search: '',
  sortBy: 'created_at',
  sortDir: 'desc' as const,
  page: 1,
  perPage: 20,
}

export const useFilterStore = create<FilterState>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      setFilter: (key, value) => set({ [key]: value, page: 1 }),
      
      setSort: (field, dir) => set((state) => ({
        sortBy: field,
        sortDir: dir ?? (state.sortBy === field && state.sortDir === 'asc' ? 'desc' : 'asc'),
        page: 1,
      })),
      
      setPage: (page) => set({ page }),
      
      reset: () => set(initialState),
      
      toParams: () => {
        const state = get()
        const params: Record<string, unknown> = {
          page: state.page,
          per_page: state.perPage,
          sort_by: state.sortBy,
          sort_dir: state.sortDir,
        }
        if (state.category) params.category = state.category
        if (state.metal) params.metal = state.metal
        if (state.rarity) params.rarity = state.rarity
        if (state.search) params.search = state.search
        return params
      },
      
      getActiveFilterCount: () => {
        const state = get()
        let count = 0
        if (state.category) count++
        if (state.metal) count++
        if (state.rarity) count++
        if (state.search) count++
        return count
      },
    }),
    { name: 'coinstack-filters' }
  )
)
```

### Type Definitions

```typescript
// Use enums for fixed values
export enum Category {
  republic = 'republic',
  imperial = 'imperial',
  provincial = 'provincial',
  byzantine = 'byzantine',
  greek = 'greek',
  other = 'other',
}

// Use interfaces for object shapes
export interface CoinListItem {
  id: number
  category: Category
  metal: Metal | null
  denomination: string | null
  issuing_authority: string | null
  grade: string | null
  acquisition_price: number | null
  primary_image_url: string | null
}

// Extend interfaces for detailed responses
export interface CoinDetail extends CoinListItem {
  created_at: string
  updated_at: string
  obverse_legend: string | null
  reverse_legend: string | null
  // ... more fields
  mint: Mint | null
  references: CoinReference[]
  images: CoinImage[]
}

// Use types for unions and utilities
export type SortDirection = 'asc' | 'desc'
export type CoinFilters = Partial<Pick<CoinDetail, 'category' | 'metal' | 'rarity'>>
```

### Form Pattern

```typescript
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'

const coinSchema = z.object({
  category: z.nativeEnum(Category),
  denomination: z.string().optional(),
  metal: z.nativeEnum(Metal).optional(),
  weight_g: z.coerce.number().positive().optional(),
  issuing_authority: z.string().min(1, 'Ruler is required'),
})

type CoinFormData = z.infer<typeof coinSchema>

interface CoinFormProps {
  defaultValues?: Partial<CoinFormData>
  onSubmit: (data: CoinFormData) => void
  isLoading?: boolean
}

export function CoinForm({ defaultValues, onSubmit, isLoading }: CoinFormProps) {
  const form = useForm<CoinFormData>({
    resolver: zodResolver(coinSchema),
    defaultValues: {
      category: Category.imperial,
      ...defaultValues,
    },
  })
  
  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label>Category</label>
        <Select {...form.register('category')}>
          {Object.values(Category).map((cat) => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </Select>
        {form.formState.errors.category && (
          <p className="text-sm text-destructive">
            {form.formState.errors.category.message}
          </p>
        )}
      </div>
      
      <div>
        <label>Ruler</label>
        <Input {...form.register('issuing_authority')} />
        {form.formState.errors.issuing_authority && (
          <p className="text-sm text-destructive">
            {form.formState.errors.issuing_authority.message}
          </p>
        )}
      </div>
      
      <Button type="submit" disabled={isLoading}>
        {isLoading ? 'Saving...' : 'Save'}
      </Button>
    </form>
  )
}
```

---

## Common Patterns

### Adding a New Field

1. **Model** - Add to SQLAlchemy model
2. **Migration** - Update database (if using Alembic)
3. **Schema** - Add to Pydantic schemas (Create, Update, Detail)
4. **CRUD** - Update if field needs special handling
5. **Router** - Add filter/sort if needed
6. **Type** - Add to TypeScript interface
7. **Form** - Add to form schema and component
8. **Display** - Add to detail/list views

### Adding a New Endpoint

1. **Schema** - Define request/response Pydantic schemas
2. **Service** - Implement business logic
3. **CRUD** - Add database operations if needed
4. **Router** - Add endpoint function
5. **Register** - Include router in main.py if new file
6. **Hook** - Add TanStack Query hook
7. **UI** - Add component to call the hook

### Error Handling Pattern

```python
# Backend - Custom exception
class DuplicateCoinError(Exception):
    pass

# Backend - Router handling
@router.post("")
def create_coin(coin: CoinCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_coin(db, coin)
    except DuplicateCoinError:
        raise HTTPException(400, "Duplicate coin detected")

# Frontend - Hook with error handling
export function useCreateCoin() {
  return useMutation({
    mutationFn: createCoin,
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to create coin')
    },
    onSuccess: () => {
      toast.success('Coin created')
    },
  })
}
```

---

**Previous:** [07-API-REFERENCE.md](07-API-REFERENCE.md) - API endpoints  
**Next:** [09-TASK-RECIPES.md](09-TASK-RECIPES.md) - Step-by-step task guides
