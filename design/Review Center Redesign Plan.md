# Review Center Redesign Plan

> **Comprehensive UI/UX Redesign for CoinStack Audit Experience**
> 
> Author: AI Design Consultant  
> Date: January 26, 2026  
> Status: Planning

---

## Executive Summary

This document outlines a complete redesign of the CoinStack audit and review experience. The goal is to create a unified "Review Center" that consolidates all review tasks (vocabulary assignments, LLM suggestions, image assignments, data discrepancies) into a single, streamlined interface with professional numismatic aesthetics.

### Key Objectives

1. **Unify fragmented review workflows** into a single destination
2. **Add visibility** with sidebar badge showing pending items
3. **Reduce cognitive load** by simplifying from 6 tabs to 4
4. **Establish consistent design patterns** across all review types
5. **Enable efficient bulk operations** with keyboard shortcuts
6. **Maintain numismatic professionalism** in visual design

---

## Part 1: Current State Analysis

### 1.1 Existing Structure

```
Current Routes:
├── /audit          → AuditPage (6 tabs, mostly mocked)
└── /review         → ReviewQueuePage (vocab only, separate)

Current Sidebar:
├── Collection
├── Series
├── Auctions
├── Audit           ← No badge/counter
├── Statistics
├── Import
├── Enrich
└── Settings
```

### 1.2 Problems Identified

| Issue | Impact | Severity |
|-------|--------|----------|
| Vocab review on separate page | Users don't find it | High |
| No pending count in sidebar | No urgency/visibility | High |
| 6 tabs overwhelming | Cognitive overload | Medium |
| Back button goes to Settings | Confusing navigation | Medium |
| Most hooks return mock data | Features don't work | High |
| Inconsistent card designs | Visual dissonance | Medium |
| No keyboard shortcuts | Slow review workflow | Medium |

### 1.3 Data Sources (What Actually Works)

| Source | API Endpoint | Status |
|--------|--------------|--------|
| Vocab Review | `/api/v2/vocab/review` | ✅ Working |
| LLM Suggestions | `/api/v2/llm/review` | ✅ Working |
| Discrepancies | `/api/v2/audit/discrepancies` | ❌ Mocked |
| Enrichments | `/api/v2/audit/enrichments` | ❌ Mocked |
| Image Review | `/api/coins` (old) | ⚠️ Outdated |

---

## Part 2: Proposed Architecture

### 2.1 New Route Structure

```
Proposed Routes:
└── /review         → ReviewCenterPage (unified, 4 tabs)

Removed:
├── /audit          → Redirects to /review
└── /review (old)   → Merged into new /review
```

### 2.2 New Sidebar Structure

```
Sidebar Navigation:
├── Collection
├── Series
├── Auctions
├── Review Center (12)  ← NEW: Badge with pending count
├── Statistics
├── Import
├── Enrich
└── Settings
```

### 2.3 New Tab Structure

```
Review Center Tabs:
├── Vocabulary (2)      ← Issuer/Mint/Denomination assignments
├── AI Suggestions (8)  ← LLM catalog references & rarity
├── Images (0)          ← Coins needing images from auctions
└── Data (0)            ← Discrepancies & Enrichments (future)
```

### 2.4 Component Hierarchy

```
ReviewCenterPage/
├── ReviewSummaryCards          # Clickable stat cards at top
├── ReviewTabs                  # Tab navigation
│   ├── VocabularyReviewTab     # Merged from ReviewQueuePage
│   ├── AIReviewTab             # Enhanced LLMReviewTab
│   ├── ImageReviewTab          # Existing component
│   └── DataReviewTab           # Discrepancies + Enrichments
├── ReviewBulkActionsBar        # Sticky bottom bar
└── ReviewEmptyState            # When no items to review
```

---

## Part 3: Component Specifications

### 3.1 Sidebar Badge Component

**File:** `frontend/src/components/layout/SidebarBadge.tsx`

```tsx
interface SidebarBadgeProps {
  count: number;
  variant?: 'default' | 'warning' | 'urgent';
}
```

