# Frontend Components Reference - AI Assistant Guide

> Comprehensive guide to CoinStack React components, patterns, and implementation details.
> **Last Updated**: January 2026 (v3.4 - Coin Detail Overhaul Complete)
>
> **See Also**: [12-UI-UX-ROADMAP.md](12-UI-UX-ROADMAP.md) for planned enhancements

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
│   │   ├── CoinCard.tsx       # Grid card (v3 design)
│   │   ├── CoinTableRowV3.tsx # Table row (v3.1 design)
│   │   ├── ImageUploadWithSplit.tsx # Upload + 2:1/1:2 split + gallery
│   │   ├── AddCoinImagesDialog.tsx  # Add obv/rev images from card
│   │   ├── CoinForm.tsx       # Create/edit form
│   │   ├── CollectionSidebar.tsx # Collection filters (Metal/Category/Grade/Rarity/Ruler chips)
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
│       ├── CoinDetailV3.tsx   # Detail display orchestrator
│       ├── CoinDetail/        # Coin detail page components (v3.2)
│       │   ├── index.tsx      # Exports
│       │   ├── IdentityHeader.tsx     # Catalog-style header
│       │   ├── ObverseReversePanel.tsx # Side-by-side panels
│       │   ├── CoinSidePanel.tsx      # Individual O/R panel
│       │   ├── ReferencesCard.tsx     # References + external links
│       │   └── ProvenanceTimeline.tsx # Timeline with gap handling
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

**Attribution display utility** (`lib/formatters.ts`): `getAttributionTitle(coin)` returns `{ primary, secondary, isPortraitSubject }` so cards and detail headers show portrait subject as primary and "Struck under {issuer}" as secondary when `portrait_subject` is set; otherwise issuer is primary. Use this helper wherever coin attribution is displayed to keep wording consistent.

---

## 2. Core Components

### 2.1 CoinCard / CoinCardV3 (Grid View)

**Location**: `frontend/src/components/coins/CoinCard.tsx`

**Purpose**: Displays a coin in grid view with v3.1 design system compliance.

**Key Features**:
- Horizontal layout (desktop) / vertical stack (mobile)
- **Attribution title**: When `portrait_subject` is set, it is the primary title and the issuer is shown as "Struck under {issuer}" below; otherwise the issuer is the primary title. Implemented via `getAttributionTitle()` in `lib/formatters.ts` (numismatic convention for empress/deified/deity on obverse).
- 3D flip animation on hover to show reverse
- Category bar with matching border-radius
- Compact badge row: [Cert] [Grade] [Metal] [Rarity●]
- Price with performance indicator
- **Add images trigger**: When obverse or reverse image is missing and `onAddImages` is provided, a semi-transparent overlay with “Add images” + `ImagePlus` icon is shown on the image area; click calls `onAddImages(coin)` and stops propagation so the card navigate does not fire.

**Props**:
```typescript
interface CoinCardProps {
  coin: Coin
  onClick?: (coin: Coin) => void
  selected?: boolean
  onSelect?: (id: number, selected: boolean) => void
  gridIndex?: number
  /** Opens add-images dialog when obv/rev missing; parent renders AddCoinImagesDialog and passes (coin) => setAddImagesCoin(coin) */
  onAddImages?: (coin: Coin) => void
}
```

**Usage**:
```typescript
import { CoinCard } from '@/components/coins/CoinCard'
import { AddCoinImagesDialog } from '@/components/coins/AddCoinImagesDialog'

const [addImagesCoin, setAddImagesCoin] = useState<Coin | null>(null)

<CoinCard
  coin={coin}
  onClick={() => navigate(`/coins/${coin.id}`)}
  onAddImages={(c) => setAddImagesCoin(c)}
/>
<AddCoinImagesDialog
  coin={addImagesCoin}
  open={!!addImagesCoin}
  onOpenChange={(open) => !open && setAddImagesCoin(null)}
  onSuccess={() => setAddImagesCoin(null)}
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

**Badge usage (VC-003)** — Use design-system badges for numismatic data so tokens stay consistent:

| Use case | Component | Location |
|----------|-----------|----------|
| **Metal** (AU, AR, AE, etc.) | `MetalBadge` | `@/components/ui/badges/MetalBadge` or `@/components/design-system/MetalBadge` |
| **Grade** (VF, AU, MS, etc.) | `GradeBadge` | `@/components/ui/badges/GradeBadge` or `@/components/design-system/GradeBadge` |
| **Certification** (NGC, PCGS) | `CertBadge` | `@/components/ui/badges/CertBadge` |
| **Rarity** (dot or label) | `RarityIndicator` | `@/components/design-system/RarityIndicator` |
| **Generic** (status, method, counts) | shadcn `Badge` | `@/components/ui/badge` — use for non-numismatic labels (e.g. “Pending”, “High”, method names). Prefer variants `outline`, `secondary`, or semantic tokens instead of raw Tailwind colors. |

Use MetalBadge/GradeBadge/CertBadge/RarityIndicator in coin cards, table rows, and detail views. Use generic `Badge` only for non-coin UI (filters, status, confidence).

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

### 2.4 ImageUploadWithSplit

**Location**: `frontend/src/components/coins/ImageUploadWithSplit.tsx`

**Purpose**: Shared “upload → detect 2:1/1:2 → split or add single → gallery with Obv/Rev/Remove/Primary”. Used by Coin Edit Finalize step and by AddCoinImagesDialog.

**Props**:
```typescript
export interface ImageEntry {
  url: string
  image_type: string   // 'obverse' | 'reverse' | 'general'
  is_primary: boolean
}

