<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# CoinStack Design System v3.0

**Complete Specification + AI Assistant Guidelines**

**Status**: Production-ready, cohesive, implementable.[^1][^2][^3]

***

## 1. Core Principles (AI Must Enforce)

### **P1: Information Density First**

- Every pixel serves data density or comparison.
- Prioritize text over imagery (image: 35–40% of card space max).
- Never use decorative elements; all visuals encode data.


### **P2: Numismatic Hierarchy**

```
1. Identity: Ruler + Category (what coin)
2. Type: Denomination + Mint + Date + Metal (which coin)
3. Condition: Grade + Rarity (quality)
4. Reference: Catalog + Notes (authenticity)
5. Financials: Value + Paid + Performance (worth)
```

**AI Rule**: Always order components this way. Never bury grade/rarity.

### **P3: Color Discipline**

- **4 accent systems only**: Category, Metal, Grade, Rarity.
- Neutral base (80% of screen).
- One strong color per text line (metal badge + neutral grade pill, etc.).


### **P4: Component Consistency**

- List, card, detail, dashboard use identical badges/chips/typography.
- Zoom-in, not mode-switch.

***

## 2. Color Tokens (Copy-Paste Ready)

```css
/* ═══════════════════════════════════════════════════════════════ */
/* COINSTACK DESIGN SYSTEM v3.0 - FINAL TOKENS */
/* ═══════════════════════════════════════════════════════════════ */

/* Neutrals */
:root {
  --bg-app: #050814;           /* Deep navy-charcoal */
  --bg-elevated: #0B1020;
  --bg-card: #0F1526;
  --bg-hover: #1A1F35;
  
  --text-primary: #F5F5F7;
  --text-secondary: #D1D5DB;
  --text-muted: #9CA3AF;
  --text-ghost: #6B7280;
  
  --border-subtle: rgba(148, 163, 184, 0.18);
  --border-strong: rgba(148, 163, 184, 0.40);
  --border-glow: rgba(148, 163, 184, 0.10);
}

/* Category Accents (4px left border + chips) */
--cat-republic: #DC2626;     /* Deep red */
--cat-imperial: #7C3AED;     /* Imperial purple */
--cat-provincial: #2563EB;   /* Blue */
--cat-greek: #16A34A;        /* Olive */

/* Metals (from your spec, unchanged) */
--metal-au: #FFD700;         /* Gold */
--metal-ag: #C0C0C0;         /* Silver */
--metal-cu: #CD7F32;         /* Copper */
--metal-ae: #8B7355;         /* Bronze */
--metal-or: #C9A227;         /* Orichalcum */
--metal-el: #E8D882;         /* Electrum */
--metal-bi: #9A9A8E;         /* Billon */
--metal-po: #5C5C52;         /* Potin */
--metal-pb: #6B6B7A;         /* Lead */
--metal-br: #B5A642;         /* Brass */

/* Grade (Temperature: Cold→Hot) */
--grade-poor: #3B82F6;       /* Blue */
--grade-fair: #10B981;       /* Green */
--grade-vf: #F59E0B;         /* Yellow */
--grade-ef: #EF4444;         /* Red */
--grade-ms: #DC2626;         /* Deep red */

/* Rarity (Gemstone, desaturated) */
--rarity-common: #D1D5DB;    /* Gray */
--rarity-scarce: #8B5CF6;    /* Amethyst */
--rarity-rare1: #06B6D4;     /* Aquamarine */
--rarity-rare2: #10B981;     /* Emerald */
--rarity-rare3: #F59E0B;     /* Topaz */
--rarity-unique: #EF4444;    /* Ruby */

/* Value Performance */
--perf-positive: #10B981;    /* Green */
--perf-negative: #EF4444;    /* Red */
--perf-neutral: #9CA3AF;     /* Gray */
}
```

**AI Rule**: Never invent new colors. Use these tokens only. Metals unchanged from your v2 spec.[^2]

***

## 3. Typography Scale

