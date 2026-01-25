# CoinStack V2: Complete Design Overhaul Specification

**Status**: 🚀 RADICAL REDESIGN - Clean Slate Approach
**Date**: 2026-01-25
**Priority**: CRITICAL - Blocks Feature Development

---

## 🎯 Executive Summary

Complete frontend redesign to support V2 backend with information-rich, modular, scalable design focused on ancient numismatics. **Breaking changes** - prioritizing optimal design over backward compatibility.

### Core Problems Solved
- ❌ **Current**: Broken UI/UX from V2 backend refactor
- ❌ **Current**: Inconsistent design language
- ❌ **Current**: Poor information density
- ❌ **Current**: Generic coin collector aesthetic (not numismatic-focused)

### New Design Philosophy
- ✅ **Information density first** - Every pixel serves data or comparison
- ✅ **Numismatic hierarchy** - Identity → Type → Condition → Reference → Financials
- ✅ **Color discipline** - 4 semantic accent systems only
- ✅ **Component consistency** - Same tokens across all views
- ✅ **Ancient numismatics focus** - Historical accuracy in colors and metaphors

---

## 📐 Design System v3.0 Foundation

### Core Principles

#### P1: Information Density First
- Prioritize text over imagery (image: 35-40% of card space max)
- No decorative elements - all visuals encode data
- Dense but readable (min 13px body text)

#### P2: Numismatic Hierarchy (ALWAYS follow this order)
```
1. Identity:   Ruler + Category (what coin is this?)
2. Type:       Denomination + Mint + Date + Metal (which specific coin?)
3. Condition:  Grade + Rarity (how good is it?)
4. Reference:  Catalog + Notes (where documented?)
5. Financials: Value + Paid + Performance (what's it worth?)
```

#### P3: Color Discipline
- **4 accent systems ONLY**: Category, Metal, Grade, Rarity
- Neutral base (80% of screen)
- One strong color per text line
- Never mix accent systems on same element

#### P4: Component Consistency
- List, card, detail, dashboard use identical badges/chips/typography
- "Zoom-in, not mode-switch" - same components, different density

---

## 🎨 Complete Color Token System

### Neutrals (80% of UI)
```css
:root {
  /* Backgrounds */
  --bg-app: #050814;           /* Deep navy-charcoal (main canvas) */
  --bg-elevated: #0B1020;      /* Cards one level up */
  --bg-card: #0F1526;          /* Individual cards */
  --bg-hover: #1A1F35;         /* Hover state */

  /* Text */
  --text-primary: #F5F5F7;     /* Headers, primary content */
  --text-secondary: #D1D5DB;   /* Body text, labels */
  --text-muted: #9CA3AF;       /* Subtle info, timestamps */
  --text-ghost: #6B7280;       /* Disabled, placeholders */

  /* Borders */
  --border-subtle: rgba(148, 163, 184, 0.18);
  --border-strong: rgba(148, 163, 184, 0.40);
  --border-glow: rgba(148, 163, 184, 0.10);
}
```

### Category Colors (9 historical periods)
```css
/* Era-appropriate colors with historical significance */
--cat-republic: #DC2626;      /* Terracotta/Roman brick red (509-27 BCE) */
--cat-imperial: #7C3AED;      /* Tyrian purple - Emperor's color (27 BCE - 284 CE) */
--cat-provincial: #2563EB;    /* Aegean blue (Greek Imperial) */
--cat-late: #D4AF37;          /* Byzantine gold (284-491 CE) */
--cat-greek: #16A34A;         /* Olive - Mediterranean (pre-Roman) */
--cat-celtic: #27AE60;        /* Forest green (Northern Europe) */
--cat-judaea: #C2956E;        /* Desert sand/stone */
--cat-eastern: #17A589;       /* Persian turquoise (Parthian/Sasanian) */
--cat-byzantine: #922B21;     /* Imperial crimson (491+ CE) */
```

**Usage**: 4px left border on ALL cards, rows, tiles