interface ImageUploadWithSplitProps {
  images: ImageEntry[]
  onImagesChange: (images: ImageEntry[]) => void
}
```

**Behavior**:
- Hidden file input + “Select File” (or similar) upload UI.
- Single file: `checkImageDimensions` — ratio 1.8–2.2 → 2:1 horizontal split suggestion; 0.45–0.55 → 1:2 vertical split suggestion; else add as general.
- Multiple files: each added via `addSingleImage`.
- Smart-split UI: toast + inline “Smart Split” panel with Confirm/Cancel; on confirm, appends obv + rev via `onImagesChange`.
- Gallery: Obv/Rev/Remove/Set-primary controls; all updates via `onImagesChange`.

### 2.5 AddCoinImagesDialog

**Location**: `frontend/src/components/coins/AddCoinImagesDialog.tsx`

**Purpose**: Dialog to add or replace obverse/reverse images for a single coin. Renders ImageUploadWithSplit, then saves via `client.updateCoin(id, { ...coin, images })` and invalidates `["coin", id]` and `["coins"]`.

**Props**:
```typescript
interface AddCoinImagesDialogProps {
  coin: Coin | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
}
```

**Usage**: Parent (e.g. CoinGridPage) holds `addImagesCoin: Coin | null`, renders one dialog, passes `onAddImages={(c) => setAddImagesCoin(c)}` to CoinCard. When user clicks “Add images” on a card, parent sets the coin and opens the dialog.

### 2.6 VocabAutocomplete

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

### 2.7 CoinDetail Components (v3.2)

**Location**: `frontend/src/features/collection/CoinDetail/`

**Purpose**: Scholarly numismatic coin detail page components.

**Add/attach images on detail page**: `CoinDetailPage` holds `addImagesOpen` state, renders `AddCoinImagesDialog` with the current coin, and passes `onOpenAddImages={() => setAddImagesOpen(true)}` to `CoinDetail`. The header shows “Attach images” (always), and each obverse/reverse panel shows “Add obverse/reverse image” when that side has no image; both open the same dialog. The dialog supports uploading single/multiple images, 2:1/1:2 smart split, and Obv/Rev/Remove/Set-primary in the gallery, then saves via `client.updateCoin` and invalidates `["coin", id]`.

#### IdentityHeader

**File**: `IdentityHeader.tsx`

**Purpose**: Catalog-style header with category bar, ruler, dates, references.

```typescript
interface IdentityHeaderProps {
  coin: Coin
  onEdit: () => void
  onDelete?: () => void
  onOpenAddImages?: () => void  // Opens add/attach images dialog
}
```

**Key Features**:
- 6px category bar (left border) using `var(--cat-${category})`
- Category label uppercase with category color
- **Attribution title**: Same convention as CoinCard via `getAttributionTitle()` — when `portrait_subject` is set, primary title is portrait subject and secondary line is "Struck under {issuer}" with reign dates; otherwise issuer with reign dates is the primary title.
- Type line: Denomination · Mint · Date
- References inline (RIC II 118 · RSC 240)
- Physical specs: 3.42g · 19mm · ↑6h
- **Attach images**: When `onOpenAddImages` is provided, an “Attach images” button (ImagePlus icon) appears next to Edit; opens AddCoinImagesDialog for adding or replacing obv/rev/general images.

#### ObverseReversePanel

**File**: `ObverseReversePanel.tsx`

**Purpose**: Side-by-side obverse/reverse display.

```typescript
interface ObverseReversePanelProps {
  coin: Coin
  onOpenAddImages?: () => void  // Opens add/attach images dialog; passed to side panels when that side has no image
  onEnrichLegend?: (side: 'obverse' | 'reverse') => void
}
```

**Key Features**:
- Side-by-side on desktop (>= 1024px), stacked on mobile
- Each panel has: image, legend (with copy), description, iconography
- Metal badge overlay on obverse image
- Legend expansion button for AI enrichment
- When a side has no image and `onOpenAddImages` is provided, that side shows an “Add obverse/reverse image” button (see CoinSidePanel).

#### CoinSidePanel

**File**: `CoinSidePanel.tsx`

**Purpose**: Individual obverse/reverse panel content.

```typescript
interface CoinSidePanelProps {
  side: 'obverse' | 'reverse'
  image?: string
  legend?: string | null
  legendExpanded?: string | null
  description?: string | null
  iconography?: string[] | null
  metal?: string
  portraitSubject?: string | null   // Person/deity on obverse (when different from issuer); obverse panel only
  onAddImage?: () => void   // Opens add-images dialog when this side has no image
  onEnrichLegend?: () => void
}
```

**Key Features**:
- Obverse panel shows **Portrait subject** section when `portraitSubject` is set (person/deity depicted on obverse when different from issuer).
- Zoomable image (uses ImageZoom component)
- When `!image && onAddImage`: shows “Add obverse/reverse image” button that calls `onAddImage` (opens AddCoinImagesDialog).
- Legend with copy-to-clipboard button
- Sparkle button for AI legend expansion
- Collapsible expanded legend section
- Iconography bullet list

#### ReferencesCard

**File**: `ReferencesCard.tsx`

**Purpose**: Display catalog references with validated external links.

```typescript
interface ReferencesCardProps {
  references: CatalogReference[] | null
  categoryType?: string
}
```

**Key Features**:
- Primary reference highlighted
- Concordance (secondary references)
- Validated external links (OCRE, CRRO, RPC)
- General search links (ACSearch, CoinArchives, Wildwinds)
- Uses `lib/referenceLinks.ts` for link generation

#### ProvenanceTimeline

**File**: `ProvenanceTimeline.tsx`

**Purpose**: Visual timeline of coin ownership history.

```typescript
interface ProvenanceTimelineProps {
  provenance: ProvenanceEntry[] | null
  categoryType?: string
  onAddProvenance?: () => void
}
```

**Key Features**:
- Chronological display with visual timeline
- Gap detection (>10 years between entries)
- Supports approximate dates (decades: "1920s")
- Price and currency formatting
- "Add provenance" button

#### HistoricalContextCard

**File**: `HistoricalContextCard.tsx`

**Purpose**: LLM-generated historical context display.

```typescript
interface HistoricalContextCardProps {
  context?: string | null
  generatedAt?: string | null
  coinMetadata: {
    coinId: number
    issuer?: string | null
    denomination?: string | null
    yearStart?: number | null
    yearEnd?: number | null
    category?: string | null
  }
  onGenerateContext?: () => Promise<void>
  isGenerating?: boolean
  categoryType?: string
}
```

**Key Features**:
- Collapsible card with AI-generated content
- Generate button for empty context
- Shows generation timestamp
- Regenerate option
- Purple sparkle icon for AI indicator

#### EnrichmentToolbar

**File**: `EnrichmentToolbar.tsx`

**Purpose**: Compact toolbar for batch AI enrichment actions.

```typescript
interface EnrichmentToolbarProps {
  actions: EnrichmentAction[]
  isEnriching?: boolean
  categoryType?: string
  defaultExpanded?: boolean
}
```

**Key Features**:
- Quick access to all LLM capabilities
- Progress indicator (X/Y complete)
- Green checkmarks for completed enrichments
- Collapsible for space saving

**Helper Hook**:
```typescript
import { useCoinEnrichmentActions } from './CoinDetail'

