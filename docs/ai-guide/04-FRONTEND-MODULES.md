# Frontend Modules Reference (V2)

> This document describes the frontend architecture, component patterns, state management, and API integration for CoinStack V2.
>
> **Related Guides**:
> - [10-DESIGN-SYSTEM.md](10-DESIGN-SYSTEM.md) - Design tokens, colors, component specs (v3.1)
> - [11-FRONTEND-COMPONENTS.md](11-FRONTEND-COMPONENTS.md) - Detailed component reference

---

## Table of Contents

1. [Directory Structure](#directory-structure)
2. [Core Application Files](#core-application-files)
3. [Pages](#pages-srcpages)
4. [Components](#components-srccomponents)
5. [API Integration](#api-integration-srcapi)
6. [Hooks](#hooks-srchooks)
7. [State Management](#state-management-srcstores)
8. [Domain Types](#domain-types-srcdomain)
9. [Utilities](#utilities-srclib)

---

## Directory Structure

```
frontend/src/
├── main.tsx             # Entry point
├── App.tsx              # Root component, routing
├── index.css            # Global styles, design tokens
├── vite-env.d.ts        # Vite type declarations
│
├── pages/               # Route pages
├── components/          # React components
│   ├── ui/              # shadcn/ui base components
│   ├── layout/          # App shell components
│   ├── coins/           # Coin-specific components
│   └── design-system/   # Domain-specific components
│
├── api/                 # API client (V2 endpoints)
├── hooks/               # TanStack Query hooks
├── stores/              # Zustand stores
├── domain/              # Zod schemas mirroring backend
└── lib/                 # Utilities
```

**Import Path Alias**: All imports use `@/` prefix (e.g., `@/api/v2`, `@/domain/schemas`, `@/components/ui/button`)

---

## Core Application Files

### `main.tsx`

Application entry point with React 18 concurrent rendering.

```typescript
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'

createRoot(document.getElementById('root')!).render(<App />)
```

### `App.tsx`

Root component with providers and routing.

**Providers**:
- `QueryClientProvider` - TanStack Query v5 for server state
- `BrowserRouter` - React Router v6 for routing
- `Toaster` - sonner for notifications

**Query Client Configuration**:
```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})
```

**Routes** (React Router v6):
```typescript
<Routes>
  <Route element={<AppShell />}>
    <Route path="/" element={<CollectionPage />} />
    <Route path="/coins/new" element={<AddCoinPage />} />
    <Route path="/coins/:id" element={<CoinDetailPage />} />
    <Route path="/coins/:id/edit" element={<EditCoinPage />} />
    <Route path="/series" element={<SeriesDashboard />} />
    <Route path="/series/:id" element={<SeriesDetailPage />} />
    <Route path="/series/new" element={<CreateSeriesPage />} />
    <Route path="/stats" element={<StatsPageV3 />} />
    <Route path="/settings" element={<SettingsPage />} />
  </Route>
</Routes>
```

### `index.css`

Global styles with CSS custom properties for design tokens.

> **Complete Design Tokens**: See [10-DESIGN-SYSTEM.md](10-DESIGN-SYSTEM.md) for full token reference.

**Key Token Categories**:
```css
:root {
  /* Backgrounds (Navy-charcoal theme) */
  --bg-app: #050814;
  --bg-elevated: #0B1020;
  --bg-card: #0F1526;
  --bg-hover: #1A1F35;

  /* Text hierarchy */
  --text-primary: #F5F5F7;
  --text-secondary: #D1D5DB;
  --text-muted: #9CA3AF;
  --text-ghost: #6B7280;

  /* Categories (Historical colors) */
  --cat-republic: #DC2626;
  --cat-imperial: #7C3AED;
  --cat-provincial: #2563EB;
  --cat-greek: #16A34A;

  /* Metals */
  --metal-au: #FFD700;
  --metal-ag: #C0C0C0;
  --metal-ae: #8B7355;

  /* Grades (Temperature scale) */
  --grade-poor: #3B82F6;
  --grade-vf: #F59E0B;
  --grade-ms: #DC2626;

  /* Certifications */
  --cert-ngc: #1A73E8;
  --cert-pcgs: #2E7D32;

  /* Rarity (Gemstone scale) */
  --rarity-common: #D1D5DB;
  --rarity-r1: #06B6D4;
  --rarity-unique: #EF4444;
}
```

---

## Pages (`src/pages/`)

### `CollectionPage.tsx`

Main collection view with grid/table toggle.

**Features**:
- Grid view (CoinCardV3) / Table view (CoinTableRowV3)
- Filter panel with all filter options
- Pagination controls
- Quick actions (add, import)
- Column customization (table view)

**Key Hooks**:
```typescript
import { useCoins } from '@/hooks/useCoins'
import { useFilterStore } from '@/stores/filterStore'
import { useUIStore } from '@/stores/uiStore'

function CollectionPage() {
  const { viewMode } = useUIStore()
  const filters = useFilterStore(state => state.toParams())
  const { data, isLoading } = useCoins(filters)

  // Render grid or table based on viewMode
}
```

### `CoinDetailPage.tsx`

Individual coin detail view.

**Features**:
- Image gallery with zoom
- All coin fields organized in sections (Classification, Attribution, Design, Physical, Grading, Acquisition)
- Edit/Delete actions
- Linked auction data
- Series membership display

**Key Hooks**:
```typescript
import { useCoin } from '@/hooks/useCoins'
import { useParams } from 'react-router-dom'

function CoinDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: coin, isLoading } = useCoin(Number(id))

  // Display nested value objects
  // coin.dimensions, coin.attribution, coin.grading, coin.acquisition
}
```

### `AddCoinPage.tsx` / `EditCoinPage.tsx`

Coin form for create/edit.

**Features**:
- Multi-tab form (Identity, Attribution, Design, Physical, Grading, Collection)
- Vocabulary autocomplete for issuer/mint
- Image upload
- Validation with Zod

**Key Hooks**:
```typescript
import { useCreateCoin, useUpdateCoin } from '@/hooks/useCoins'
import { CoinSchema } from '@/domain/schemas'

function AddCoinPage() {
  const createCoin = useCreateCoin()

  const onSubmit = (data: Coin) => {
    createCoin.mutate(data, {
      onSuccess: (coin) => {
        // Navigate to detail page
        navigate(`/coins/${coin.id}`)
      }
    })
  }
}
```

### `SeriesDashboard.tsx`

Series management dashboard.

**Features**:
- List all series with completion status
- Create new series button
- Series type filters (ruler, type, catalog, custom)
- Completion statistics

**Key Hooks**:
```typescript
import { useSeries } from '@/hooks/useSeries'

function SeriesDashboard() {
  const { data: seriesList, isLoading } = useSeries()

  // Display series cards with progress
}
```

### `SeriesDetailPage.tsx`

Individual series with slot management.

**Features**:
- Series metadata display
- Slot grid with filled/empty status
- Add coin to slot functionality
- Completion tracking

**Key Hooks**:
```typescript
import { useSeriesDetail, useAddCoinToSeries } from '@/hooks/useSeries'

function SeriesDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: series } = useSeriesDetail(Number(id))
  const addCoin = useAddCoinToSeries()

  const handleAddCoin = (coinId: number, slotId: number) => {
    addCoin.mutate({ seriesId: Number(id), coinId, slotId })
  }
}
```

### `StatsPageV3.tsx`

Collection statistics dashboard.

**Features**:
- Total collection value
- Distribution charts (category, metal, issuer)
- Timeline coverage
- Recent acquisitions

**Key Hooks**:
```typescript
import { useCoins } from '@/hooks/useCoins'

function StatsPageV3() {
  const { data } = useCoins({})

  // Compute statistics from coin data
  // Charts with recharts library
}
```

### `SettingsPage.tsx`

Application settings.

**Features**:
- Database info
- Backup/restore
- CSV export
- Clear cache

---

## Components (`src/components/`)

### Layout Components (`layout/`)

#### `AppShell.tsx`

Main layout wrapper with nested routing.

```typescript
import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { Sidebar } from './Sidebar'

function AppShell() {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 overflow-auto">
          <Outlet /> {/* Route content */}
        </main>
      </div>
    </div>
  )
}
```

#### `Header.tsx`

Top navigation bar.

**Features**:
- Global search input
- Add coin button
- Theme toggle
- Command palette trigger (Cmd+K)

```typescript
import { Button } from '@/components/ui/button'
import { useUIStore } from '@/stores/uiStore'

function Header() {
  const { setCommandPaletteOpen } = useUIStore()

  return (
    <header className="border-b">
      <Button onClick={() => setCommandPaletteOpen(true)}>
        Search (⌘K)
      </Button>
    </header>
  )
}
```

#### `Sidebar.tsx`

Left navigation sidebar.

**Navigation Items**:
- Collection (home)
- Series
- Statistics
- Settings

**Features**:
- Collapsible
- Active state indication
- Icons from lucide-react

```typescript
import { NavLink } from 'react-router-dom'
import { Home, Grid3x3, BarChart3, Settings } from 'lucide-react'

function Sidebar() {
  return (
    <aside className="w-64 border-r">
      <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>
        <Home /> Collection
      </NavLink>
      <NavLink to="/series">
        <Grid3x3 /> Series
      </NavLink>
    </aside>
  )
}
```

### Coin Components (`coins/`)

#### `CoinCardV3.tsx`

Grid view card for a coin (V3 design system).

```typescript
import { Coin } from '@/domain/schemas'
import { MetalBadge } from '@/components/design-system/MetalBadge'

interface CoinCardV3Props {
  coin: Coin
  onClick?: () => void
}

function CoinCardV3({ coin, onClick }: CoinCardV3Props) {
  return (
    <div className="coin-card" onClick={onClick}>
      {coin.images[0] && (
        <img src={coin.images[0].url} alt={coin.attribution.issuer || ''} />
      )}
      <div className="coin-card-content">
        <h3>{coin.attribution.issuer}</h3>
        <p>{coin.denomination}</p>
        <MetalBadge metal={coin.metal} />
        <p>{coin.grading.grade}</p>
      </div>
    </div>
  )
}
```

**Displays**:
- Primary image thumbnail
- Issuer (from `coin.attribution.issuer`)
- Denomination
- Metal badge
- Grade badge
- Acquisition price

#### `CoinTableRowV3.tsx`

Table row for coin (V3 design system).

```typescript
interface CoinTableRowV3Props {
  coin: Coin
  onRowClick?: (id: number) => void
}

function CoinTableRowV3({ coin, onRowClick }: CoinTableRowV3Props) {
  return (
    <tr onClick={() => onRowClick?.(coin.id!)}>
      <td>{coin.images[0]?.url && <img src={coin.images[0].url} />}</td>
      <td>{coin.category}</td>
      <td>{coin.metal}</td>
      <td>{coin.denomination}</td>
      <td>{coin.attribution.issuer}</td>
      <td>{coin.grading.grade}</td>
      <td>{coin.acquisition?.price}</td>
    </tr>
  )
}
```

#### `CoinForm.tsx`

Multi-tab form for coin data.

**Form Structure**:
```typescript
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { CoinSchema, Coin } from '@/domain/schemas'

interface CoinFormProps {
  coin?: Coin  // For edit mode
  onSubmit: (data: Coin) => void
  isLoading?: boolean
}

function CoinForm({ coin, onSubmit, isLoading }: CoinFormProps) {
  const form = useForm<Coin>({
    resolver: zodResolver(CoinSchema),
    defaultValues: coin || {
      dimensions: {},
      attribution: {},
      grading: {},
      acquisition: {},
    }
  })

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <Tabs>
        <TabsList>
          <TabsTrigger value="identity">Identity</TabsTrigger>
          <TabsTrigger value="attribution">Attribution</TabsTrigger>
          <TabsTrigger value="design">Design</TabsTrigger>
          <TabsTrigger value="physical">Physical</TabsTrigger>
          <TabsTrigger value="grading">Grading</TabsTrigger>
          <TabsTrigger value="collection">Collection</TabsTrigger>
        </TabsList>

        <TabsContent value="identity">
          {/* category, denomination, metal */}
        </TabsContent>

        <TabsContent value="attribution">
          {/* issuer, mint, year_start, year_end */}
          {/* Uses VocabAutocomplete for issuer/mint */}
        </TabsContent>

        {/* Other tabs... */}
      </Tabs>
    </form>
  )
}
```

**Tabs**:
1. **Identity** - category, denomination, metal
2. **Attribution** - issuer, mint, year_start, year_end
3. **Design** - obverse/reverse legends and descriptions
4. **Physical** - weight_g, diameter_mm, die_axis
5. **Grading** - service, grade, certification_number
6. **Collection** - acquisition price/source/date/url

#### `VocabAutocomplete.tsx`

Autocomplete for controlled vocabulary (issuer, mint, denomination).

```typescript
import { useState } from 'react'
import { v2 } from '@/api/v2'

interface VocabAutocompleteProps {
  vocabType: 'issuer' | 'mint' | 'denomination'
  value: string
  onChange: (value: string) => void
}

function VocabAutocomplete({ vocabType, value, onChange }: VocabAutocompleteProps) {
  const [suggestions, setSuggestions] = useState<string[]>([])

  const handleSearch = async (query: string) => {
    const results = await v2.searchVocab(vocabType, query)
    setSuggestions(results.map(r => r.canonical_name))
  }

  return (
    <Combobox
      value={value}
      onChange={onChange}
      onInputChange={handleSearch}
      options={suggestions}
    />
  )
}
```

#### `CoinFilters.tsx`

Filter panel for collection view.

**Filter Options**:
```typescript
import { useFilterStore } from '@/stores/filterStore'

function CoinFilters() {
  const {
    category,
    metal,
    setFilter
  } = useFilterStore()

  return (
    <div className="filters">
      <Select value={category} onChange={(v) => setFilter('category', v)}>
        <option value="">All Categories</option>
        <option value="greek">Greek</option>
        <option value="roman_imperial">Roman Imperial</option>
        <option value="roman_republic">Roman Republic</option>
      </Select>

      <Select value={metal} onChange={(v) => setFilter('metal', v)}>
        <option value="">All Metals</option>
        <option value="gold">Gold</option>
        <option value="silver">Silver</option>
        <option value="bronze">Bronze</option>
      </Select>

      {/* Price range, year range, text search */}
    </div>
  )
}
```

**Available Filters**:
- Category (select)
- Metal (select)
- Grade range (slider)
- Price range (min/max inputs)
- Year range (min/max inputs with BC/AD support)
- Issuer (text search with autocomplete)
- Mint (text search with autocomplete)
- Full-text search

### Design System Components (`design-system/`)

#### `MetalBadge.tsx`

Badge showing coin metal with color coding.

```typescript
import { Metal } from '@/domain/schemas'

interface MetalBadgeProps {
  metal?: Metal
  size?: 'sm' | 'md' | 'lg'
}

function MetalBadge({ metal, size = 'md' }: MetalBadgeProps) {
  if (!metal) return null

  const colorClass = {
    gold: 'bg-yellow-500',
    silver: 'bg-gray-300',
    bronze: 'bg-amber-700',
    copper: 'bg-orange-600',
  }[metal]

  return (
    <span className={`badge ${colorClass} ${size}`}>
      {metal.toUpperCase()}
    </span>
  )
}
```

#### `GradeBadge.tsx`

Badge showing coin grade with service logo.

```typescript
import { GradeService } from '@/domain/schemas'

interface GradeBadgeProps {
  grade?: string
  service?: GradeService
}

function GradeBadge({ grade, service }: GradeBadgeProps) {
  if (!grade) return null

  return (
    <div className="grade-badge">
      {service && <img src={`/logos/${service}.png`} alt={service} />}
      <span>{grade}</span>
    </div>
  )
}
```

### UI Components (`ui/`)

shadcn/ui components - use as provided, customize via CSS variables in `index.css`.

**Key Components**:
- `Button` - Primary actions
- `Card`, `CardHeader`, `CardContent` - Content containers
- `Dialog`, `DialogContent`, `DialogTrigger` - Modal dialogs
- `Select`, `SelectTrigger`, `SelectContent` - Dropdown selection
- `Input` - Text inputs
- `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableCell` - Data tables
- `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` - Tab navigation
- `Badge` - Status indicators
- `Tooltip` - Hover hints
- `Skeleton` - Loading states
- `Combobox` - Autocomplete inputs

---

## API Integration (`src/api/`)

### API Client Pattern

**File**: `src/api/v2.ts`

Centralized API client with Zod schema validation.

```typescript
import api from './api'  // Axios instance
import { Coin, CoinSchema, SeriesSchema } from '@/domain/schemas'
import { z } from 'zod'

const PaginatedCoinsSchema = z.object({
  items: z.array(CoinSchema),
  total: z.number(),
  page: z.number(),
  per_page: z.number(),
  pages: z.number()
})

export type PaginatedCoinsResponse = z.infer<typeof PaginatedCoinsSchema>

export const v2 = {
  // Coins API (/api/v2/coins)
  getCoins: async (params?: Record<string, any>): Promise<PaginatedCoinsResponse> => {
    const response = await api.get('/api/v2/coins', { params })
    return PaginatedCoinsSchema.parse(response.data)
  },

  getCoin: async (id: number): Promise<Coin> => {
    const response = await api.get(`/api/v2/coins/${id}`)
    return CoinSchema.parse(response.data)
  },

  createCoin: async (coin: Omit<Coin, 'id'>): Promise<Coin> => {
    const payload = mapCoinToPayload(coin)  // Flatten nested objects
    const response = await api.post('/api/v2/coins', payload)
    return CoinSchema.parse(response.data)
  },

  updateCoin: async (id: number, coin: Omit<Coin, 'id'>): Promise<Coin> => {
    const payload = mapCoinToPayload(coin)
    const response = await api.put(`/api/v2/coins/${id}`, payload)
    return CoinSchema.parse(response.data)
  },

  deleteCoin: async (id: number): Promise<void> => {
    await api.delete(`/api/v2/coins/${id}`)
  },

  // Series API (/api/series - NOTE: no /v2 prefix yet)
  getSeries: async (): Promise<SeriesListResponse> => {
    const response = await api.get('/api/series')
    return SeriesListSchema.parse(response.data)
  },

  getSeriesDetail: async (id: number): Promise<Series> => {
    const response = await api.get(`/api/series/${id}`)
    return SeriesSchema.parse(response.data)
  },

  createSeries: async (data: any): Promise<Series> => {
    const response = await api.post('/api/series', data)
    return SeriesSchema.parse(response.data)
  },

  addCoinToSeries: async (
    seriesId: number,
    coinId: number,
    slotId?: number
  ): Promise<any> => {
    const response = await api.post(
      `/api/series/${seriesId}/coins/${coinId}`,
      null,
      { params: { slot_id: slotId } }
    )
    return response.data
  },

  // Audit API (/api/v2/audit)
  auditCoin: async (id: number): Promise<AuditResult> => {
    const response = await api.get(`/api/v2/audit/${id}`)
    return AuditResultSchema.parse(response.data)
  },

  applyEnrichment: async (id: number, field: string, value: string): Promise<void> => {
    await api.post(`/api/v2/audit/${id}/apply`, { field, value })
  },

  // Scraper API (/api/v2/scrape)
  scrapeLot: async (url: string): Promise<ScrapeResult> => {
    const response = await api.post('/api/v2/scrape/lot', { url })
    return ScrapeResultSchema.parse(response.data)
  },

  // Vocabulary API (/api/v2/vocab)
  searchVocab: async (
    vocabType: string,
    query: string
  ): Promise<VocabTerm[]> => {
    const response = await api.get(`/api/v2/vocab/search/${vocabType}`, {
      params: { q: query }
    })
    return response.data
  },
}
```

**Helper Function** (flattens nested domain objects for API):
```typescript
function mapCoinToPayload(coin: Omit<Coin, 'id'>) {
  return {
    // Classification
    category: coin.category,
    metal: coin.metal,
    denomination: coin.denomination,

    // Dimensions (flatten value object)
    weight_g: coin.dimensions.weight_g,
    diameter_mm: coin.dimensions.diameter_mm,
    die_axis: coin.dimensions.die_axis,

    // Attribution (flatten value object)
    issuer: coin.attribution.issuer,
    issuer_id: coin.attribution.issuer_id,
    mint: coin.attribution.mint,
    mint_id: coin.attribution.mint_id,
    year_start: coin.attribution.year_start,
    year_end: coin.attribution.year_end,

    // Grading (flatten value object)
    grading_state: coin.grading.grading_state,
    grade: coin.grading.grade,
    grade_service: coin.grading.service,
    certification: coin.grading.certification_number,
    strike: coin.grading.strike,
    surface: coin.grading.surface,

    // Acquisition (flatten value object)
    acquisition_price: coin.acquisition?.price,
    acquisition_source: coin.acquisition?.source,
    acquisition_date: coin.acquisition?.date,
    acquisition_url: coin.acquisition?.url,

    // Design
    obverse_legend: coin.obverse_legend,
    obverse_description: coin.obverse_description,
    reverse_legend: coin.reverse_legend,
    reverse_description: coin.reverse_description,
  }
}
```

### Base Axios Instance

**File**: `src/api/api.ts`

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Show toast notification on error
    toast.error(error.response?.data?.detail || 'An error occurred')
    throw error
  }
)

export default api
```

**Environment Variables**:
- `VITE_API_URL` - Defaults to `/api` (proxied to backend in dev)
- Vite dev server proxies `/api` → `http://localhost:8000`

---

## Hooks (`src/hooks/`)

### TanStack Query Hooks (V5 Syntax)

All hooks use TanStack Query v5 with object-based configuration.

#### `useCoins.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { v2 } from '@/api/v2'
import type { Coin, PaginatedCoinsResponse } from '@/api/v2'

// List coins with filters
export function useCoins(filters?: Record<string, any>) {
  return useQuery({
    queryKey: ['coins', filters],
    queryFn: () => v2.getCoins(filters),
  })
}

// Get single coin
export function useCoin(id: number) {
  return useQuery({
    queryKey: ['coin', id],
    queryFn: () => v2.getCoin(id),
    enabled: !!id,  // Only run if id is truthy
  })
}

// Create coin
export function useCreateCoin() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: Omit<Coin, 'id'>) => v2.createCoin(data),
    onSuccess: () => {
      // Invalidate coins list to refetch
      queryClient.invalidateQueries({ queryKey: ['coins'] })
    },
  })
}

// Update coin
export function useUpdateCoin() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Omit<Coin, 'id'> }) =>
      v2.updateCoin(id, data),
    onSuccess: (_, { id }) => {
      // Invalidate both list and detail
      queryClient.invalidateQueries({ queryKey: ['coins'] })
      queryClient.invalidateQueries({ queryKey: ['coin', id] })
    },
  })
}

