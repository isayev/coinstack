# Frontend Components Reference - AI Assistant Guide

> Comprehensive guide to CoinStack React components, patterns, and implementation details.
> **Last Updated**: January 2026 (v3.1)

---

## Quick Reference

```
✅ Use @/ alias for all imports
✅ Use design tokens from index.css
✅ Use TanStack Query v5 syntax (object-based)
✅ Use Zustand for client state
❌ NEVER use relative imports for cross-feature
❌ NEVER define plain TypeScript interfaces for domain types (use Zod)
❌ NEVER lazy load relationships in components
```

---

## 1. Component Architecture

### Directory Structure

```
frontend/src/
├── App.tsx                    # Root component, providers, routes
├── index.css                  # Design tokens, global styles
├── main.tsx                   # React entry point
│
├── pages/                     # Route-level components
│   ├── CollectionPage.tsx     # Main coin grid/table
│   ├── CoinDetailPage.tsx     # Single coin view
│   ├── AddCoinPage.tsx        # Create coin form
│   ├── EditCoinPage.tsx       # Edit coin form
│   ├── SeriesDashboard.tsx    # Series listing
│   ├── SeriesDetailPage.tsx   # Series slots view
│   ├── StatsPageV3.tsx        # Statistics dashboard
│   └── SettingsPage.tsx       # App settings
│
├── components/
│   ├── layout/                # App shell components
│   │   ├── AppShell.tsx       # Main layout wrapper
│   │   ├── Header.tsx         # Top navigation
│   │   ├── Sidebar.tsx        # Left navigation
│   │   ├── BottomPanel.tsx    # Expandable bottom charts
│   │   └── CommandBar/        # Top action bar
│   │
│   ├── coins/                 # Coin-specific components
│   │   ├── CoinCardV3.tsx     # Grid card (v3.1 design)
│   │   ├── CoinTableRowV3.tsx # Table row (v3.1 design)
│   │   ├── CoinForm.tsx       # Create/edit form
│   │   ├── CoinFilters.tsx    # Filter panel
│   │   └── VocabAutocomplete.tsx # Issuer/mint search
│   │
│   ├── dashboard/             # Dashboard widgets
│   │   ├── CategoryDonut.tsx  # Category distribution
│   │   ├── YearHistogram.tsx  # Year distribution
│   │   ├── CollectionHealthWidget.tsx
│   │   └── RulerTimeline.tsx
│   │
│   ├── design-system/         # Design system primitives
│   │   ├── colors.ts          # Color utilities
│   │   └── RarityIndicator.tsx
│   │
│   └── ui/                    # shadcn/ui base components
│       ├── badges/
│       │   ├── MetalBadge.tsx
│       │   └── GradeBadge.tsx
│       ├── button.tsx
│       ├── card.tsx
│       ├── dialog.tsx
│       └── ...
│
├── features/                  # Feature-specific components
│   └── collection/
│       ├── CoinListV3.tsx     # Grid/table view manager
│       ├── CoinDetailV3.tsx   # Detail display
│       ├── CollectionDashboard/
│       │   └── index.tsx      # Left sidebar dashboard
│       └── CollectionToolbar/
│           └── index.tsx      # Sort/filter/view controls
│
├── api/                       # API layer
│   ├── api.ts                 # Axios instance
│   └── v2.ts                  # API client + types
│
├── hooks/                     # Custom hooks
│   ├── useCoins.ts            # Coin CRUD hooks
│   └── useSeries.ts           # Series hooks
│
├── stores/                    # Zustand stores
│   ├── uiStore.ts             # UI state (sidebar, view mode)
│   └── filterStore.ts         # Filter/sort/pagination
│
└── domain/                    # Domain types (Zod schemas)
    └── schemas.ts             # Type definitions
```

---

## 2. Core Components

### 2.1 CoinCardV3 (Grid View)

**Location**: `frontend/src/components/coins/CoinCardV3.tsx`

**Purpose**: Displays a coin in grid view with v3.1 design system compliance.

**Key Features**:
- Horizontal layout (desktop) / vertical stack (mobile)
- 3D flip animation on hover to show reverse
- Category bar with matching border-radius
- Compact badge row: [Cert] [Grade] [Metal] [Rarity●]
- Price with performance indicator

**Props**:
```typescript
interface CoinCardV3Props {
  coin: DomainCoin
  onClick?: (coin: DomainCoin) => void
  compact?: boolean
}
```

**Usage**:
```typescript
import { CoinCardV3 } from '@/components/coins/CoinCardV3'

<CoinCardV3
  coin={coin}
  onClick={(c) => navigate(`/coins/${c.id}`)}
/>
```