### Metal Colors (10 metals - chemically derived)
```css
/* Precious Metals (warm tones, high value) */
--metal-au: #FFD700;          /* Gold (Au, Z=79) - d-orbital transitions */
--metal-el: #E8D882;          /* Electrum (Au+Ag natural alloy) - pale gold */
--metal-ag: #C0C0C0;          /* Silver (Ag, Z=47) - cool white */

/* Base Metals (earth tones, lower value) */
--metal-or: #C9A227;          /* Orichalcum (Roman "mountain copper") - GOLDEN brass */
--metal-br: #B5A642;          /* Brass (Cu+Zn) - yellow-gold */
--metal-cu: #CD7F32;          /* Copper (Cu, Z=29) - reddish-brown */
--metal-ae: #8B7355;          /* Aes (generic bronze) - muted patina */

/* Debased/Alloy (gray tones, crisis coinage) */
--metal-bi: #9A9A8E;          /* Billon (Ag+Cu debased) - grayish */
--metal-po: #5C5C52;          /* Potin (Cu+Sn+Pb Celtic) - dark gray-brown */
--metal-pb: #6B6B7A;          /* Lead (Pb, Z=82) - blue-gray */
```

**Usage**: Badge with element symbol (Au, Ag, Æ, etc.) + shimmer hover on precious metals

### Grade Colors (6 tiers - temperature metaphor)
```css
/* Cold (poor) → Hot (mint) progression */
--grade-poor: #3B82F6;        /* ❄️ Freezing blue (P/FR/AG grades) */
--grade-good: #64D2FF;        /* 🧊 Cold teal (G/VG) */
--grade-fine: #34C759;        /* 🌡️ Neutral green (F/VF) */
--grade-ef: #FFD60A;          /* ☀️ Warm yellow (EF/XF) */
--grade-au: #FF9F0A;          /* 🔥 Hot orange (AU) */
--grade-ms: #FF6B6B;          /* 🔥 Fire red (MS/FDC) */

/* Certification Services (brand colors) */
--grade-ngc: #1A73E8;         /* NGC blue */
--grade-pcgs: #2E7D32;        /* PCGS green */
```

**Usage**: Rounded pill badge with grade text, temperature color = quality

### Rarity Colors (6 tiers - gemstone metaphor)
```css
/* Gemstone-inspired, increasing value/intensity */
--rarity-c: #D1D5DB;          /* Quartz (neutral, abundant) - Common */
--rarity-s: #8B5CF6;          /* Amethyst (first tier interesting) - Scarce */
--rarity-r1: #06B6D4;         /* Sapphire (genuinely uncommon) - Rare */
--rarity-r2: #10B981;         /* Emerald (significant scarcity) - Very Rare */
--rarity-r3: #EF4444;         /* Ruby (exceptional) - Extremely Rare */
--rarity-u: #FFFFFF;          /* Diamond (one-of-a-kind) - Unique */
```

**Usage**: Dot indicator + code (●R2), with tooltip showing gemstone name

### Performance Colors (3 states)
```css
--perf-positive: #10B981;     /* Green - profit */
--perf-negative: #EF4444;     /* Red - loss */
--perf-neutral: #9CA3AF;      /* Gray - no change */
```

---

## 📏 Typography Scale

```css
:root {
  /* Font Family */
  --font-family-primary: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;

  /* Sizes (6 tiers) */
  --font-size-xs: 12px;       /* Microcopy, paid amounts, timestamps */
  --font-size-sm: 13px;       /* Denom, mint, dates, body text */
  --font-size-md: 15px;       /* References, value, section labels */
  --font-size-lg: 17px;       /* Ruler names, card headers */
  --font-size-xl: 20px;       /* Section headers, dashboard titles */
  --font-size-xxl: 24px;      /* Page titles, hero text */

  /* Weights */
  --font-weight-light: 300;
  --font-weight-normal: 400;
  --font-weight-medium: 500;  /* Most common - badges, labels */
  --font-weight-semibold: 600;/* Headers */
  --font-weight-bold: 700;    /* Emphasis, values */
}
```

**Rules**:
- Ruler names: 17px semibold
- Denomination/mint/date: 13px regular
- References: 12px monospace
- Values: 15px bold
- Microcopy: 12px regular

---

## 🧩 Core Component Specifications

### 1. Category Bar (Signature Element)
```css
.category-bar {
  width: 4px;
  height: 100%;
  border-radius: 2px;
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  background: var(--cat-imperial); /* or republic, etc. */
}
```
**CRITICAL**: Must be on EVERY card, row, tile, modal. No exceptions.