// Delete coin
export function useDeleteCoin() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => v2.deleteCoin(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coins'] })
    },
  })
}
```

**Usage in Components**:
```typescript
function CoinDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: coin, isLoading, error } = useCoin(Number(id))
  const updateCoin = useUpdateCoin()
  const deleteCoin = useDeleteCoin()

  const handleUpdate = (data: Omit<Coin, 'id'>) => {
    updateCoin.mutate({ id: Number(id), data }, {
      onSuccess: () => toast.success('Coin updated')
    })
  }

  const handleDelete = () => {
    deleteCoin.mutate(Number(id), {
      onSuccess: () => navigate('/')
    })
  }

  if (isLoading) return <Skeleton />
  if (error) return <ErrorMessage error={error} />
  if (!coin) return <NotFound />

  return <CoinDetail coin={coin} onUpdate={handleUpdate} onDelete={handleDelete} />
}
```

#### `useSeries.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { v2 } from '@/api/v2'
import type { Series } from '@/domain/schemas'

export function useSeries() {
  return useQuery({
    queryKey: ['series'],
    queryFn: v2.getSeries,
  })
}

export function useSeriesDetail(id: number) {
  return useQuery({
    queryKey: ['series', id],
    queryFn: () => v2.getSeriesDetail(id),
    enabled: !!id,
  })
}