**Visual Spec:**
- Position: Right side of nav item, vertically centered
- Size: min-width 20px, height 20px, border-radius 10px
- Font: 11px, semibold
- Colors:
  - Default (1-9): `var(--metal-ar)` background, white text
  - Warning (10-49): `var(--caution)` background
  - Urgent (50+): `var(--error)` background, pulse animation
- When sidebar collapsed: Show as dot indicator only

**Behavior:**
- Updates via React Query (5-second refetch interval)
- Animates on count change (subtle scale bump)
- Disappears when count = 0

### 3.2 Review Count Hook (Real-Time)

**File:** `frontend/src/hooks/useReviewCountsRealtime.ts`

```typescript
interface ReviewCounts {
  total: number;
  vocabulary: number;
  ai: number;
  images: number;
  data: number;
}

export function useReviewCountsRealtime(): {
  data: ReviewCounts;
  isLoading: boolean;
  refetch: () => void;
}
```

**API Calls:**
1. `GET /api/v2/review/counts` → Single endpoint returning all counts (preferred)
   - OR fallback to multiple endpoints if counts endpoint not available
2. (Future) Image and Data counts

**Caching:**
- Refetch every 5 seconds (`refetchInterval: 5000`) for real-time updates
- Invalidate on any review action
- Uses React Query pattern (matches `BulkEnrichPage.tsx` implementation)

### 3.3 Review Summary Cards

**File:** `frontend/src/components/review/ReviewSummaryCards.tsx`

**Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │  📚         │ │  🤖         │ │  🖼️         │ │  📊         ││
│  │  Vocabulary │ │  AI         │ │  Images     │ │  Data       ││
│  │             │ │  Suggestions│ │             │ │             ││
│  │     2       │ │     8       │ │     0       │ │     0       ││
│  │   pending   │ │   pending   │ │   pending   │ │   pending   ││
│  │             │ │             │ │             │ │             ││
│  │ [Review →]  │ │ [Review →]  │ │ [Review →]  │ │ [Review →]  ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

**Behavior:**
- Clicking card switches to corresponding tab
- Card highlights when tab is active
- Count animates on change
- Zero-count cards are muted (gray)

**Colors by State:**
| Count | Card Style |
|-------|------------|
| 0 | Muted gray, no glow |
| 1-5 | Default, subtle border |
| 6-20 | Amber accent, slight glow |
| 21+ | Red accent, stronger glow |

### 3.4 Unified Review Card

**File:** `frontend/src/components/review/ReviewCard.tsx`

**Structure:**
```
┌─────────────────────────────────────────────────────────────────┐
│ ┌──────────┐                                                    │
│ │          │  #42 · Denarius · Nero                  [View →]   │
│ │  [IMG]   │  ──────────────────────────────────────────────    │
│ │          │                                                    │
│ └──────────┘  Field: mint                                       │
│               ──────────────────────────────────────────────    │
│               Current value:  "Roma"                            │
│               Suggested:      Rome                              │
│                                                                 │
│               ┌───────────────────────────────────────────┐     │
│               │ ████████████████████░░░░ 89% confidence   │     │
│               └───────────────────────────────────────────┘     │
│                                                                 │
│               Method: FTS match · Source: Vocabulary DB         │
│                                                                 │
│  ───────────────────────────────────────────────────────────    │
│  ☐ Select          [ Skip ]              [ ✓ Approve ]          │
└─────────────────────────────────────────────────────────────────┘
```

**Props:**
```typescript
interface ReviewCardProps {
  id: number;
  coinId: number;
  coinPreview: {
    image: string;
    denomination: string;
    issuer: string;
    category: string;
  };
  field: string;
  currentValue: string;
  suggestedValue: string | null;
  confidence: number;
  method: string;
  source: string;
  isSelected: boolean;
  onSelect: () => void;
  onApprove: () => void;
  onReject: () => void;
  onSkip?: () => void;
  onViewCoin: () => void;
}
```