const actions = useCoinEnrichmentActions({
  onExpandObverse: () => handleExpandLegend('obverse'),
  onExpandReverse: () => handleExpandLegend('reverse'),
  onGenerateContext: handleGenerateContext,
  hasObverseLegendExpanded: !!coin.obverse_legend_expanded,
  // ... other options
})
```

#### DieStudyCard

**File**: `DieStudyCard.tsx`

**Purpose**: Simplified die study information display.

```typescript
interface DieStudyCardProps {
  dieAxis?: number | null
  dieMatch?: {
    obverseDie?: string | null
    reverseDie?: string | null
    isKnownCombination?: boolean
    matchingCoins?: number
  } | null
  controlMarks?: string[] | null
  dieStats?: {
    knownObverseDies?: number
    knownReverseDies?: number
    estimatedMintage?: string
  } | null
  categoryType?: string
  defaultExpanded?: boolean
}
```

**Key Features**:
- Collapsible card (default collapsed)
- Die axis with large clock visualization
- Die axis description (medallic vs coin alignment)
- Control marks display
- Die statistics grid
- Only renders when there's data

#### IconographySection

**File**: `IconographySection.tsx`

**Purpose**: Display iconographic elements from coin designs.

```typescript
interface IconographySectionProps {
  obverseIconography?: string[] | null
  reverseIconography?: string[] | null
  categoryType?: string
}
```

**Key Features**:
- Split view for obverse/reverse iconography
- Auto-matching icons (crown, sword, eagle, etc.)
- `IconographyInline` component for compact display
- Only renders when there's data

**Available Icons**:
- Crown/Diadem - royalty
- Swords/Spear - military
- Shield - armor
- Temple/Column - architecture
- Eagle/Bird - animals
- Branch/Olive - nature
- Star - celestial
- Flame/Torch - religious

### 2.8 DieAxisClock

**Location**: `frontend/src/components/coins/DieAxisClock.tsx`

**Purpose**: SVG clock visualization for coin die axis.

```typescript
interface DieAxisClockProps {
  axis: number | null  // 0-12 clock hours
  size?: 'sm' | 'md' | 'lg'  // 32px, 48px, 64px
  interactive?: boolean
  onChange?: (axis: number) => void
}
```

**Key Features**:
- Hour markers at 12, 3, 6, 9 (12h and 6h highlighted)
- Arrow pointing to die axis position
- "?" display when axis is null
- Interactive mode for editing
- Uses `var(--cat-imperial)` for arrow color

**Usage**:
```typescript
import { DieAxisClock } from '@/components/coins/DieAxisClock'

