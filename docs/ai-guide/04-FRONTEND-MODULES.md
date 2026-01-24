# Frontend Modules Reference

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
│   ├── audit/           # Audit components
│   ├── auctions/        # Auction components
│   ├── import/          # Import workflow
│   └── design-system/   # Domain-specific components
│
├── hooks/               # TanStack Query hooks
├── stores/              # Zustand stores
├── types/               # TypeScript types
└── lib/                 # Utilities
```

---

## Core Application Files

### `main.tsx`

Application entry point.

```typescript
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'

createRoot(document.getElementById('root')!).render(<App />)
```

### `App.tsx`

Root component with providers and routing.

```typescript
// Providers
- QueryClientProvider (TanStack Query)
- ThemeProvider (dark/light mode)
- BrowserRouter (React Router)
- Toaster (sonner notifications)

// Query Client Config
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
})

// Routes
<Routes>
  <Route element={<AppShell />}>
    <Route path="/" element={<CollectionPage />} />
    <Route path="/coins/new" element={<AddCoinPage />} />
    <Route path="/coins/:id" element={<CoinDetailPage />} />
    <Route path="/coins/:id/edit" element={<EditCoinPage />} />
    <Route path="/import" element={<ImportPage />} />
    <Route path="/stats" element={<StatsPage />} />
    <Route path="/settings" element={<SettingsPage />} />
    <Route path="/bulk-enrich" element={<BulkEnrichPage />} />
    <Route path="/auctions" element={<AuctionsPage />} />
    <Route path="/audit" element={<AuditPage />} />
  </Route>
</Routes>
```

### `index.css`

Global styles and CSS custom properties.

```css
/* Design tokens for metals, grades, rarities */
:root {
  /* Metals */
  --metal-au: #ffd700;    /* Gold */
  --metal-ar: #c0c0c0;    /* Silver */
  --metal-ae: #cd7f32;    /* Bronze */
  
  /* Rarities */
  --rarity-common: #6b7280;
  --rarity-scarce: #22c55e;
  --rarity-rare: #3b82f6;
  --rarity-very-rare: #a855f7;
  --rarity-extremely-rare: #ef4444;
  --rarity-unique: #fbbf24;
  
  /* Categories */
  --category-republic: #dc2626;
  --category-imperial: #7c3aed;
  --category-provincial: #059669;
  --category-byzantine: #d97706;
  --category-greek: #2563eb;
}
```

---

## Pages (`src/pages/`)

### `CollectionPage.tsx`

Main collection view with grid/table toggle.

```typescript
// Features:
- Grid view (CoinCard) / Table view (CoinTable)
- Filter panel with all filter options
- Pagination controls
- Quick actions (add, import)
- Column customization (table view)

// Key hooks:
- useCoins() - Fetch paginated coins
- useFilterStore() - Filter state
- useUIStore() - View mode toggle
- useColumnStore() - Table columns
```

### `CoinDetailPage.tsx`

Individual coin detail view.

```typescript
// Features:
- Image gallery with zoom
- All coin fields organized in sections
- Reference list with catalog links
- Provenance timeline
- Linked auction data
- Edit/Delete actions
- Navigation (prev/next)

// Key hooks:
- useCoin(id) - Fetch single coin
- useCoinNavigation(id) - Get prev/next IDs
```

### `AddCoinPage.tsx` / `EditCoinPage.tsx`

Coin form for create/edit.

```typescript
// Features:
- Multi-tab form (Identity, Attribution, Design, etc.)
- Inline legend expansion
- Reference autocomplete
- Image upload
- Validation with Zod

// Key hooks:
- useCreateCoin() - Mutation for create
- useUpdateCoin() - Mutation for update
- useLegendExpand() - Legend expansion
```

### `ImportPage.tsx`

Import workflow hub.

```typescript
// Features:
- URL import panel
- NGC lookup panel
- Excel/CSV upload
- Batch import
- Preview before saving
- Duplicate detection