```css
/* Typography */
--font-family-primary: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
--font-size-xs: 12px;    /* Microcopy, paid amounts */
--font-size-sm: 13px;    /* Denom, mint, dates */
--font-size-md: 15px;    /* References, value */
--font-size-lg: 17px;    /* Ruler names */
--font-size-xl: 20px;    /* Section headers */
--font-size-xxl: 24px;   /* Page titles */

/* Weights */
--font-weight-light: 300;
--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;
```


***

## 4. Component Specifications

### 4.1 **Category Bar** (4px left accent)

```css
.category-bar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  border-radius: 8px 0 0 8px;  /* Match card's rounded corners */
  background: var(--cat-republic); /* or imperial, provincial, greek */
  z-index: 1;
}
```

**Usage**: Full-height left edge of every card, table row, dashboard tile.
**Important**: Border-radius must match the parent card's left corners to prevent clipping.

### 4.2 **Metal Badge** (Compact v3.1)

```css
.metal-badge {
  font-size: 8px;
  font-weight: 700;
  padding: 2px 5px;
  border-radius: 2px;
  text-transform: uppercase;
  color: var(--metal-ag);           /* Metal color */
  background: var(--metal-ag-subtle); /* Subtle background */
}
.metal-badge:hover {
  box-shadow: 0 2px 8px var(--metal-glow-color);
}
```

**Content**: `AU`, `AR`, `AE`, `BI` (element abbreviation, uppercase).

### 4.3 **Grade Badge** (Outline style)

```css
.grade-badge {
  font-size: 8px;
  font-weight: 700;
  padding: 2px 5px;
  border-radius: 2px;
  border: 1px solid var(--grade-vf);  /* Temperature color */
  color: var(--grade-vf);
  background: transparent;
}
```

**Content**: `VF`, `XF`, `AU`, `MS` etc.

### 4.4 **Certification Badge** (Filled style)

```css
.cert-badge {
  font-size: 8px;
  font-weight: 700;
  padding: 2px 5px;
  border-radius: 2px;
  text-transform: uppercase;
  color: #fff;
  background: var(--cert-ngc);  /* or --cert-pcgs */
}
```

**Content**: `NGC`, `PCGS`.

### 4.5 **Rarity Dot**

```css
.rarity-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--rarity-rare2);  /* Gemstone color */
}
```

### 4.6 **Badge Row Order** (Right-aligned)

```
[Certification] [Grade] [Metal] [Rarity●]
```

- Show certification only if coin is slabbed (NGC/PCGS)
- Always show grade and metal
- Rarity dot only if rarity data exists


### 4.5 **Coin Card** (Horizontal Layout - v3.1)

```
┌────────────────────────────────────────────────────────────────────┐
│ [4px]  ┌────────────┐  Ruler (15px bold)           Year (12px)     │
│  Cat   │            │  ─────────────────────────────────────────   │
│  Bar   │  160×160   │  OBV: LEGEND TEXT...                         │
│        │  Coin Img  │  REV: LEGEND TEXT...                         │
│        │  (3D flip) │  Reference (9px mono)                        │
│        │            │  ─────────────────────────────────────────   │
│        └────────────┘  $384 ↑12%        [NGC] [VF] [AR] [●]        │
└────────────────────────────────────────────────────────────────────┘
```

**Exact dimensions (v3.1 - January 2026)**:

- Card: `min-width: 360px`, `height: 170px` (desktop), `100%` width (mobile)
- Image: `160px × 160px` (square, with 3D flip on hover)
- Category bar: `4px` wide, `border-radius: 8px 0 0 8px` (matches card corners)
- Content padding: `12px 14px 12px 16px` (desktop), `10px` (tablet)
- Badge row: compact 8px font, 3px gap between badges
- Mobile: vertical stack with 180px tall image, 380px min-height card

***

## 5. Layout Patterns

### 5.1 **List View** (Your table is perfect, just style it)