// Display mode
<DieAxisClock axis={6} size="sm" />

// Edit mode
<DieAxisClock
  axis={dieAxis}
  size="md"
  interactive
  onChange={(newAxis) => setDieAxis(newAxis)}
/>
```

### 2.9 CoinNavigation

**Location**: `frontend/src/components/coins/CoinNavigation.tsx`

**Purpose**: Left/right navigation between coin detail pages.

```typescript
interface CoinNavigationProps {
  currentCoinId: number
  className?: string
}
```

**Key Features**:
- Arrow buttons to navigate prev/next coin
- Keyboard shortcuts (left/right arrow keys)
- Position indicator (e.g., "5 / 30")
- Uses collection order from `useCoins()` hook

**Usage**:
```typescript
import { CoinNavigation } from '@/components/coins/CoinNavigation'

// In page header
<CoinNavigation currentCoinId={coinId} />
```

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

### 3.5 CollectionSidebar

**Location**: `frontend/src/components/coins/CollectionSidebar.tsx`

**Purpose**: Left sidebar on collection page with search, stats, and filter chips. All filters use the same badge-with-count pattern (design tokens).

**Filter chips** (from design-system): MetalChip, CategoryChip, GradeChip, RarityChip; Ruler section uses inline chips with `--bg-card`, `--border-subtle`, `--text-secondary`; selected state uses ring + optional gold accent. Ruler section is expanded by default and shows top 12 rulers. Unknown Ruler/Year/Mint and Attributes (Circa, Test Cut) use the same chip size and selected ring. See [10-DESIGN-SYSTEM.md § 4.7](10-DESIGN-SYSTEM.md#47-collection-sidebar-filter-chips).

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

### 6.2 useLLM Hooks

**Location**: `frontend/src/hooks/useLLM.ts`

**Purpose**: React hooks for LLM-powered numismatic operations.

```typescript
import { 
  useExpandLegendV2, 
  useObserveCondition, 
  useGenerateHistoricalContext,
  useNormalizeVocab,
  useParseAuction 
} from '@/hooks/useLLM'

// Legend expansion
const expandLegend = useExpandLegendV2()
expandLegend.mutate({ abbreviation: "IMP CAES AVG" })
// Returns: { expanded, confidence, cost_usd, model_used, cached }