### 2. Metal Badge
```tsx
// Element symbol style
<div className="metal-badge">
  {symbol} {/* Au, Ag, Æ, Cu, etc. */}
</div>

// CSS
.metal-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  background: var(--metal-au-subtle);
  color: var(--metal-au-text);
  border: 1px solid var(--metal-au-border);
  font-family: monospace;
}

/* Precious metal shimmer on hover */
.metal-badge.precious:hover {
  box-shadow: 0 2px 8px var(--metal-au-glow);
}
```

**Variants**:
- `xs`: 16px × 16px (table cells)
- `sm`: 20px × 20px (cards)
- `md`: 24px × 24px (detail views)
- `lg`: 32px × 32px (hero sections)

### 3. Grade Pill
```css
.grade-pill {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  background: var(--grade-vf);  /* Temperature color */
  color: #000;                  /* Always black text on colored bg */
  border: 1px solid rgba(0,0,0,0.1);
}
```

**Grade Mapping**:
- Poor/Fair/AG → Blue (cold)
- Good/VG → Teal
- Fine/VF → Green (neutral)
- EF/XF → Yellow (warm)
- AU → Orange (hot)
- MS/FDC → Red (fire)

### 4. Rarity Dot
```css
.rarity-dot {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 500;
}

.rarity-dot::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--rarity-r2);  /* Gemstone color */
}
```

**Content**: `●R2` with tooltip: "Very Rare (Emerald)"

### 5. Coin Card (Fixed Spec)
```
┌─────────────────────────────────────────────────────┐
│ [4px Category Bar]                                   │
│                                                       │
│  ┌──────────┐  Antoninus Pius          [Imperial]   │
│  │          │  Denarius · Rome · 138 AD              │
│  │  Image   │  [Au] [VF] ●R2                        │
│  │  140×140 │  RIC III 61 · Rome mint               │
│  │          │  $384 → $320 ▲ +20%                   │
│  └──────────┘                                        │
│                                                       │
└─────────────────────────────────────────────────────┘
```

**Dimensions**:
- Total: 280px × 380px (fixed)
- Image: 140px × 140px (left column)
- Text: 220px width (right column, 5 lines min)
- Padding: 16px all sides
- Gap: 12px between image and text

**MUST HAVE** on every card:
1. Category bar (4px left)
2. Thumbnail/image (constrained to 140px)
3. Ruler name (17px semibold)
4. Denomination + Mint + Date (13px)
5. Metal badge + Grade pill + Rarity dot
6. Reference (12px monospace)
7. Value + Paid + Performance (15px)

### 6. Table Row (12 columns)
```
| Cat Bar | ☑ | 🖼️ | Ruler | Reference | Denom | Mint | Metal | Date | Grade | Rarity | Value |
```

**Column Widths** (optimized for 1920px):
- Category bar: 4px (visual only)
- Checkbox: 40px
- Thumbnail: 48px
- Ruler: 160px (name + reign)
- Reference: 120px (RIC/Crawford)
- Denomination: 100px
- Mint: 80px
- Metal: 48px (badge)
- Date: 100px
- Grade: 56px (pill)
- Rarity: 56px (dot + code)
- Value: 120px (current + paid + %)

**Row Height**: 56px (comfortable, scannable)

**Hover State**: Slide right 4px + intensify category border + bg lighten

---

## 🎨 Layout Patterns

### Pattern 1: Grid View (Primary)
```
Desktop (1920px):  5 columns × 280px cards = 1400px + gaps
Tablet (1024px):   3 columns
Mobile (375px):    1 column (full width)
```

**Responsive Breakpoints**:
- `xl`: 1440px+ → 5 columns
- `lg`: 1024px-1439px → 4 columns
- `md`: 768px-1023px → 3 columns
- `sm`: 640px-767px → 2 columns
- `xs`: <640px → 1 column

### Pattern 2: Table View (Power Users)
```
Desktop:  All 12 columns visible
Tablet:   Hide Mint, Date (keep core columns)
Mobile:   Not recommended (switch to cards)
```

**Sticky Header**: Always visible when scrolling