**Key Implementation Details**:

```typescript
// Responsive dimensions (v3.1)
const cardMinWidth = isMobile ? 'auto' : '360px'
const cardHeight = isMobile ? 'auto' : '170px'
const imageWidth = isMobile ? '100%' : '160px'
const imageHeight = isMobile ? '180px' : '160px'

// Category bar with matching radius
<div style={{
  position: 'absolute',
  left: 0,
  top: 0,
  bottom: 0,
  width: '4px',
  background: `var(--cat-${categoryType})`,
  borderRadius: '8px 0 0 8px',  // MUST match card
  zIndex: 1,
}} />

// Badge row order
<div style={{ display: 'flex', gap: '3px' }}>
  {/* 1. Certification (if slabbed) */}
  {coin.grading.service && coin.grading.service !== 'none' && (
    <div className="cert-badge">{coin.grading.service}</div>
  )}
  
  {/* 2. Grade */}
  {coin.grading.grade && (
    <div className="grade-badge">{coin.grading.grade}</div>
  )}
  
  {/* 3. Metal */}
  {coin.metal && (
    <div className="metal-badge">{coin.metal}</div>
  )}
  
  {/* 4. Rarity dot */}
  {coin.rarity && (
    <RarityIndicator rarity={coin.rarity} variant="dot" />
  )}
</div>
```

### 2.2 CoinTableRowV3 (Table View)

**Location**: `frontend/src/components/coins/CoinTableRowV3.tsx`

**Purpose**: Displays a coin in table row format.

**Key Columns**:
1. Category bar (4px)
2. Thumbnail (40x40px)
3. Issuer/Ruler
4. Denomination
5. Metal badge
6. Year
7. Mint
8. Grade badge
9. Reference
10. Acquisition price
11. Actions

**Props**:
```typescript
interface CoinTableRowV3Props {
  coin: DomainCoin
  onRowClick?: (coinId: number) => void
  sortColumn?: string
}
```

### 2.3 CoinForm (Create/Edit)

**Location**: `frontend/src/components/coins/CoinForm.tsx`

**Purpose**: Multi-tab form for coin data entry.

**Form Tabs**:
1. **Identity**: category, denomination, metal
2. **Attribution**: issuer, mint, year_start, year_end
3. **Design**: obverse/reverse legends and descriptions
4. **Physical**: weight_g, diameter_mm, die_axis
5. **Grading**: service, grade, certification_number
6. **Collection**: acquisition price/source/date/url

**Key Features**:
- react-hook-form with Zod validation
- VocabAutocomplete for issuer/mint fields
- Image upload handling
- Year input supports BC (negative numbers)

**Props**:
```typescript
interface CoinFormProps {
  coin?: DomainCoin        // For edit mode
  onSubmit: (data: DomainCoin) => void
  isSubmitting?: boolean
}
```

**Usage**:
```typescript
import { CoinForm } from '@/components/coins/CoinForm'
import { useCreateCoin } from '@/hooks/useCoins'

function AddCoinPage() {
  const createCoin = useCreateCoin()
  
  return (
    <CoinForm
      onSubmit={(data) => {
        createCoin.mutate(data, {
          onSuccess: (coin) => navigate(`/coins/${coin.id}`)
        })
      }}
      isSubmitting={createCoin.isPending}
    />
  )
}
```

### 2.4 VocabAutocomplete

**Location**: `frontend/src/components/coins/VocabAutocomplete.tsx`

**Purpose**: Autocomplete for controlled vocabulary (issuer, mint).

**Props**:
```typescript
interface VocabAutocompleteProps {
  vocabType: 'issuer' | 'mint' | 'denomination'
  value: number | null       // vocab term ID
  onChange: (id: number | null) => void
  placeholder?: string
}
```

**Key Features**:
- Debounced search (300ms)
- Returns vocab term ID, not string
- Shows canonical_name in dropdown
- Allows creating new terms

---

## 3. Layout Components

### 3.1 AppShell

**Location**: `frontend/src/components/layout/AppShell.tsx`

**Purpose**: Main layout wrapper with sidebar, header, and content area.

**Structure**:
```typescript
<div className="flex h-screen">
  <Sidebar />           {/* Left navigation */}
  <div className="flex-1 flex flex-col">
    <Header />          {/* Top bar */}
    <main className="flex-1 overflow-auto">
      <Outlet />        {/* Route content */}
    </main>
    <BottomPanel />     {/* Collapsible charts */}
  </div>
</div>
```

### 3.2 CommandBar

**Location**: `frontend/src/components/layout/CommandBar/`

**Purpose**: Top action bar with primary actions.