export function useCreateSeries() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: v2.createSeries,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['series'] })
    },
  })
}

export function useAddCoinToSeries() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      seriesId,
      coinId,
      slotId
    }: {
      seriesId: number
      coinId: number
      slotId?: number
    }) => v2.addCoinToSeries(seriesId, coinId, slotId),
    onSuccess: (_, { seriesId }) => {
      // Invalidate series detail to show updated slots
      queryClient.invalidateQueries({ queryKey: ['series', seriesId] })
    },
  })
}
```

### Utility Hooks

#### `useDebounce.ts`

```typescript
import { useEffect, useState } from 'react'

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])

  return debouncedValue
}
```

**Usage**:
```typescript
function CoinFilters() {
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebounce(search, 300)  // 300ms delay

  // Use debouncedSearch in API calls
  const { data } = useCoins({ search: debouncedSearch })
}
```

---

## State Management (`src/stores/`)

### Zustand Stores

Client-side UI state management with Zustand.

#### `uiStore.ts`

UI state (sidebar, view mode, dialogs).

```typescript
import { create } from 'zustand'

interface UIState {
  sidebarOpen: boolean
  viewMode: 'grid' | 'table'
  commandPaletteOpen: boolean
  parseListingOpen: boolean
  screenSize: 'mobile' | 'tablet' | 'desktop'