// Key hooks:
- useImportFromURL() - Parse auction URL
- useNGCLookup() - NGC certificate
- useImportExcel() - Excel import
- useCheckDuplicates() - Duplicate check
```

### `AuditPage.tsx`

Audit and quality management.

```typescript
// Features:
- Audit run controls
- Discrepancy list with filters
- Enrichment suggestions
- Auto-merge controls
- Field history viewer
- Conflict triage view

// Key hooks:
- useAuditSummary() - Summary stats
- useDiscrepancies() - Discrepancy list
- useEnrichments() - Enrichment list
- useStartAudit() - Start audit mutation
- useResolveDiscrepancy() - Resolve mutation
- useApplyEnrichment() - Apply mutation
```

### `AuctionsPage.tsx`

Auction data management.

```typescript
// Features:
- Auction list with filters
- Scrape URL dialog
- Link to coin action
- Price comparables

// Key hooks:
- useAuctions() - Fetch auctions
- useScrapeURL() - Scrape mutation
```

### `StatsPage.tsx`

Collection statistics dashboard.

```typescript
// Features:
- Total collection value
- Distribution charts (category, metal, ruler)
- Price distribution histogram
- Timeline coverage
- Recent acquisitions

// Key hooks:
- useCollectionStats() - All statistics
```

### `SettingsPage.tsx`

Application settings.

```typescript
// Features:
- Database info
- Backup/restore
- CSV export
- Clear cache

// Key hooks:
- useSettings() - Settings data
- useBackup() - Backup mutation
```

---

## Components (`src/components/`)

### Layout Components (`layout/`)

#### `AppShell.tsx`

Main layout wrapper.

```typescript
// Structure:
<div className="flex h-screen">
  <Sidebar />
  <div className="flex-1 flex flex-col">
    <Header />
    <main className="flex-1 overflow-auto">
      <Outlet /> {/* Route content */}
    </main>
  </div>
</div>
```

#### `Header.tsx`

Top navigation bar.

```typescript
// Features:
- Global search input
- Add coin button
- Theme toggle
- Command palette trigger (Cmd+K)
```

#### `Sidebar.tsx`

Left navigation sidebar.

```typescript
// Navigation items:
- Collection (home)
- Import
- Auctions
- Audit
- Statistics
- Settings

// Features:
- Collapsible
- Active state indication
- Icons from lucide-react
```

#### `CommandPalette.tsx`

Keyboard-driven command palette (Cmd+K).

```typescript
// Commands:
- Navigate to pages
- Quick actions (add coin, start audit)
- Search coins
- Toggle theme
```

#### `ThemeToggle.tsx`

Dark/light mode toggle button.

```typescript
// Uses ThemeProvider context
// Cycles: dark -> light -> system
```

### Coin Components (`coins/`)

#### `CoinCard.tsx`

Grid view card for a coin.

```typescript
interface CoinCardProps {
  coin: CoinListItem
  onClick?: () => void
}

// Displays:
- Primary image thumbnail
- Issuing authority
- Denomination
- Metal badge
- Grade badge
- Price
```

#### `CoinTable.tsx`

Table view for coins.

```typescript
interface CoinTableProps {
  coins: CoinListItem[]
  onRowClick?: (id: number) => void
}

// Features:
- Sortable columns
- Customizable columns (from columnStore)
- Row selection
- Compact/comfortable density
```

#### `CoinForm.tsx`

Multi-tab form for coin data.

```typescript
interface CoinFormProps {
  coin?: CoinDetail  // For edit mode
  onSubmit: (data: CoinCreate | CoinUpdate) => void
  isLoading?: boolean
}

// Tabs:
1. Identity - category, denomination, metal
2. Attribution - ruler, dates, mint
3. Design - obverse/reverse legends and descriptions
4. Physical - weight, diameter, die axis
5. Grading - service, grade, certification
6. Collection - acquisition, storage, value, notes
7. References - catalog references
8. Images - image upload
```

#### `CoinFilters.tsx`

Filter panel for collection view.

```typescript
// Filter options:
- Category (select)
- Metal (select)
- Rarity (select)
- Grade range (slider)
- Price range (min/max inputs)
- Year range (min/max inputs)
- Ruler (text search)
- Mint (text search)
- Full-text search
```

#### `ImageGallery.tsx`

Image viewer for coin detail.

```typescript
interface ImageGalleryProps {
  images: CoinImage[]
  onUpload?: (file: File) => void
}