```
| Category Bar | Checkbox | Thumbnail | Ruler | Reference | Denom | Mint | Metal | Date | Grade | Rarity | Value |
```

- 12 columns, responsive to 8 on mobile.
- Sortable headers with subtle underlines.


### 5.2 **Dashboard Tiles**

- 2–3 column grid.
- Each tile has category bar + identical badge system.
- Charts use neutral lines + accent fills (category/metal colors).


### 5.3 **Detail View**

```
Left (35%):  Images (obverse/reverse tabs, 260px max)
Right (65%): Cards (identity, condition, references, market)
```


***

## 6. AI Assistant Design Guidelines

**When generating UI code, components, or layouts for CoinStack:**

### **MUST DO:**

```
1. Use ONLY the tokens above (no new colors/fonts/sizes)
2. Follow exact hierarchy: Identity → Type → Condition → Reference → Financials
3. Every card MUST have: category bar + metal badge + grade badge
4. Image: 160×160px square with 3D flip animation on hover
5. Card min dimensions: 360px wide × 170px tall (desktop)
6. Badges: 8px font, 2px 5px padding, compact row
7. Badge order (right-aligned): [Cert] [Grade] [Metal] [Rarity●]
8. Hover: subtle lift (-2px) + enhanced shadow
```


### **NEVER DO:**

```
❌ Giant hero images dominating cards (max 160px)
❌ More than 4 accent colors in one view
❌ Decorative gradients/shadows (only data-encoding visuals)
❌ Inconsistent badge styles across pages
❌ Burying grade/rarity below fold
❌ Pure black (#000) or pure white (#fff) — always use tokens
❌ Clipped category bars (use matching border-radius)
❌ Overlapping cards on resize (use proper grid gaps)
```


### **Component Checklist** (AI must verify):

```
□ Category bar (4px left, 8px 0 0 8px radius)?
□ Metal badge (8px font, uppercase)?
□ Grade badge (outline style, temperature color)?
□ Certification badge (filled, if slabbed)?
□ Rarity dot (6px, gemstone color)?
□ Price + performance on same line?
□ Image 160×160px with flip effect?
□ Legends section (OBV/REV labels)?
```


***

## 7. Implementation Priority

```
Week 1: Copy CSS tokens → Refactor coin cards → Table styling
Week 2: Dashboard tiles → Detail page alignment
Week 3: Mobile responsiveness → Animations
```

**This system unifies all your existing guidelines into one cohesive spec.** Drop the CSS tokens into your root and every page will instantly feel consistent.

***

## 8. Changelog

### v3.1 (January 2026)

**Card Layout**:
- Reduced card dimensions: 360×170px (from 420×180px)
- Square images: 160×160px (from 180×180px)
- Category bar radius: 8px 0 0 8px (matches card corners)
- Content padding reduced: 12-16px (from 16-20px)

**Badges**:
- Compact badges: 8px font (from 9px), 2px 5px padding (from 3px 8px)
- Badge order: [Certification] [Grade] [Metal] [Rarity●]
- Grade badge: outline style (border only, transparent bg)
- Certification badge: filled style (solid background)
- Metal badge: subtle background with text color
- 3px gap between badges (from 4px)

**Legends Section**:
- Compact OBV/REV labels (7px)
- Legend text: 10px Cinzel font
- 2px gap between lines (from 5px)
- Section uses flex: 1 to fill available space

**Bottom Row**:
- Price: 16px (from 18px)
- Performance: inline arrow (↑12%) instead of bordered box
- 6px gap (from 8px)
<span style="display:none">[^10][^4][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: coinstack_list_view.html

[^2]: CoinStack_Design_System-v2.md

[^3]: coinstack_unified_colors.html

[^4]: collection-v1.csv

[^5]: image.jpg

[^6]: CoinStack_-Complete-LLM-Strategy-Guide.md

[^7]: CoinStack_Detail_Numismatic.md

[^8]: CoinStack_Design_System.md

[^9]: coinstack_numismatic_detail.html

[^10]: coinstack_statistics_v2.html