  toggleSidebar: () => void
  setViewMode: (mode: 'grid' | 'table') => void
  setCommandPaletteOpen: (open: boolean) => void
  setParseListingOpen: (open: boolean) => void
  setScreenSize: (size: 'mobile' | 'tablet' | 'desktop') => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  viewMode: 'grid',
  commandPaletteOpen: false,
  parseListingOpen: false,
  screenSize: 'desktop',

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setViewMode: (viewMode) => set({ viewMode }),
  setCommandPaletteOpen: (commandPaletteOpen) => set({ commandPaletteOpen }),
  setParseListingOpen: (parseListingOpen) => set({ parseListingOpen }),
  setScreenSize: (screenSize) => set({ screenSize }),
}))
```

**Usage**:
```typescript
function CollectionPage() {
  const { viewMode, setViewMode } = useUIStore()

  return (
    <div>
      <Button onClick={() => setViewMode('grid')}>Grid</Button>
      <Button onClick={() => setViewMode('table')}>Table</Button>

      {viewMode === 'grid' ? <CoinGrid /> : <CoinTable />}
    </div>
  )
}
```

#### `filterStore.ts` (with persistence)

Filter and pagination state with localStorage persistence.

```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface FilterState {
  // Filters
  category: string | null
  metal: string | null
  gradeMin: string | null
  gradeMax: string | null
  priceMin: number | null
  priceMax: number | null
  yearStart: number | null
  yearEnd: number | null
  issuer: string | null
  mint: string | null
  search: string

  // Sorting
  sortBy: string
  sortDir: 'asc' | 'desc'

  // Pagination
  page: number
  perPage: number  // 20, 50, 100

  // Actions
  setFilter: (key: string, value: any) => void
  setSort: (field: string, dir?: 'asc' | 'desc') => void
  setPage: (page: number) => void
  setPerPage: (perPage: number) => void
  reset: () => void

  // Helpers
  toParams: () => Record<string, any>
  getActiveFilterCount: () => number
}