**Components**:
- `index.tsx` - Main command bar
- `AddCoinSplitButton.tsx` - Add coin with dropdown
- `ScrapePopover.tsx` - Paste URL popover
- `CertLookupPopover.tsx` - NGC/PCGS lookup

**Key Actions**:
- Add Coin (split button: Manual, Import Excel, Bulk Normalize)
- Paste URL (scrape auction lot)
- Cert # (NGC/PCGS lookup)
- Search bar
- Theme toggle

### 3.3 CollectionDashboard

**Location**: `frontend/src/features/collection/CollectionDashboard/`

**Purpose**: Left sidebar with interactive dashboard widgets.

**Widgets** (in order):
1. Collection Health
2. Metal badges (clickable filters)
3. Grade spectrum
4. Ruler distribution
5. Category donut
6. Certification summary
7. Advanced filters

**Key Pattern**:
```typescript
// Widgets act as filters
const handleMetalClick = (metal: string) => {
  setFilter('metal', metal)
}

<MetalBadge
  metal="silver"
  count={stats.by_metal.silver}
  onClick={() => handleMetalClick('silver')}
  isActive={filters.metal === 'silver'}
/>
```

### 3.4 CollectionToolbar

**Location**: `frontend/src/features/collection/CollectionToolbar/`

**Purpose**: Top toolbar with active filters, sort, and view toggle.

**Features**:
- Active filter chips (removable)
- Sort control (field + direction)
- View toggle (grid/table)
- Compact view toggle
- Items per page

---

## 4. Dashboard Widgets

### 4.1 CategoryDonut

**Location**: `frontend/src/components/dashboard/CategoryDonut.tsx`

**Purpose**: Pie/donut chart showing category distribution.

**Key Features**:
- Uses Recharts PieChart
- Category colors from design tokens
- Click to filter by category
- Center shows total count

**Props**:
```typescript
interface CategoryDonutProps {
  data: Array<{ category: string; count: number }>
  onCategoryClick?: (category: string) => void
}
```

### 4.2 YearHistogram

**Location**: `frontend/src/components/dashboard/YearHistogram.tsx`

**Purpose**: Bar chart of coins by year with brush selection.

**Key Features**:
- Handles BC years (negative numbers)
- Brush selection for year range filter
- Updates mint_year_gte/mint_year_lte on selection

**Props**:
```typescript
interface YearHistogramProps {
  data: Array<{ year: number; count: number }>
  onRangeChange?: (start: number, end: number) => void
}
```

### 4.3 CollectionHealthWidget

**Location**: `frontend/src/components/dashboard/CollectionHealthWidget.tsx`

**Purpose**: Shows collection completeness metrics.

**Metrics**:
- Overall health score
- Fields completion (descriptions, images, references)
- Grading coverage
- Attribution quality

---

## 5. State Management

### 5.1 useUIStore (Zustand)

**Location**: `frontend/src/stores/uiStore.ts`

**Purpose**: UI state that persists across sessions.

**State**:
```typescript
interface UIState {
  sidebarOpen: boolean
  sidebarCollapsed: boolean
  viewMode: 'grid' | 'table'
  compactView: boolean
  commandPaletteOpen: boolean
  parseListingOpen: boolean
  screenSize: 'mobile' | 'tablet' | 'desktop'
  bottomPanelExpanded: boolean
  bottomPanelTab: 'timeline' | 'acquisitions' | 'geography'
}
```

**Usage**:
```typescript
import { useUIStore } from '@/stores/uiStore'

function CollectionPage() {
  const { viewMode, setViewMode, screenSize } = useUIStore()
  
  return (
    <div>
      <Button onClick={() => setViewMode('grid')}>Grid</Button>
      <Button onClick={() => setViewMode('table')}>Table</Button>
      
      {viewMode === 'grid' ? <CoinGrid /> : <CoinTable />}
    </div>
  )
}
```

### 5.2 useFilterStore (Zustand with Persistence)

**Location**: `frontend/src/stores/filterStore.ts`

**Purpose**: Filter, sort, and pagination state.

**State**:
```typescript
interface FilterState {
  // Filters
  category: string | null
  metal: string | null
  grade: string | null
  certification: string | null
  issuer: string | null
  mint: string | null
  mint_year_gte: number | null
  mint_year_lte: number | null
  priceRange: [number | null, number | null]
  search: string
  
  // Sorting
  sortBy: SortField
  sortDirection: 'asc' | 'desc'
  
  // Pagination
  page: number
  perPage: number
}

type SortField = 'value' | 'category' | 'metal' | 'year' | 'grade' | 'acquisition_date' | 'denomination'
```