// Features:
- Thumbnail strip
- Main image display
- Zoom on hover/click
- Upload dropzone
```

### Audit Components (`audit/`)

#### `DiscrepancyCard.tsx`

Card showing a single discrepancy.

```typescript
interface DiscrepancyCardProps {
  discrepancy: Discrepancy
  onResolve: (status: 'accepted' | 'rejected') => void
}

// Displays:
- Field name
- Current value vs suggested value
- Severity indicator
- Source info
- Accept/Reject buttons
```

#### `EnrichmentCard.tsx`

Card showing enrichment suggestion.

```typescript
interface EnrichmentCardProps {
  enrichment: Enrichment
  onApply: () => void
  onReject: () => void
}

// Displays:
- Field name
- Suggested value
- Confidence score
- Source type
- Apply/Reject buttons
```

#### `ConflictTriageView.tsx`

Keyboard-driven conflict resolution view.

```typescript
// Features:
- One conflict at a time
- Side-by-side comparison
- Keyboard shortcuts (A=accept, R=reject, S=skip)
- Progress indicator
```

#### `AuditSummaryStats.tsx`

Summary statistics for audit.

```typescript
// Displays:
- Total discrepancies (by status)
- Total enrichments (by status)
- Auto-merge candidates
- Last audit run info
```

### Design System Components (`design-system/`)

#### `MetalBadge.tsx`

Badge showing coin metal.

```typescript
interface MetalBadgeProps {
  metal: Metal
  size?: 'sm' | 'md' | 'lg'
}

// Renders colored badge with metal abbreviation
// AU (gold), AR (silver), AE (bronze), etc.
```

#### `GradeBadge.tsx`

Badge showing coin grade.

```typescript
interface GradeBadgeProps {
  grade: string
  service?: GradeService
}

// Color-coded by grade level
// Shows service logo if NGC/PCGS
```

#### `RarityIndicator.tsx`

Visual indicator for rarity.

```typescript
interface RarityIndicatorProps {
  rarity: Rarity
  showLabel?: boolean
}

// Colored dot + optional label
// Colors from common (gray) to unique (gold)
```

#### `PriceTrend.tsx`

Price trend indicator with sparkline.

```typescript
interface PriceTrendProps {
  current: number
  history: number[]
  change?: number
}

// Shows current price + up/down arrow + sparkline
```

### Import Components (`import/`)

#### `URLImportPanel.tsx`

Panel for importing from auction URL.

```typescript
// Features:
- URL input
- Parse button
- Preview of extracted data
- Confidence indicators
- Save/Edit before save
```

#### `BatchImportPanel.tsx`

Panel for batch importing multiple coins.

```typescript
// Features:
- Multi-URL input
- Progress indicator
- Success/failure list
- Retry failed
```

#### `DuplicateAlert.tsx`

Alert showing potential duplicate coins.

```typescript
interface DuplicateAlertProps {
  duplicates: CoinListItem[]
  onProceed: () => void
  onCancel: () => void
}
```

### UI Components (`ui/`)

shadcn/ui components - use as provided, customize via CSS variables.

Key components:
- `Button` - Primary actions
- `Card` - Content containers
- `Dialog` - Modal dialogs
- `Select` - Dropdown selection
- `Input` - Text inputs
- `Table` - Data tables
- `Tabs` - Tab navigation
- `Badge` - Status indicators
- `Tooltip` - Hover hints
- `Skeleton` - Loading states

---

## Hooks (`src/hooks/`)

### Data Fetching Hooks (TanStack Query)

#### `useCoins.ts`

```typescript
// List coins with filters
function useCoins(filters?: CoinFilters) {
  return useQuery({
    queryKey: ['coins', filters],
    queryFn: () => api.get('/coins', { params: filters }),
  })
}