const initialState = {
  category: null,
  metal: null,
  gradeMin: null,
  gradeMax: null,
  priceMin: null,
  priceMax: null,
  yearStart: null,
  yearEnd: null,
  issuer: null,
  mint: null,
  search: '',
  sortBy: 'acquisition_date',
  sortDir: 'desc' as const,
  page: 0,
  perPage: 50,
}

export const useFilterStore = create<FilterState>()(
  persist(
    (set, get) => ({
      ...initialState,

      setFilter: (key, value) => set({ [key]: value, page: 0 }),

      setSort: (field, dir) => set((state) => ({
        sortBy: field,
        sortDir: dir || (state.sortBy === field && state.sortDir === 'asc' ? 'desc' : 'asc'),
        page: 0,
      })),

      setPage: (page) => set({ page }),

      setPerPage: (perPage) => set({ perPage, page: 0 }),

      reset: () => set(initialState),

      toParams: () => {
        const state = get()
        const params: Record<string, any> = {
          skip: state.page * state.perPage,
          limit: state.perPage,
        }

        if (state.category) params.category = state.category
        if (state.metal) params.metal = state.metal
        if (state.issuer) params.issuer = state.issuer
        if (state.mint) params.mint = state.mint
        if (state.priceMin !== null) params.price_min = state.priceMin
        if (state.priceMax !== null) params.price_max = state.priceMax
        if (state.yearStart !== null) params.year_start = state.yearStart
        if (state.yearEnd !== null) params.year_end = state.yearEnd
        if (state.search) params.search = state.search

        params.sort_by = state.sortBy
        params.sort_dir = state.sortDir

        return params
      },

      getActiveFilterCount: () => {
        const state = get()
        let count = 0
        if (state.category) count++
        if (state.metal) count++
        if (state.issuer) count++
        if (state.mint) count++
        if (state.priceMin !== null || state.priceMax !== null) count++
        if (state.yearStart !== null || state.yearEnd !== null) count++
        if (state.search) count++
        return count
      },
    }),
    {
      name: 'coinstack-filters',  // localStorage key
      partialize: (state) => ({
        // Only persist filters, not pagination
        category: state.category,
        metal: state.metal,
        sortBy: state.sortBy,
        sortDir: state.sortDir,
        perPage: state.perPage,
      }),
    }
  )
)
```

**Usage**:
```typescript
function CollectionPage() {
  const filters = useFilterStore(state => state.toParams())
  const setFilter = useFilterStore(state => state.setFilter)
  const reset = useFilterStore(state => state.reset)

  const { data } = useCoins(filters)

  return (
    <div>
      <CoinFilters />
      <Button onClick={reset}>Clear Filters</Button>
      <CoinGrid coins={data?.items || []} />
    </div>
  )
}
```

---

## Domain Types (`src/domain/`)

### Zod Schemas

**File**: `src/domain/schemas.ts`

Type definitions using Zod schemas that mirror backend domain entities.

**Enums**:
```typescript
import { z } from 'zod'