### Pattern 3: Detail View (35/65 Split)
```
┌──────────────┬─────────────────────────────────────┐
│              │  Identity Card (6-field grid)       │
│              ├─────────────────────────────────────┤
│  Images      │  Condition Card (grade/rarity/specs)│
│  (35%)       ├─────────────────────────────────────┤
│              │  References Card (RIC, etc.)        │
│  Tabs:       ├─────────────────────────────────────┤
│  - Obverse   │  Market Card (value/comps)          │
│  - Reverse   ├─────────────────────────────────────┤
│  - Line      │  Provenance Card (timeline)         │
│              │                                     │
└──────────────┴─────────────────────────────────────┘
```

**Left (35%)**:
- Large image viewer (400×320px max)
- Image tabs (obverse/reverse/line drawing)
- Quick stats (weight, diameter, die axis)
- Metal badge overlay

**Right (65%)**:
- 5 data cards stacked vertically
- Each card has category bar
- Consistent spacing (24px between cards)

### Pattern 4: Dashboard (Tiles)
```
Row 1:  [Portfolio Value] [Category Distribution] [Average Grade]
Row 2:  [Metal Pie Chart] [Grade Histogram]
Row 3:  [Performance Line Chart - Full Width]
```

**Tile Specs**:
- Min height: 200px
- Category bar on left
- Sparklines for trends
- Hover lift effect
- Click to drill down

---

## 🎬 Interaction Patterns

### Hover States
```css
/* Cards */
.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px var(--category-color)/20;
}

/* Table rows */
.table-row:hover {
  transform: translateX(4px);
  border-left-color: var(--category-color);
  background: var(--bg-hover);
}

/* Metal badges (precious only) */
.metal-badge.precious:hover {
  box-shadow: 0 2px 8px var(--metal-glow);
  transform: scale(1.05);
}
```

### Selection States
```css
.selected {
  background: var(--cat-imperial)/10;
  border: 2px solid var(--cat-imperial);
}
```

### Loading States
```tsx
// Skeleton card
<div className="skeleton">
  <div className="category-bar animate-pulse" />
  <div className="skeleton-image" />
  <div className="skeleton-text-line w-3/4" />
  <div className="skeleton-text-line w-1/2" />
</div>
```

### Empty States
```tsx
// No coins found
<div className="empty-state">
  <div className="coin-silhouette" /> {/* Subtle outline */}
  <h3>No coins match your filters</h3>
  <button>Clear Filters</button>
</div>
```

---

## 📱 Responsive Strategy

### Mobile-First Approach
```
1. Design for 375px first (iPhone SE)
2. Scale up to 768px (tablet)
3. Optimize for 1920px (desktop)
```

### Mobile Specific
- Bottom tab navigation (5 items)
- Sheet modals for filters
- Swipe gestures (card dismiss, image gallery)
- Touch targets min 44×44px
- Simplified animations (battery/performance)

### Tablet Specific
- Hybrid navigation (top + bottom)
- 2-3 column grids
- Collapsible sidebar (overlay)
- Landscape-optimized detail view

---

## 🚀 Implementation Roadmap

### Phase 1: Foundation (Week 1) - CRITICAL
- [ ] Create `design-tokens.css` with all color/typography tokens
- [ ] Configure Tailwind with extended palette
- [ ] Build core components: MetalBadge, GradePill, RarityDot, CategoryBar
- [ ] Create Storybook for component library
- [ ] Document token usage patterns

### Phase 2: Core Views (Weeks 2-3) - HIGH PRIORITY
- [ ] Rebuild CoinCard with new spec (280×380px)
- [ ] Rebuild CoinTable (12 columns, sticky header)
- [ ] Build CoinDetail (35/65 split)
- [ ] Build Navigation (header + sidebar)
- [ ] Test responsive behavior across breakpoints

### Phase 3: Advanced Features (Week 4) - MEDIUM PRIORITY
- [ ] Build Dashboard with charts (Chart.js integration)
- [ ] Implement advanced filters (metal chips, year histogram)
- [ ] Add search autocomplete
- [ ] Build bulk actions toolbar
- [ ] Implement saved views/presets