// Condition observations (NOT grades)
const observeCondition = useObserveCondition()
observeCondition.mutate({ image_b64: base64Image })
// Returns: { wear_observations, surface_notes, strike_quality, concerns }

// Vocabulary normalization
const normalizeVocab = useNormalizeVocab()
normalizeVocab.mutate({ 
  raw_text: "Aug.", 
  vocab_type: "issuer" 
})
// Returns: { canonical_name, confidence, reasoning }
```

**Backend Endpoints**:
- `POST /api/v2/llm/legend/expand` - Expand Latin abbreviations
- `POST /api/v2/llm/condition/observe` - Describe wear (not grade)
- `POST /api/v2/llm/vocab/normalize` - Normalize vocabulary
- `POST /api/v2/llm/auction/parse` - Parse auction descriptions

### 6.3 useCollectionStats

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

### 8.4 Reference Links and Catalog Parse

**Location**: `frontend/src/lib/referenceLinks.ts`, `frontend/src/hooks/useCatalog.ts`

**Purpose**: Format references, build validated external links, and (optionally) parse reference strings. Authoritative parsing is backend `POST /api/v2/catalog/parse`; client `parseReference` is best-effort.

```typescript
import { buildExternalLinks, formatReference, parseReference, SUPPORTED_CATALOGS_FALLBACK } from '@/lib/referenceLinks'
import { useCatalogSystems, useParseCatalogReference } from '@/hooks/useCatalog'

// Format for display (includes volume, supplement, mint, collection when present)
formatReference({ catalog: 'RPC', volume: 'I', supplement: 'S', number: '123' }) // "RPC I S 123"
formatReference({ catalog: 'SNG', collection: 'Cop', number: '123' })           // "SNG Cop 123"

// Best-effort client parse; use API for validation
const parsed = parseReference('RIC II 118')  // { catalog: 'RIC', volume: 'II', number: '118' }

// Build links (uses ref.catalog for RIC/RRC/RPC detection; search query uses formatReference)
const links = buildExternalLinks(references)

// Catalog list: from API or fallback
const { data: systems } = useCatalogSystems()  // GET /api/v2/catalog/systems
// Fallback: SUPPORTED_CATALOGS_FALLBACK when API unavailable
```

**Validated Links** (by `ref.catalog`): OCRE (RIC), CRRO (RRC), RPC Online (RPC). General search links (ACSearch, Wildwinds, CoinArchives) use `formatReference(primaryRef)` for the query.

**Catalog Parse API**: `useParseCatalogReference().mutateAsync({ raw })` returns `{ ref, confidence, warnings }`; use for import validation or inline feedback.

### 8.5 Grade Color Helper

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

## 11. Planned Features (Not Yet Implemented)

The following features are specified but not yet implemented. See [12-UI-UX-ROADMAP.md](12-UI-UX-ROADMAP.md) for full details.

### High Priority (Phase 1)

| Feature | Status | Notes |
|---------|--------|-------|
| Keyboard Shortcuts | 🔴 Missing | N, U, /, G C, J/K/H/L navigation |
| Bulk Selection Store | 🔴 Missing | selectionStore.ts needed |
| Bulk Actions Bar | 🔴 Missing | Enrich, Export, Delete selected |
| Enhanced Command Palette | 🟡 Basic | Needs coin search, shortcuts |

### Medium Priority (Phase 2)

| Feature | Status | Notes |
|---------|--------|-------|
| User Preferences | 🟡 Partial | Missing showLegends, enableFlip |
| Saved Filters | 🔴 Missing | Save filter presets |
| Recent Items | 🔴 Missing | Recent searches, coins |
| Grid Navigation | 🔴 Missing | Vim-style J/K/H/L |

### Accessibility (Phase 4)

| Feature | Status | Notes |
|---------|--------|-------|
| ARIA on Cards | 🟡 Partial | Need role, aria-label, aria-pressed |
| Focus Management | 🟡 Partial | Need visible focus rings |
| Reduced Motion | 🔴 Missing | prefers-reduced-motion support |

---

**Previous**: [10-DESIGN-SYSTEM.md](10-DESIGN-SYSTEM.md) - Design tokens
**Next**: [12-UI-UX-ROADMAP.md](12-UI-UX-ROADMAP.md) - UI/UX implementation roadmap
**Related**: [04-FRONTEND-MODULES.md](04-FRONTEND-MODULES.md) - Architecture overview