export const MetalSchema = z.enum([
  'gold',
  'silver',
  'bronze',
  'copper',
  'electrum',
  'billon',
  'potin',
  'orichalcum',
])

export const CategorySchema = z.enum([
  'greek',
  'roman_imperial',
  'roman_republic',
  'roman_provincial',
  'byzantine',
  'medieval',
  'other'
])

export const GradingStateSchema = z.enum([
  'raw',
  'slabbed',
  'capsule',
  'flip',
])

export const GradeServiceSchema = z.enum([
  'ngc',
  'pcgs',
  'icg',
  'anacs',
  'none',
])
```

**Value Objects** (match backend):
```typescript
export const DimensionsSchema = z.object({
  weight_g: z.coerce.number().min(0).nullable().optional(),
  diameter_mm: z.coerce.number().min(0).nullable().optional(),
  thickness_mm: z.coerce.number().min(0).nullable().optional(),
  die_axis: z.coerce.number().min(0).max(12).nullable().optional(),
})

export const AttributionSchema = z.object({
  issuer: z.string().min(1).nullable().optional(),
  issuer_id: z.number().nullable().optional(),
  mint: z.string().nullable().optional(),
  mint_id: z.number().nullable().optional(),
  year_start: z.coerce.number().nullable().optional(),
  year_end: z.coerce.number().nullable().optional(),
})