**Visual States:**
| State | Visual Treatment |
|-------|------------------|
| Default | Standard card |
| Selected | Blue left border, subtle blue bg |
| Hovered | Elevated shadow |
| High confidence (>90%) | Green confidence bar |
| Medium confidence (70-90%) | Amber confidence bar |
| Low confidence (<70%) | Red confidence bar |
| No match | Gray, "Manual required" badge |

### 3.5 Vocabulary Review Tab

**File:** `frontend/src/components/review/VocabularyReviewTab.tsx`

**Features:**
- Table view with sortable columns
- **Default sort**: Confidence ASC (low-confidence items first) - review uncertain items first
- **Smart Sort button**: Client-side heuristic (confidence + field importance)
- Filters: Field type (issuer/mint/denomination), Confidence level
- Bulk select with checkbox column
- Inline approve/reject actions
- Empty state when no pending items
- Per-tab undo stack (last 3 actions)

**Columns:**
| Column | Width | Content |
|--------|-------|---------|
| ☐ | 40px | Checkbox for bulk select |
| Coin | 200px | Thumbnail + ID + denomination |
| Field | 100px | Badge: issuer/mint/denomination |
| Current | 180px | Raw value (monospace) |
| Suggested | 180px | Canonical name or "No match" |
| Confidence | 120px | Progress bar + percentage |
| Actions | 120px | Approve / Reject buttons |

### 3.6 AI Suggestions Tab

**File:** `frontend/src/components/review/AIReviewTab.tsx`

**Enhanced from existing LLMReviewTab with:**
- Unified card design (matches VocabularyReviewTab)
- **Default sort**: Confidence ASC (low-confidence items first)
- Expandable details for each suggestion
- Reference previews with links
- Rarity gemstone visualization
- Batch dismiss functionality
- Per-tab undo stack (last 3 actions)

**Content per item:**
```
┌─────────────────────────────────────────────────────────────────┐
│ #42 · Denarius                                                  │
│                                                                 │
│ Suggested References:                                           │
│   • RIC I² 123 (Primary)                                        │
│   • RSC 456                                                     │
│   • BMCRE 789                                                   │
│                                                                 │
│ Suggested Rarity:  [●] Scarce                                   │
│                                                                 │
│ Analysis: "This coin matches the description of RIC I² 123..."  │
│                                                                 │
│  [ Dismiss ]                              [ ✓ Accept All ]      │
└─────────────────────────────────────────────────────────────────┘
```

### 3.7 Bulk Actions Bar

**File:** `frontend/src/components/review/ReviewBulkActionsBar.tsx`

**Position:** Fixed to bottom of viewport, above footer
**Visibility:** Only when items are selected

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ☑ 5 items selected                                             │
│                                                                 │
│  [ Clear Selection ]      [ Reject All ]      [ ✓ Approve All ] │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Keyboard Shortcuts:**
| Key | Action |
|-----|--------|
| `Escape` | Clear selection |
| `a` | Approve all selected |
| `r` | Reject all selected |

### 3.8 Empty States

**File:** `frontend/src/components/review/ReviewEmptyState.tsx`

**Variants:**

1. **All Clear (no pending items)**
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                          ✓                                      │
│                                                                 │
│                    All caught up!                               │
│                                                                 │
│        No items need your review at the moment.                 │
│        New items will appear here when coins are                │
│        imported or AI analysis runs.                            │
│                                                                 │
│                   [ View Collection ]                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

2. **Tab-specific empty (e.g., no vocab items)**
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                          📚                                     │
│                                                                 │
│              No vocabulary items to review                      │
│                                                                 │
│        Vocabulary assignments are created when you              │
│        import coins or run bulk normalization.                  │
│                                                                 │
│                [ Run Bulk Normalize ]                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 4: Implementation Plan

### Phase 1: Foundation (Day 1)

**Tasks:**

1. **Create useReviewCountsRealtime hook**
   - File: `frontend/src/hooks/useReviewCountsRealtime.ts`
   - Fetches vocab + LLM counts via `/api/v2/review/counts` endpoint
   - 5-second refetch interval (`refetchInterval: 5000`) for real-time updates
   - Query invalidation on mutations
   - Matches pattern from `BulkEnrichPage.tsx`