**Key Actions**:
```typescript
setCategory: (category: string | null) => void
setMetal: (metal: string | null) => void
setMintYearGte: (year: number | null) => void
setMintYearLte: (year: number | null) => void
setSort: (field: SortField, direction: 'asc' | 'desc') => void
resetFilters: () => void
toQueryParams: () => Record<string, any>
```

**Usage**:
```typescript
import { useFilterStore } from '@/stores/filterStore'

function CoinFilters() {
  const { 
    category, 
    setCategory, 
    resetFilters,
    toQueryParams 
  } = useFilterStore()
  
  // Pass to API hook
  const { data } = useCoins(toQueryParams())
  
  return (
    <Select value={category} onChange={setCategory}>
      <option value="">All Categories</option>
      <option value="imperial">Imperial</option>
      {/* ... */}
    </Select>
  )
}
```

---

## 6. API Hooks (TanStack Query v5)

### 6.1 useCoins

**Location**: `frontend/src/hooks/useCoins.ts`

**Purpose**: Fetch coins with filters and pagination.

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { v2 } from '@/api/v2'

// List coins
export function useCoins(params?: Record<string, any>) {
  return useQuery({
    queryKey: ['coins', params],
    queryFn: () => v2.getCoins(params),
    staleTime: 5 * 60 * 1000,  // 5 minutes
  })
}

// Get single coin
export function useCoin(id: number) {
  return useQuery({
    queryKey: ['coin', id],
    queryFn: () => v2.getCoin(id),
    enabled: !!id,
  })
}

// Create coin
export function useCreateCoin() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: v2.createCoin,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coins'] })
    },
  })
}

// Update coin
export function useUpdateCoin() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }) => v2.updateCoin(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['coins'] })
      queryClient.invalidateQueries({ queryKey: ['coin', id] })
    },
  })
}

// Delete coin
export function useDeleteCoin() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: v2.deleteCoin,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coins'] })
    },
  })
}
```

### 6.2 useCollectionStats

**Purpose**: Fetch collection statistics for dashboard.

```typescript
export function useCollectionStats() {
  return useQuery({
    queryKey: ['collection-stats'],
    queryFn: v2.getCollectionStats,
    staleTime: 60 * 1000,  // 1 minute
  })
}
```

**Response Shape**:
```typescript
interface CollectionStats {
  total_coins: number
  total_value: number
  by_category: Record<string, number>
  by_metal: Record<string, number>
  by_grade: Record<string, number>
  by_certification: Record<string, number>
  by_ruler: Array<{ ruler: string; count: number }>
  year_distribution: Array<{ year: number; count: number }>
  health_metrics: {
    overall: number
    with_images: number
    with_references: number
    with_descriptions: number
  }
}
```

---

## 7. Domain Types (Zod Schemas)

**Location**: `frontend/src/domain/schemas.ts`

### Key Schemas

```typescript
import { z } from 'zod'

// Value Objects
export const DimensionsSchema = z.object({
  weight_g: z.number().nullable().optional(),
  diameter_mm: z.number().nullable().optional(),
  die_axis: z.number().nullable().optional(),
})

export const AttributionSchema = z.object({
  issuer: z.string().nullable().optional(),
  issuer_id: z.number().nullable().optional(),
  mint: z.string().nullable().optional(),
  mint_id: z.number().nullable().optional(),
  year_start: z.number().nullable().optional(),
  year_end: z.number().nullable().optional(),
})

export const GradingSchema = z.object({
  grade: z.string().nullable().optional(),
  service: z.string().nullable().optional(),
  certification_number: z.string().nullable().optional(),
})

export const AcquisitionSchema = z.object({
  price: z.number().nullable().optional(),
  currency: z.string().nullable().optional(),
  source: z.string().nullable().optional(),
  date: z.string().nullable().optional(),
  url: z.string().nullable().optional(),
})

export const DesignSchema = z.object({
  obverse_legend: z.string().nullable().optional(),
  obverse_description: z.string().nullable().optional(),
  reverse_legend: z.string().nullable().optional(),
  reverse_description: z.string().nullable().optional(),
})

// Main Coin Schema
export const DomainCoinSchema = z.object({
  id: z.number().nullable(),
  category: z.string(),
  metal: z.string().nullable().optional(),
  denomination: z.string().nullable().optional(),
  rarity: z.string().nullable().optional(),
  
  // Nested value objects
  dimensions: DimensionsSchema.optional().default({}),
  attribution: AttributionSchema.optional().default({}),
  grading: GradingSchema.optional().default({}),
  acquisition: AcquisitionSchema.nullable().optional(),
  design: DesignSchema.optional().default({}),
  
  // Relations
  images: z.array(ImageSchema).optional().default([]),
  references: z.array(ReferenceSchema).optional(),
})

