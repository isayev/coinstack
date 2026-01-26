# UI/UX Implementation Roadmap

> Implementation specifications and feature backlog for CoinStack frontend enhancements.
> **Last Updated**: January 2026

---

## Implementation Status

| Feature | Status | Priority | Phase |
|---------|--------|----------|-------|
| Command Palette (Cmd+K) | 🟡 Basic | High | 1 |
| Keyboard Shortcuts | 🔴 Missing | High | 1 |
| Bulk Selection + Actions | 🔴 Missing | High | 1 |
| User Preferences Store | 🟡 Partial | Medium | 2 |
| Accessibility (ARIA) | 🟡 Partial | Medium | 4 |
| Coin Card (Flip + Legends) | 🟢 Complete | - | Done |
| Badge System | 🟢 Complete | - | Done |
| Year Histogram (Brush) | 🟢 Complete | - | Done |
| Dashboard Widgets | 🟢 Complete | - | Done |

---

## Phase 1: Core Infrastructure (High Priority)

### 1.1 Keyboard Shortcuts System

**Status**: Missing
**Files to create**: `src/hooks/useKeyboardShortcuts.ts`, `src/hooks/useHotkeys.ts`

#### Global Shortcuts

| Key | Action | Context |
|-----|--------|---------|
| `Cmd+K` | Open command palette | Global |
| `N` | New coin (manual entry) | Not in input |
| `U` | Paste URL (scrape) | Not in input |
| `/` | Focus search | Not in input |
| `G C` | Go to Collection | Not in input |
| `G S` | Go to Statistics | Not in input |
| `G A` | Go to Auctions | Not in input |
| `G E` | Go to Settings | Not in input |
| `J/K/H/L` | Navigate grid (vim-style) | On grid |
| `X` | Toggle selection | On coin card |
| `Cmd+A` | Select all | On grid |
| `Escape` | Clear selection | Any |
| `E` | Enrich selected | Has selection |
| `Delete` | Delete selected | Has selection |

#### Implementation Pattern

```typescript
// src/hooks/useKeyboardShortcuts.ts
import { useHotkeys } from 'react-hotkeys-hook';
import { useNavigate } from 'react-router-dom';
import { useUIStore } from '@/stores/uiStore';

export function useKeyboardShortcuts() {
  const navigate = useNavigate();
  const { setCommandPaletteOpen } = useUIStore();
  
  // Command palette
  useHotkeys('mod+k', (e) => {
    e.preventDefault();
    setCommandPaletteOpen(true);
  });
  
  // Quick actions (only when not in input)
  useHotkeys('n', () => navigate('/coins/new'), { 
    enabled: !isInputFocused() 
  });
  
  useHotkeys('u', () => {
    // Open quick scrape modal
  }, { enabled: !isInputFocused() });
  
  // Navigation
  useHotkeys('g c', () => navigate('/'), { enabled: !isInputFocused() });
  useHotkeys('g s', () => navigate('/stats'), { enabled: !isInputFocused() });
}

function isInputFocused(): boolean {
  const active = document.activeElement;
  return active instanceof HTMLInputElement || 
         active instanceof HTMLTextAreaElement;
}
```

**Dependencies**: `react-hotkeys-hook`

---

### 1.2 Bulk Selection System

**Status**: Missing
**Files to create**: `src/stores/selectionStore.ts`, `src/features/collection/BulkActionsBar.tsx`

#### Selection Store

```typescript
// src/stores/selectionStore.ts
import { create } from 'zustand';

interface SelectionState {
  selectedIds: Set<number>;
  isSelecting: boolean;
  
  toggle: (id: number) => void;
  select: (id: number) => void;
  deselect: (id: number) => void;
  selectAll: (ids: number[]) => void;
  clear: () => void;
}

export const useSelectionStore = create<SelectionState>((set) => ({
  selectedIds: new Set(),
  isSelecting: false,
  
  toggle: (id) => set((state) => {
    const newSet = new Set(state.selectedIds);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    return { selectedIds: newSet };
  }),
  
  select: (id) => set((state) => ({
    selectedIds: new Set(state.selectedIds).add(id)
  })),
  
  deselect: (id) => set((state) => {
    const newSet = new Set(state.selectedIds);
    newSet.delete(id);
    return { selectedIds: newSet };
  }),
  
  selectAll: (ids) => set({ selectedIds: new Set(ids) }),
  
  clear: () => set({ selectedIds: new Set(), isSelecting: false }),
}));
```