// Get single coin
function useCoin(id: number) {
  return useQuery({
    queryKey: ['coin', id],
    queryFn: () => api.get(`/coins/${id}`),
  })
}

// Create coin
function useCreateCoin() {
  return useMutation({
    mutationFn: (data: CoinCreate) => api.post('/coins', data),
    onSuccess: () => queryClient.invalidateQueries(['coins']),
  })
}

// Update coin
function useUpdateCoin() {
  return useMutation({
    mutationFn: ({ id, data }) => api.put(`/coins/${id}`, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries(['coins'])
      queryClient.invalidateQueries(['coin', id])
    },
  })
}

// Delete coin
function useDeleteCoin() {
  return useMutation({
    mutationFn: (id: number) => api.delete(`/coins/${id}`),
    onSuccess: () => queryClient.invalidateQueries(['coins']),
  })
}

// Navigation (prev/next)
function useCoinNavigation(id: number) {
  return useQuery({
    queryKey: ['coin-nav', id],
    queryFn: () => api.get(`/coins/${id}/nav`),
  })
}
```

#### `useAudit.ts`

```typescript
// Audit summary
function useAuditSummary() {
  return useQuery({
    queryKey: ['audit', 'summary'],
    queryFn: () => api.get('/audit/summary'),
  })
}

// Discrepancies list
function useDiscrepancies(filters?: DiscrepancyFilters) {
  return useQuery({
    queryKey: ['audit', 'discrepancies', filters],
    queryFn: () => api.get('/audit/discrepancies', { params: filters }),
  })
}

// Enrichments list
function useEnrichments(filters?: EnrichmentFilters) {
  return useQuery({
    queryKey: ['audit', 'enrichments', filters],
    queryFn: () => api.get('/audit/enrichments', { params: filters }),
  })
}

// Start audit
function useStartAudit() {
  return useMutation({
    mutationFn: (coinIds?: number[]) => api.post('/audit/start', { coin_ids: coinIds }),
    onSuccess: () => queryClient.invalidateQueries(['audit']),
  })
}

// Resolve discrepancy
function useResolveDiscrepancy() {
  return useMutation({
    mutationFn: ({ id, status, note }) => 
      api.post(`/audit/discrepancies/${id}/resolve`, { status, note }),
    onSuccess: () => queryClient.invalidateQueries(['audit', 'discrepancies']),
  })
}

// Apply enrichment
function useApplyEnrichment() {
  return useMutation({
    mutationFn: (id: number) => api.post(`/audit/enrichments/${id}/apply`),
    onSuccess: () => {
      queryClient.invalidateQueries(['audit', 'enrichments'])
      queryClient.invalidateQueries(['coins'])
    },
  })
}
```

#### `useAuctions.ts`

```typescript
// List auctions
function useAuctions(filters?: AuctionFilters)

// Get comparable auctions for coin
function useComparables(coinId: number)

// Scrape URL
function useScrapeURL()

// Link auction to coin
function useLinkAuction()
```

#### `useCatalog.ts`

```typescript
// Lookup reference
function useCatalogLookup(reference: string)

// Enrich coin from catalog
function useEnrichFromCatalog()

// Bulk enrich
function useBulkEnrich()
```

#### `useImport.ts`

```typescript
// Import from URL
function useImportFromURL()

// NGC lookup
function useNGCLookup()

// Excel import
function useImportExcel()