export const GradingDetailsSchema = z.object({
  grading_state: GradingStateSchema.optional(),
  grade: z.string().nullable().optional(),
  service: GradeServiceSchema.nullable().optional(),
  certification_number: z.string().nullable().optional(),
  strike: z.string().nullable().optional(),
  surface: z.string().nullable().optional(),
  eye_appeal: z.number().nullable().optional(),
  toning_description: z.string().nullable().optional(),
})

export const AcquisitionDetailsSchema = z.object({
  price: z.coerce.number().min(0).nullable().optional(),
  currency: z.string().nullable().optional(),
  source: z.string().nullable().optional(),
  date: z.string().nullable().optional(), // ISO string
  url: z.string().url().nullable().optional(),
})
```

**Coin Schema** (nested domain entity):
```typescript
export const CoinSchema = z.object({
  id: z.number().nullable(),
  created_at: z.string().optional(),
  updated_at: z.string().optional(),

  // Classification
  category: z.string(),
  sub_category: z.string().nullable().optional(),
  denomination: z.string().nullable().optional(),
  metal: MetalSchema.optional(),
  series: z.string().nullable().optional(),

  // People
  issuing_authority: z.string().nullable().optional(),
  portrait_subject: z.string().nullable().optional(),
  status: z.string().nullable().optional(),

  // Chronology
  reign_start: z.number().nullable().optional(),
  reign_end: z.number().nullable().optional(),
  mint_year_start: z.number().nullable().optional(),
  mint_year_end: z.number().nullable().optional(),
  is_circa: z.boolean().optional(),

  // Nested value objects (match backend Clean Architecture)
  dimensions: DimensionsSchema,
  attribution: AttributionSchema,
  grading: GradingDetailsSchema,
  acquisition: AcquisitionDetailsSchema.nullable().optional(),

  // Design (flat for backwards compatibility)
  obverse_legend: z.string().nullable().optional(),
  obverse_description: z.string().nullable().optional(),
  reverse_legend: z.string().nullable().optional(),
  reverse_description: z.string().nullable().optional(),
  description: z.string().nullable().optional(),

  // Relations
  images: z.array(ImageSchema).default([]).optional(),
  tags: z.array(z.string()).optional(),
  references: z.array(CatalogReferenceSchema).optional(),
  provenance: z.array(z.any()).optional(),
})

export type Coin = z.infer<typeof CoinSchema>
export type Metal = z.infer<typeof MetalSchema>
export type Category = z.infer<typeof CategorySchema>
export type Dimensions = z.infer<typeof DimensionsSchema>
export type Attribution = z.infer<typeof AttributionSchema>
export type GradingDetails = z.infer<typeof GradingDetailsSchema>
export type AcquisitionDetails = z.infer<typeof AcquisitionDetailsSchema>
```

**Series Schema**:
```typescript
export const SeriesSchema = z.object({
  id: z.number(),
  name: z.string(),
  slug: z.string(),
  description: z.string().nullable().optional(),
  series_type: z.string(),
  category: z.string().nullable().optional(),
  target_count: z.number().nullable().optional(),
  is_complete: z.boolean(),
  completion_date: z.string().nullable().optional(),
  canonical_vocab_id: z.number().nullable().optional(),  // V3: Link to vocab
  slots: z.array(SeriesSlotSchema).optional(),
  coin_count: z.number().optional(),
})

export type Series = z.infer<typeof SeriesSchema>
```

---

## Utilities (`src/lib/`)

### `utils.ts`

Common utility functions.

```typescript
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