### Phase 4: Polish (Week 5) - MEDIUM PRIORITY
- [ ] Add animations (hover, transitions, micro-interactions)
- [ ] Optimize loading states (skeletons, progressive enhancement)
- [ ] Add empty states and error handling
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] Performance optimization (lazy loading, virtual scroll)

### Phase 5: Documentation (Week 6) - LOW PRIORITY
- [ ] Complete Storybook with all states
- [ ] Write developer documentation
- [ ] Create Figma design file
- [ ] Record demo videos
- [ ] Migration guide from V1

---

## ✅ Design Checklist (Use for Code Review)

Every component MUST have:
- [ ] Category bar (4px left) in correct historical color
- [ ] Metal badge with element symbol (Au, Ag, Æ, etc.)
- [ ] Grade pill with temperature color (blue → red)
- [ ] Rarity dot with gemstone color + code (●R2)
- [ ] Value with paid + performance percentage
- [ ] Image constrained to max 140px height (cards) or 40px (table)
- [ ] Ruler text at 17px semibold
- [ ] Consistent spacing (padding, gaps) using tokens
- [ ] Hover state with category-colored glow
- [ ] Responsive behavior defined for all breakpoints

Never allowed:
- ❌ Giant hero images dominating cards
- ❌ More than 4 accent colors in one view
- ❌ Decorative gradients/shadows without data meaning
- ❌ Inconsistent badge styles across pages
- ❌ Burying grade/rarity below fold
- ❌ Pure black (#000) or pure white (#fff) - always use tokens
- ❌ Inventing new colors outside the token system

---

## 📚 Reference Files

**Design System**:
- `/design/CoinStack Design System v3.0.md` - Master specification
- `/design/v1/CoinStack_Design_System-v2.md` - Historical reference

**Page Designs**:
- `/design/CoinStack Frontpage + Grid Design.md` - Grid layout spec
- `/design/CoinStack Coin Table Design.md` - Table column spec
- `/design/CoinStack Individual Coin Page Design.md` - Detail page spec
- `/design/CoinStack Statistics Dashboard Design.md` - Dashboard spec

**V2 Backend Docs**:
- `/CLAUDE.md` - Backend architecture and patterns
- `/WEEK1_COMPLETE_SUMMARY.md` - Refactoring progress

---

## 🎯 Success Criteria

**Must Achieve**:
1. ✅ 100% token compliance (no arbitrary colors/sizes)
2. ✅ Category bar on every card/row/tile
3. ✅ Consistent badge system across all views
4. ✅ Numismatic hierarchy respected in all layouts
5. ✅ Image constraints enforced (max 40% card width)
6. ✅ Mobile-responsive (all breakpoints tested)
7. ✅ Lighthouse score > 90 (performance)
8. ✅ WCAG 2.1 AA accessibility
9. ✅ 60fps animations (no jank)
10. ✅ Comprehensive Storybook documentation

**Measures of Success**:
- Information density: 7+ data points per card (vs. 3-4 currently)
- Scan time: <2s to evaluate coin quality (grade/rarity visible immediately)
- Recognition: Instant category identification via color bar
- Consistency: Same component looks identical across grid/table/detail views

---

## 🚧 Migration Notes

### Breaking Changes (Intentional)
1. **Complete color system overhaul** - all existing color variables deprecated
2. **New component architecture** - no backward compatibility with V1 components
3. **Layout restructure** - card dimensions changed, grid columns changed
4. **Typography scale changes** - font sizes adjusted for better hierarchy
5. **Image constraints** - existing oversized images will be cropped

### Migration Strategy
1. Run both V1 and V2 designs in parallel (feature flag)
2. Migrate page by page (start with collection grid)
3. Provide theme toggle for users during transition (1 month)
4. Deprecate V1 components after 2 months
5. Remove V1 code after 3 months

### Rollback Plan
- Keep V1 components in `/components/legacy` for 3 months
- Feature flag `USE_V2_DESIGN` controls which version loads
- Quick rollback via environment variable if critical issues found

---

**Document Version**: 1.0
**Last Updated**: 2026-01-25
**Owner**: Frontend Team
**Review Cycle**: Weekly during implementation

---

**This specification is the single source of truth for all V2 frontend development.**
All code must comply with these standards. No exceptions without design team approval.