// Check duplicates
function useCheckDuplicates()
```

#### `useStats.ts`

```typescript
// All collection statistics
function useCollectionStats() {
  return useQuery({
    queryKey: ['collection-stats'],
    queryFn: () => api.get('/stats'),
    staleTime: 1000 * 60 * 10, // 10 minutes
  })
}
```

#### `useLegend.ts`

```typescript
// Expand legend abbreviations
function useLegendExpand() {
  return useMutation({
    mutationFn: (legend: string) => api.post('/legend/expand', { legend }),
  })
}
```

### Utility Hooks

#### `useDebounce.ts`

```typescript
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value)
  
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  
  return debouncedValue
}
```

#### `useAuditKeyboard.ts`

```typescript
// Keyboard shortcuts for audit triage
function useAuditKeyboard(handlers: {
  onAccept: () => void
  onReject: () => void
  onSkip: () => void
}) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'a') handlers.onAccept()
      if (e.key === 'r') handlers.onReject()
      if (e.key === 's') handlers.onSkip()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handlers])
}
```

---

## Stores (`src/stores/`)

### `uiStore.ts`

UI state management.

```typescript
interface UIState {
  sidebarOpen: boolean
  viewMode: 'grid' | 'table'
  commandPaletteOpen: boolean
  parseListingOpen: boolean
  
  // Actions
  toggleSidebar: () => void
  setViewMode: (mode: 'grid' | 'table') => void
  openCommandPalette: () => void
  closeCommandPalette: () => void
}

const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  viewMode: 'grid',
  commandPaletteOpen: false,
  parseListingOpen: false,
  
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setViewMode: (mode) => set({ viewMode: mode }),
  openCommandPalette: () => set({ commandPaletteOpen: true }),
  closeCommandPalette: () => set({ commandPaletteOpen: false }),
}))
```

### `filterStore.ts`

Filter and pagination state with persistence.

```typescript
interface FilterState {
  // Filters
  category: Category | null
  metal: Metal | null
  rarity: Rarity | null
  gradeMin: string | null
  gradeMax: string | null
  priceMin: number | null
  priceMax: number | null
  yearStart: number | null
  yearEnd: number | null
  ruler: string | null
  mint: string | null
  search: string
  
  // Sorting
  sortBy: string
  sortDir: 'asc' | 'desc'
  
  // Pagination
  page: number
  perPage: number  // 20, 50, 100, or -1 for all
  
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

const useFilterStore = create<FilterState>()(
  persist(
    (set, get) => ({
      // Initial state...
      
      toParams: () => {
        const state = get()
        const params: Record<string, any> = {}
        if (state.category) params.category = state.category
        if (state.metal) params.metal = state.metal
        // ... build params object
        return params
      },
      
      getActiveFilterCount: () => {
        const state = get()
        let count = 0
        if (state.category) count++
        if (state.metal) count++
        // ... count active filters
        return count
      },
    }),
    { name: 'coinstack-filters' }
  )
)
```

### `columnStore.ts`

Table column configuration with persistence.

```typescript
interface Column {
  id: string
  label: string
  visible: boolean
  sortable: boolean
  width?: number
}

interface ColumnState {
  columns: Column[]
  