// Tailwind class merge utility (for shadcn/ui)
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Format currency
export function formatCurrency(value: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(value)
}

// Format date
export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

// Format year (BC/AD)
export function formatYear(year: number): string {
  if (year < 0) return `${Math.abs(year)} BC`
  return `AD ${year}`
}

// Format year range
export function formatYearRange(start: number, end: number): string {
  if (start === end) return formatYear(start)
  return `${formatYear(start)} - ${formatYear(end)}`
}
```

---

## Key Patterns Summary

### V2 API Integration

**✅ CORRECT**:
```typescript
import { v2 } from '@/api/v2'
import { useQuery } from '@tanstack/react-query'

function useCoins(filters?: Record<string, any>) {
  return useQuery({
    queryKey: ['coins', filters],
    queryFn: () => v2.getCoins(filters),  // Uses /api/v2/coins
  })
}
```

**❌ WRONG**:
```typescript
// Don't call axios directly
const response = await axios.get('/coins')

// Don't use old /api paths without /v2
const response = await api.get('/api/coins')
```

### TanStack Query v5 Syntax

**✅ CORRECT**:
```typescript
// Object-based configuration
useQuery({
  queryKey: ['coin', id],
  queryFn: () => v2.getCoin(id),
  enabled: !!id,
})

useMutation({
  mutationFn: (data) => v2.createCoin(data),
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ['coins'] }),
})
```

**❌ WRONG**:
```typescript
// Old v4 syntax (array-based)
useQuery(['coin', id], () => v2.getCoin(id))

useMutation((data) => v2.createCoin(data), {
  onSuccess: () => queryClient.invalidateQueries(['coins'])
})
```

### Import Conventions

**✅ CORRECT**:
```typescript
import { Button } from '@/components/ui/button'
import { v2 } from '@/api/v2'
import { Coin, CoinSchema } from '@/domain/schemas'
import { useUIStore } from '@/stores/uiStore'
```

**❌ WRONG**:
```typescript
// Don't use relative paths for cross-feature imports
import { Button } from '../../../components/ui/button'
import { v2 } from '../../api/v2'
```

### Domain Types

**✅ CORRECT** (Zod schemas):
```typescript
import { z } from 'zod'

export const CoinSchema = z.object({
  id: z.number().nullable(),
  category: z.string(),
  dimensions: DimensionsSchema,
})

export type Coin = z.infer<typeof CoinSchema>
```

**❌ WRONG** (plain TypeScript interfaces):
```typescript
// Don't define plain interfaces for domain types
interface Coin {
  id: number | null
  category: string
  dimensions: Dimensions
}
```

**Why Zod?**:
- Runtime validation of API responses
- Type inference from schemas
- Consistent with backend Pydantic models
- Automatic form validation with react-hook-form

---

## Testing Patterns

### Component Tests

```typescript
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CoinCard } from '@/components/coins/CoinCard'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } }
})

describe('CoinCard', () => {
  it('renders coin data', () => {
    const coin: Coin = {
      id: 1,
      category: 'roman_imperial',
      metal: 'silver',
      attribution: { issuer: 'Augustus' },
      dimensions: {},
      grading: {},
      acquisition: null,
    }

    render(
      <QueryClientProvider client={queryClient}>
        <CoinCard coin={coin} />
      </QueryClientProvider>
    )

    expect(screen.getByText('Augustus')).toBeInTheDocument()
    expect(screen.getByText('silver')).toBeInTheDocument()
  })
})
```

### Hook Tests

```typescript
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useCoins } from '@/hooks/useCoins'

const queryClient = new QueryClient()
const wrapper = ({ children }) => (
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
)

describe('useCoins', () => {
  it('fetches coins', async () => {
    const { result } = renderHook(() => useCoins(), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.items).toBeDefined()
  })
})
```

---

## Design System v3.1 (January 2026)

The frontend uses Design System v3.1 with specific component specifications:

- **Card dimensions**: 360×170px (desktop), responsive mobile
- **Images**: 160×160px square with 3D flip
- **Badge order**: [Certification] [Grade] [Metal] [Rarity●]
- **Badge font**: 8px with 2px 5px padding

For complete design token reference, see **[10-DESIGN-SYSTEM.md](10-DESIGN-SYSTEM.md)**.
For detailed component implementations, see **[11-FRONTEND-COMPONENTS.md](11-FRONTEND-COMPONENTS.md)**.

---

**Previous**: [03-BACKEND-MODULES.md](03-BACKEND-MODULES.md) - Backend reference
**Next**: [05-DATA-MODEL.md](05-DATA-MODEL.md) - Database schema
**Related**: 
- [10-DESIGN-SYSTEM.md](10-DESIGN-SYSTEM.md) - Design tokens and specs
- [11-FRONTEND-COMPONENTS.md](11-FRONTEND-COMPONENTS.md) - Component details
- [06-DATA-FLOWS.md](06-DATA-FLOWS.md) - Sequence diagrams
- [07-API-REFERENCE.md](07-API-REFERENCE.md) - API endpoints