2. **Create SidebarBadge component**
   - File: `frontend/src/components/layout/SidebarBadge.tsx`
   - Renders badge with count
   - Handles collapsed state

3. **Update Sidebar**
   - File: `frontend/src/components/layout/Sidebar.tsx`
   - Add badge to "Audit" nav item
   - Rename to "Review Center"
   - Connect to useReviewCount

4. **Create route redirect**
   - File: `frontend/src/App.tsx`
   - Redirect `/audit` to `/review`
   - Update route for ReviewCenterPage

### Phase 2: Core Components (Day 2)

**Tasks:**

1. **Create ReviewSummaryCards**
   - File: `frontend/src/components/review/ReviewSummaryCards.tsx`
   - 4 stat cards with counts
   - Click to switch tab

2. **Create ReviewCard**
   - File: `frontend/src/components/review/ReviewCard.tsx`
   - Unified card design
   - All visual states

3. **Create ReviewBulkActionsBar**
   - File: `frontend/src/components/review/ReviewBulkActionsBar.tsx`
   - Fixed bottom bar
   - Bulk actions (approve/reject)
   - Optional "Preview Selection" button (5+ items selected)
   - "Auto-Approve High-Conf" button (95%+ confidence)
   - Undo toast integration

4. **Create ReviewEmptyState**
   - File: `frontend/src/components/review/ReviewEmptyState.tsx`
   - Empty state variants

### Phase 3: Tab Components (Day 3)

**Tasks:**

1. **Create VocabularyReviewTab**
   - File: `frontend/src/components/review/VocabularyReviewTab.tsx`
   - Migrate from ReviewQueuePage
   - Add table view
   - Add bulk selection
   - Default sort: Confidence ASC (low-confidence first)
   - Smart Sort button (client-side heuristic)

2. **Enhance AIReviewTab**
   - File: `frontend/src/components/review/AIReviewTab.tsx`
   - Unified card design
   - Bulk actions
   - Default sort: Confidence ASC (low-confidence first)
   - Smart Sort button (client-side heuristic)

3. **Update ImageReviewTab**
   - File: `frontend/src/components/review/ImageReviewTab.tsx`
   - Fix API endpoints (v1 → v2)
   - Add empty state

4. **Create DataReviewTab**
   - File: `frontend/src/components/review/DataReviewTab.tsx`
   - Placeholder for future discrepancies/enrichments

### Phase 4: Main Page (Day 4)

**Tasks:**

1. **Create ReviewCenterPage**
   - File: `frontend/src/pages/ReviewCenterPage.tsx`
   - Combine all components
   - Tab state management
   - URL-based tab selection

2. **Add keyboard shortcuts**
   - `j/k` navigation
   - `a/r` approve/reject
   - `Space` toggle select
   - `Escape` clear selection

3. **Remove old pages**
   - Delete: `frontend/src/pages/ReviewQueuePage.tsx`
   - Update: `frontend/src/pages/AuditPage.tsx` (redirect only)

4. **Update navigation**
   - Update CommandPalette commands
   - Update any internal links

### Phase 5: Polish (Day 5)

**Tasks:**

1. **Animation & transitions**
   - Card hover effects
   - Tab switch transitions
   - Badge count animation
   - Bulk bar slide-up

2. **Responsive design**
   - Mobile tab stacking
   - Card layout adjustments
   - Collapsed sidebar badge

3. **Accessibility**
   - ARIA labels
   - Focus management
   - Screen reader support

4. **Contextual Help**
   - Tooltips on confidence badges: "Why low confidence?"
   - Tooltips on field labels: "What does this field mean?"
   - Numismatic context in tooltips (~1h)

5. **Documentation**
   - Update `docs/ai-guide/11-FRONTEND-COMPONENTS.md`
   - Update `docs/ai-guide/12-UI-UX-ROADMAP.md`

---

## Part 5: File Changes Summary

### New Files