export type DomainCoin = z.infer<typeof DomainCoinSchema>
```

---

## 8. Common Patterns

### 8.1 Filter Chip Colors

```typescript
function getFilterChipColor(field: string, value: string) {
  if (field === 'category') {
    return {
      bg: `var(--cat-${value.toLowerCase().replace('_', '-')})`,
      text: '#fff'
    }
  }
  if (field === 'metal') {
    return {
      bg: `var(--metal-${value.toLowerCase()})`,
      text: value === 'gold' ? '#000' : '#fff'
    }
  }
  // ... handle grade, certification
  return { bg: 'var(--bg-elevated)', text: 'var(--text-primary)' }
}
```

### 8.2 Year Display (BC/AD)

```typescript
function formatYear(year: number | null): string {
  if (year === null) return '—'
  if (year < 0) return `${Math.abs(year)} BC`
  return `AD ${year}`
}

function formatYearRange(start: number | null, end: number | null): string {
  if (!start && !end) return '—'
  if (start === end) return formatYear(start)
  return `${formatYear(start)} – ${formatYear(end)}`
}
```

### 8.3 Price Formatting

```typescript
function formatPrice(price: number | null, currency = 'USD'): string {
  if (price === null) return '—'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(price)
}
```

### 8.4 Grade Color Helper

```typescript
function getGradeColor(grade: string): string {
  const normalized = grade.toUpperCase()
  
  if (['P', 'FR', 'AG', 'POOR', 'FAIR'].some(g => normalized.includes(g))) {
    return 'var(--grade-poor)'
  }
  if (['G', 'VG', 'GOOD'].some(g => normalized.includes(g))) {
    return 'var(--grade-good)'
  }
  if (['F', 'FINE'].some(g => normalized === g)) {
    return 'var(--grade-fine)'
  }
  if (['VF', 'VERY FINE'].some(g => normalized.includes(g))) {
    return 'var(--grade-vf)'
  }
  if (['EF', 'XF', 'EXTREMELY FINE'].some(g => normalized.includes(g))) {
    return 'var(--grade-ef)'
  }
  if (['AU', 'ABOUT UNC'].some(g => normalized.includes(g))) {
    return 'var(--grade-au)'
  }
  if (['MS', 'MINT STATE', 'FDC'].some(g => normalized.includes(g))) {
    return 'var(--grade-ms)'
  }
  
  return 'var(--text-muted)'
}
```

---

## 9. Testing Patterns

### Component Test

```typescript
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CoinCardV3 } from '@/components/coins/CoinCardV3'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } }
})

const wrapper = ({ children }) => (
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
)

describe('CoinCardV3', () => {
  it('renders coin information', () => {
    const coin = {
      id: 1,
      category: 'imperial',
      metal: 'silver',
      attribution: { issuer: 'Augustus' },
      grading: { grade: 'VF' },
      dimensions: {},
      design: {},
      images: [],
    }

    render(<CoinCardV3 coin={coin} />, { wrapper })

    expect(screen.getByText('Augustus')).toBeInTheDocument()
    expect(screen.getByText('VF')).toBeInTheDocument()
  })
})
```

### Hook Test

```typescript
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useCoins } from '@/hooks/useCoins'

describe('useCoins', () => {
  it('fetches coins', async () => {
    const { result } = renderHook(() => useCoins(), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.items).toBeDefined()
  })
})
```

---

## 10. AI Implementation Checklist

Before submitting frontend changes:

### Imports
- [ ] Using `@/` alias (not relative paths)
- [ ] Design tokens from `index.css`
- [ ] TanStack Query v5 syntax

### Components
- [ ] Following design system (see 10-DESIGN-SYSTEM.md)
- [ ] Responsive layout (mobile/tablet/desktop)
- [ ] Using Zustand stores for state
- [ ] Error handling for API calls

### Types
- [ ] Using Zod schemas (not plain interfaces)
- [ ] Proper null handling
- [ ] Type-safe props

### Performance
- [ ] Using `useMemo`/`useCallback` where needed
- [ ] Keys on list items
- [ ] Lazy loading for large components

---

**Previous**: [10-DESIGN-SYSTEM.md](10-DESIGN-SYSTEM.md) - Design tokens
**Next**: [06-FILE-LOCATIONS.md](06-FILE-LOCATIONS.md) - File reference
**Related**: [04-FRONTEND-MODULES.md](04-FRONTEND-MODULES.md) - Architecture overview