  // Actions
  toggleColumn: (id: string) => void
  reorderColumns: (fromIndex: number, toIndex: number) => void
  resetColumns: () => void
}

const DEFAULT_COLUMNS: Column[] = [
  { id: 'thumbnail', label: 'Image', visible: true, sortable: false },
  { id: 'category', label: 'Category', visible: true, sortable: true },
  { id: 'metal', label: 'Metal', visible: true, sortable: true },
  { id: 'denomination', label: 'Denomination', visible: true, sortable: true },
  { id: 'issuing_authority', label: 'Ruler', visible: true, sortable: true },
  { id: 'grade', label: 'Grade', visible: true, sortable: true },
  { id: 'acquisition_price', label: 'Price', visible: true, sortable: true },
  { id: 'rarity', label: 'Rarity', visible: false, sortable: true },
  { id: 'mint', label: 'Mint', visible: false, sortable: true },
  { id: 'reference', label: 'Reference', visible: false, sortable: false },
]

const useColumnStore = create<ColumnState>()(
  persist(
    (set) => ({
      columns: DEFAULT_COLUMNS,
      
      toggleColumn: (id) => set((state) => ({
        columns: state.columns.map((col) =>
          col.id === id ? { ...col, visible: !col.visible } : col
        ),
      })),
      
      reorderColumns: (from, to) => set((state) => {
        const cols = [...state.columns]
        const [removed] = cols.splice(from, 1)
        cols.splice(to, 0, removed)
        return { columns: cols }
      }),
      
      resetColumns: () => set({ columns: DEFAULT_COLUMNS }),
    }),
    { name: 'coinstack-columns' }
  )
)
```

---

## Types (`src/types/`)

### `coin.ts`

```typescript
// Enums (mirror backend)
enum Category {
  republic = 'republic',
  imperial = 'imperial',
  provincial = 'provincial',
  byzantine = 'byzantine',
  greek = 'greek',
  other = 'other',
}

enum Metal {
  gold = 'gold',
  silver = 'silver',
  billon = 'billon',
  bronze = 'bronze',
  orichalcum = 'orichalcum',
  copper = 'copper',
}

enum Rarity {
  common = 'common',
  scarce = 'scarce',
  rare = 'rare',
  very_rare = 'very_rare',
  extremely_rare = 'extremely_rare',
  unique = 'unique',
}

enum GradeService {
  ngc = 'ngc',
  pcgs = 'pcgs',
  self = 'self',
  dealer = 'dealer',
}

// Interfaces
interface CoinListItem {
  id: number
  category: Category
  metal: Metal | null
  denomination: string | null
  issuing_authority: string | null
  grade: string | null
  acquisition_price: number | null
  primary_image_url: string | null
}

interface CoinDetail extends CoinListItem {
  // All coin fields...
  mint: Mint | null
  references: CoinReference[]
  images: CoinImage[]
  provenance_events: ProvenanceEvent[]
  tags: CoinTag[]
  countermarks: Countermark[]
  auction_data: AuctionData[]
}

interface CoinCreate {
  category: Category
  // All editable fields...
}

interface CoinUpdate {
  category?: Category
  // All fields optional...
}

interface PaginatedCoins {
  items: CoinListItem[]
  total: number
  page: number
  per_page: number
  pages: number
}

// Related types
interface CoinReference {
  id: number
  system: string
  volume: string | null
  number: string
}

interface CoinImage {
  id: number
  image_type: 'obverse' | 'reverse' | 'combined' | 'detail'
  file_path: string
  is_primary: boolean
}

interface Mint {
  id: number
  name: string
  ancient_name: string | null
  modern_name: string | null
}
```

### `audit.ts`

```typescript
enum TrustLevel {
  catalog = 'catalog',
  auction = 'auction',
  user = 'user',
  llm = 'llm',
}

enum DiscrepancyStatus {
  pending = 'pending',
  accepted = 'accepted',
  rejected = 'rejected',
  ignored = 'ignored',
}

enum EnrichmentStatus {
  pending = 'pending',
  applied = 'applied',
  rejected = 'rejected',
}

interface Discrepancy {
  id: number
  coin_id: number
  field_name: string
  coin_value: string | null
  auction_value: string | null
  difference_type: string
  severity: 'low' | 'medium' | 'high'
  status: DiscrepancyStatus
}

interface Enrichment {
  id: number
  coin_id: number
  field_name: string
  suggested_value: string
  confidence: number
  source_type: string
  status: EnrichmentStatus
}

interface AuditRun {
  id: number
  started_at: string
  completed_at: string | null
  coins_audited: number
  discrepancies_found: number
  enrichments_suggested: number
  status: 'running' | 'completed' | 'failed'
}

interface AuditSummary {
  pending_discrepancies: number
  pending_enrichments: number
  auto_merge_candidates: number
  last_audit: AuditRun | null
}
```

---

## Utilities (`src/lib/`)

### `api.ts`

Axios instance configuration.

```typescript
import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // Handle errors (toast notifications, etc.)
    throw error
  }
)
```

### `utils.ts`

Utility functions.

```typescript
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

// Tailwind class merge utility
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
```

---

**Previous:** [03-BACKEND-MODULES.md](03-BACKEND-MODULES.md) - Backend reference  
**Next:** [05-DATA-MODEL.md](05-DATA-MODEL.md) - Database schema