#### Bulk Actions Bar

Fixed at bottom of screen when items selected:

```
┌────────────────────────────────────────────────────────────────┐
│  12 selected  │  ✨ Enrich  │  📥 Export  │  🗑️ Delete  │  ✕  │
└────────────────────────────────────────────────────────────────┘
```

**Actions**:
- Enrich: Run LLM enrichment on selected coins
- Export: Download CSV/JSON of selected
- Delete: Remove selected coins (with confirmation)

---

### 1.3 Enhanced Command Palette

**Status**: Basic (navigation only)
**File**: `src/components/layout/CommandPalette.tsx`

#### Current State

- Basic navigation commands only
- No coin search
- No keyboard navigation hints

#### Enhancements Needed

1. **Coin Search Integration**
   - Add `useCoinSearch` hook
   - Show matching coins in results
   - Navigate to coin detail on select

2. **Action Descriptions + Shortcuts**
   - Show shortcut keys next to actions
   - Add descriptions for each action

3. **Recent Items**
   - Show recently viewed coins
   - Show recent searches

4. **Footer Hints**
   - `↑↓ Navigate`, `↵ Select`, `Esc Close`

#### Enhanced Structure

```tsx
interface CommandItem {
  id: string;
  type: 'action' | 'coin' | 'navigation' | 'filter';
  label: string;
  description?: string;
  icon?: React.ReactNode;
  shortcut?: string;
  onSelect: () => void;
}

// Actions should include:
const actions: CommandItem[] = [
  { id: 'add-coin', label: 'Add Coin', shortcut: 'N', ... },
  { id: 'paste-url', label: 'Paste Auction URL', shortcut: 'U', ... },
  { id: 'cert-lookup', label: 'NGC/PCGS Lookup', ... },
  { id: 'run-audit', label: 'Run Audit', ... },
  { id: 'enrich-all', label: 'AI Enrich Collection', ... },
];
```

---

## Phase 2: User Experience (Medium Priority)

### 2.1 User Preferences Store Enhancement

**Status**: Partial (uiStore exists but limited)
**File**: `src/stores/userPrefsStore.ts`

#### Missing Preferences

```typescript
interface UserPrefs {
  // Layout (existing in uiStore)
  sidebarOpen: boolean;
  viewMode: 'grid' | 'table' | 'compact';
  
  // NEW: Card Display Options
  showLegends: boolean;       // Toggle legends on cards
  enableFlip: boolean;        // Toggle 3D flip animation
  gridDensity: 'comfortable' | 'compact' | 'dense';
  
  // NEW: Saved Filters
  savedFilters: Record<string, SavedFilter>;
  lastUsedFilters: FilterState | null;
  
  // NEW: Recent Items
  recentSearches: string[];
  recentCoins: number[];  // Last viewed coin IDs
}
```

#### Usage Example

```tsx
// In CoinCard
function CoinCard({ coin }) {
  const { showLegends, enableFlip } = useUserPrefs();
  
  return (
    <div 
      onMouseEnter={() => enableFlip && setFlipped(true)}
      ...
    >
      {showLegends && <LegendsSection coin={coin} />}
    </div>
  );
}

// In Settings
function ViewSettings() {
  const { showLegends, setShowLegends } = useUserPrefs();
  
  return (
    <Toggle 
      label="Show legends on cards" 
      checked={showLegends} 
      onChange={setShowLegends} 
    />
  );
}
```

---

### 2.2 Grid Navigation

**Status**: Missing
**File**: `src/hooks/useGridNavigation.ts`

Vim-style navigation through coin grid:

```typescript
export function useGridNavigation(itemCount: number, columns: number) {
  const [focusIndex, setFocusIndex] = useState(0);
  
  useHotkeys('j', () => setFocusIndex(i => Math.min(i + columns, itemCount - 1)));
  useHotkeys('k', () => setFocusIndex(i => Math.max(i - columns, 0)));
  useHotkeys('h', () => setFocusIndex(i => Math.max(i - 1, 0)));
  useHotkeys('l', () => setFocusIndex(i => Math.min(i + 1, itemCount - 1)));
  useHotkeys('Home', () => setFocusIndex(0));
  useHotkeys('End', () => setFocusIndex(itemCount - 1));
  
  // Focus element when index changes
  useEffect(() => {
    document.querySelector(`[data-grid-index="${focusIndex}"]`)?.focus();
  }, [focusIndex]);
  
  return { focusIndex };
}
```

---

## Phase 3: Advanced Features

### 3.1 Quick Edit Mode

In-place editing of coin fields without navigating to edit page.

### 3.2 Saved Filter Presets

Save and name filter combinations for quick access.

### 3.3 Batch Operations

- Batch category assignment
- Batch grade update
- Batch export to Excel

---

## Phase 4: Polish (Accessibility & Performance)

### 4.1 Accessibility Requirements

#### ARIA Labels on Coin Cards

```tsx
<article
  role="button"
  aria-label={`${coin.issuing_authority} ${coin.denomination}, ${coin.mint}`}
  aria-pressed={isSelected}
  tabIndex={0}
  onKeyDown={handleKeyDown}
>
```

#### Focus Management

- Visible focus rings on all interactive elements
- Tab order follows logical flow
- Focus trap in modals

#### Reduced Motion Support

```css
@media (prefers-reduced-motion: reduce) {
  .coin-card__face {
    transition: none;
  }
  
  /* Fallback to opacity instead of 3D flip */
  .coin-card__image-container--flipped .coin-card__face--obverse {
    opacity: 0;
  }
  .coin-card__image-container--flipped .coin-card__face--reverse {
    opacity: 1;
  }
}
```

### 4.2 Loading States

- Skeleton loaders for cards
- Progress indicators for bulk operations
- Optimistic updates for selections

### 4.3 Empty States

- No coins matching filter
- No search results
- First-time user guidance

---

## Testing Criteria

### Keyboard Shortcuts
```
✓ Cmd+K opens Command Palette
✓ Type "trajan" → shows matching coins
✓ Press 'n' → opens Add Coin
✓ Press '/' → focuses search
✓ Press 'g c' → navigates to Collection
```

### Bulk Selection
```
✓ Click checkbox → selects coin
✓ Press 'x' on card → toggles selection
✓ Cmd+A → selects all visible
✓ Bulk bar appears with count
✓ Actions work on selection
```

### Accessibility
```
✓ Tab through all interactive elements
✓ Focus ring visible on keyboard nav
✓ Screen reader announces card content
✓ Reduced motion disables flip animation
```

---

## File Structure for New Features

```
frontend/src/
├── hooks/
│   ├── useHotkeys.ts           # NEW: Hotkey hook wrapper
│   ├── useKeyboardShortcuts.ts # NEW: Global shortcuts
│   ├── useGridNavigation.ts    # NEW: Grid nav
│   └── useCoinSearch.ts        # NEW: Search hook
│
├── stores/
│   ├── selectionStore.ts       # NEW: Bulk selection
│   └── userPrefsStore.ts       # NEW: Preferences (or extend uiStore)
│
├── features/
│   └── collection/
│       ├── BulkActionsBar.tsx  # NEW: Bulk actions
│       └── ...
│
└── components/
    └── layout/
        └── CommandPalette.tsx  # ENHANCE: Add search, shortcuts
```

---

## Dependencies to Add

```json
{
  "react-hotkeys-hook": "^4.x"
}
```

---

**Previous**: [11-FRONTEND-COMPONENTS.md](11-FRONTEND-COMPONENTS.md) - Component reference
**Related**: [10-DESIGN-SYSTEM.md](10-DESIGN-SYSTEM.md) - Design tokens