| File | Purpose |
|------|---------|
| `hooks/useReviewCountsRealtime.ts` | Real-time review counts (5s polling) |
| `hooks/useReviewUndo.ts` | Per-tab undo stack (last 3 actions) |
| `components/layout/SidebarBadge.tsx` | Badge component |
| `components/review/AIBatchPreview.tsx` | Optional AI preview modal (deferred) |
| `components/review/ReviewSummaryCards.tsx` | Summary stat cards |
| `components/review/ReviewCard.tsx` | Unified review card |
| `components/review/ReviewBulkActionsBar.tsx` | Bulk actions bar |
| `components/review/ReviewEmptyState.tsx` | Empty state component |
| `components/review/VocabularyReviewTab.tsx` | Vocab review tab |
| `components/review/AIReviewTab.tsx` | AI suggestions tab |
| `components/review/DataReviewTab.tsx` | Data review tab |
| `pages/ReviewCenterPage.tsx` | Main review page |
| `components/review/index.ts` | Barrel export |

### Modified Files

| File | Changes |
|------|---------|
| `components/layout/Sidebar.tsx` | Add badge, rename item |
| `App.tsx` | Update routes |
| `hooks/useAudit.ts` | Add count queries (if needed) |
| `components/audit/ImageReviewTab.tsx` | Fix API, move to review/ |

### Deleted Files

| File | Reason |
|------|--------|
| `pages/ReviewQueuePage.tsx` | Merged into ReviewCenterPage |

---

## Part 6: Visual Design Tokens

### Colors

```css
/* Review States */
--review-pending: var(--metal-ar);        /* Silver - pending */
--review-approved: var(--success);         /* Green - approved */
--review-rejected: var(--text-tertiary);   /* Gray - rejected */

/* Confidence Levels */
--confidence-high: var(--success);         /* >90% */
--confidence-medium: var(--caution);       /* 70-90% */
--confidence-low: var(--error);            /* <70% */
--confidence-none: var(--text-tertiary);   /* No match */

/* Card States */
--card-selected-bg: hsl(217, 91%, 97%);    /* Light blue bg */
--card-selected-border: var(--primary);    /* Blue border */
```

### Spacing

```css
/* Review Layout */
--review-page-padding: 24px;
--review-card-gap: 12px;
--review-section-gap: 24px;

/* Card Internal */
--review-card-padding: 16px;
--review-card-radius: 8px;
```

### Typography

```css
/* Review Typography */
--review-title: 24px / 1.2 / 600;          /* Page title */
--review-tab: 14px / 1.4 / 500;            /* Tab labels */
--review-card-title: 16px / 1.3 / 500;     /* Coin ID */
--review-field-label: 12px / 1.4 / 400;    /* "Field:" */
--review-field-value: 14px / 1.4 / 400;    /* Actual value */
--review-mono: 13px / 1.4 / 400 / mono;    /* Raw values */
```

---

## Part 7: Interaction Patterns

### 7.1 Keyboard Navigation

| Key | Context | Action |
|-----|---------|--------|
| `j` | Any tab | Select next item |
| `k` | Any tab | Select previous item |
| `Space` | Item focused | Toggle selection |
| `Enter` | Item focused | Open coin detail |
| `a` | Items selected | Approve all selected |
| `r` | Items selected | Reject all selected |
| `Escape` | Items selected | Clear selection |
| `1-4` | Any | Switch to tab 1-4 |
| `?` | Any | Show keyboard help |

### 7.2 Mouse Interactions

| Element | Click | Double-click | Hover |
|---------|-------|--------------|-------|
| Card | Toggle select | Open coin | Elevate shadow |
| Checkbox | Toggle select | - | - |
| Approve btn | Approve item | - | Green highlight |
| Reject btn | Reject item | - | Red highlight |
| View link | Open in new tab | - | Underline |
| Tab | Switch tab | - | Subtle bg |
| Summary card | Switch to tab | - | Elevate |

### 7.3 Touch Interactions

| Gesture | Action |
|---------|--------|
| Tap card | Toggle select |
| Long press | Show actions menu |
| Swipe left | Reject |
| Swipe right | Approve |
| Pull down | Refresh |

---

## Part 8: API Integration

### 8.1 Required Endpoints

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v2/vocab/review` | GET | List vocab items | ✅ Working |
| `/api/v2/vocab/review/{id}/approve` | POST | Approve vocab | ✅ Working |
| `/api/v2/vocab/review/{id}/reject` | POST | Reject vocab | ✅ Working |
| `/api/v2/llm/review` | GET | List LLM suggestions | ✅ Working |
| `/api/v2/llm/review/{id}/dismiss` | POST | Dismiss LLM | ✅ Working |
| `/api/v2/llm/review/{id}/accept` | POST | Accept LLM | ⚠️ To verify |
| `/api/v2/review/counts` | GET | Get all counts | ❌ To create (CRITICAL - Phase 1) |

### 8.2 New Endpoint: Review Counts

**Recommended:** Create a single endpoint that returns all review counts.

```
GET /api/v2/review/counts

Response:
{
  "vocabulary": 2,
  "ai": 8,
  "images": 0,
  "data": 0,
  "total": 10
}
```

This avoids multiple API calls from the sidebar badge.

---

## Part 9: Success Metrics

### 9.1 User Experience Goals

| Metric | Current | Target |
|--------|---------|--------|
| Time to find review items | ~30s (navigate to 2 pages) | <5s (badge visible) |
| Items reviewed per minute | ~5 | ~15 (keyboard shortcuts) |
| Navigation clicks to review | 3-4 | 1 (sidebar badge) |
| Cognitive load (tabs) | 6 tabs | 4 tabs |

### 9.2 Technical Goals

| Metric | Target |
|--------|--------|
| First contentful paint | <1s |
| Tab switch time | <100ms |
| Badge count update | <500ms |
| Bulk action (10 items) | <2s |

---

## Part 10: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Mock data shows empty UI | High | Medium | Add realistic placeholder text |
| Badge causes sidebar layout shift | Medium | Low | Reserve space always |
| Keyboard shortcuts conflict | Low | Medium | Audit existing shortcuts |
| Mobile layout breaks | Medium | Medium | Test responsive breakpoints |
| API count endpoint missing | High | High | Add backend endpoint first |

---

## Appendix A: Mockups Reference

See wireframes in Part 3 of this document.

## Appendix B: Component API Reference

See Props interfaces in Part 3 of this document.

## Appendix C: Related Documentation

- `design/CoinStack Design System v3.0.md` - Design tokens
- `docs/ai-guide/11-FRONTEND-COMPONENTS.md` - Component specs
- `docs/ai-guide/07-API-REFERENCE.md` - API endpoints

---

**Document Status:** Ready for Implementation

**Next Steps:**
1. ✅ Plan reviewed and feedback incorporated
2. Create backend `/api/v2/review/counts` endpoint (Phase 1)
3. Begin Phase 1 implementation

---

## Part 11: Feedback Integration

### Accepted Improvements

1. **Real-Time Updates**: Changed from 30s to 5s polling (`refetchInterval: 5000`)
2. **Undo Stack**: Per-tab undo (last 3 actions) with toast notifications
3. **Priority Sorting**: Default sort by confidence ASC, Smart Sort button
4. **Contextual Help**: Tooltips for confidence badges and field labels
5. **AI Batch Preview**: Optional "Preview Selection" button (deferred, not automatic)
6. **Auto-Approve High-Conf**: Single-click bulk approve for 95%+ confidence items

### Revised Time Estimates

| Phase | Original | Revised | Notes |
|-------|----------|---------|-------|
| Phase 1 | 4h | 4h | No change |
| Phase 2 | 3h | 5h | +2h (undo + optional preview) |
| Phase 3 | 1h | 1h | No change |
| Phase 4 | 1h | 1h | No change |
| Phase 5 | 1h | 1h | No change |
| **Total** | **10h** | **12h** | **+2h** |

**Status**: ✅ Ready for implementation
