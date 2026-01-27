# Design System v3.1 - AI Assistant Guide

> Complete design token reference and UI component specifications for CoinStack.
> **Last Updated**: January 2026 (v3.1)

---

## Quick Reference for AI

When implementing UI changes, follow these rules:

```
✅ ALWAYS use design tokens (CSS variables)
✅ ALWAYS follow numismatic hierarchy
✅ ALWAYS verify badge order: [Cert] [Grade] [Metal] [Rarity●]
✅ ALWAYS use 8px 0 0 8px radius for category bars
❌ NEVER use raw hex colors - use tokens
❌ NEVER exceed 160px for card images
❌ NEVER add decorative elements
```

---

## 1. Core Design Principles

### P1: Information Density First

- Every pixel serves data density or comparison
- Prioritize text over imagery (image: 35-40% of card space max)
- Never use decorative elements; all visuals encode data

### P2: Numismatic Hierarchy

Components MUST follow this order:

```
1. Identity    → Ruler + Category (what coin)
2. Type        → Denomination + Mint + Date + Metal (which coin)
3. Condition   → Grade + Rarity (quality)
4. Reference   → Catalog + Notes (authenticity)
5. Financials  → Value + Paid + Performance (worth)
```

### P3: Color Discipline

- **4 accent systems ONLY**: Category, Metal, Grade, Rarity
- Neutral base (80% of screen)
- One strong color per text line maximum

### P4: Component Consistency

- List, card, detail, dashboard use identical badges/chips/typography
- Zoom-in, not mode-switch

---

## 2. Color Tokens

### 2.1 Backgrounds & Text

```css
/* Backgrounds - Navy-charcoal theme */
--bg-app: #050814;        /* Main app background */
--bg-elevated: #0B1020;   /* Header, sidebar */
--bg-card: #0F1526;       /* Cards, panels */
--bg-hover: #1A1F35;      /* Hover states */

/* Text hierarchy */
--text-primary: #F5F5F7;   /* Main text */
--text-secondary: #D1D5DB; /* Supporting text */
--text-muted: #9CA3AF;     /* Tertiary text */
--text-ghost: #6B7280;     /* Disabled/hints */

/* Borders */
--border-subtle: rgba(148, 163, 184, 0.18);
--border-strong: rgba(148, 163, 184, 0.40);
```

### 2.2 Category Colors (Historical Accuracy)

```css
--cat-republic: #DC2626;    /* Roman Republic - Terracotta red */
--cat-imperial: #7C3AED;    /* Roman Imperial - Tyrian purple */
--cat-provincial: #2563EB;  /* Provincial - Aegean blue */
--cat-greek: #16A34A;       /* Greek - Olive green */
--cat-late: #D4AF37;        /* Late Roman - Byzantine gold */
--cat-byzantine: #922B21;   /* Byzantine - Imperial crimson */
--cat-celtic: #27AE60;      /* Celtic - Forest green */
--cat-judaea: #C2956E;      /* Judaea - Desert sand */
--cat-eastern: #17A589;     /* Eastern - Persian turquoise */
```

**Usage**: Category bar left edge + filter chips

### 2.3 Metal Colors

```css
--metal-au: #FFD700;  /* Gold */
--metal-ag: #C0C0C0;  /* Silver */
--metal-ae: #8B7355;  /* Bronze */
--metal-cu: #CD7F32;  /* Copper */
--metal-bi: #9A9A8E;  /* Billon */
--metal-or: #C9A227;  /* Orichalcum */
--metal-el: #E8D882;  /* Electrum */
--metal-po: #5C5C52;  /* Potin */
--metal-pb: #6B6B7A;  /* Lead */
--metal-br: #B5A642;  /* Brass */

/* Subtle backgrounds for badges */
--metal-au-subtle: rgba(255, 215, 0, 0.15);
--metal-ag-subtle: rgba(192, 192, 192, 0.15);
--metal-ae-subtle: rgba(139, 115, 85, 0.15);
/* ... etc for each metal */
```

### 2.4 Grade Colors (Temperature Scale)

Cold → Hot progression represents increasing quality:

```css
--grade-poor: #3B82F6;  /* Poor/Fair - Ice blue (❄️) */
--grade-good: #64D2FF;  /* Good/VG - Cold cyan (🧊) */
--grade-fine: #34C759;  /* Fine - Neutral green (🌡️) */
--grade-vf: #FFD60A;    /* VF - Warm yellow (☀️) */
--grade-ef: #FF9F0A;    /* EF/XF - Hot orange (🔥) */
--grade-au: #FF6B6B;    /* AU - Fire red (🔥🔥) */
--grade-ms: #DC2626;    /* MS/FDC - Deep red (💎) */

/* Certification services */
--cert-ngc: #1A73E8;    /* NGC blue */
--cert-pcgs: #2E7D32;   /* PCGS green */
```

### 2.5 Rarity Colors (Gemstone Scale)

```css
--rarity-common: #D1D5DB;   /* Common - Quartz (gray) */
--rarity-scarce: #8B5CF6;   /* Scarce - Amethyst (purple) */
--rarity-r1: #06B6D4;       /* R1 - Sapphire (cyan) */
--rarity-r2: #10B981;       /* R2 - Emerald (green) */
--rarity-r3: #F59E0B;       /* R3 - Topaz (amber) */
--rarity-unique: #EF4444;   /* Unique - Ruby (red) */
```

### 2.6 Performance Colors

```css
--perf-positive: #10B981;  /* Green - profit/increase */
--perf-negative: #EF4444;  /* Red - loss/decrease */
--perf-neutral: #9CA3AF;   /* Gray - no change */
```

### 2.7 Form Interaction Colors

Standardized feedback colors for data entry and AI population:

```css
/* Standard Text */
--text-input: var(--foreground);           /* User-entered / Committed */
--text-placeholder: var(--muted-foreground); /* Empty / Hint */

/* Tentative / Fetched Data */
--text-tentative: #C2410C;                 /* Orange-700 (Light) */
--text-tentative-dark: #FDBA74;            /* Orange-300 (Dark) */
--ring-tentative: rgba(249, 115, 22, 0.5); /* Orange-500/50 */
--bg-tentative: rgba(255, 247, 237, 0.1);  /* Orange-50/10 */
```

**Usage Rule**:
- **Gray**: Placeholder / Empty
- **White/Black**: User committed data / Current value
- **Orange**: AI-fetched or Auto-populated suggestions (Tentative)

---

## 3. Typography

### Font Scale

```css
--font-size-xs: 8px;    /* Badge text, microcopy */
--font-size-sm: 10px;   /* Legends, small labels */
--font-size-md: 12px;   /* Secondary text */
--font-size-base: 14px; /* Body text */
--font-size-lg: 15px;   /* Ruler names */
--font-size-xl: 17px;   /* Section headers */
--font-size-xxl: 20px;  /* Page titles */
```

### Font Weights

```css
--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;
```

### Special Typography

**Legends (Obverse/Reverse)**: Use Cinzel font for classical feel:
```css
font-family: "Cinzel", serif;
font-size: 10px;
color: var(--text-secondary);
```

**References**: Use monospace for catalog numbers:
```css
font-family: monospace;
font-size: 9px;
color: var(--text-muted);
```

---

## 4. Component Specifications

### 4.1 Category Bar

Left accent indicating coin category.

```css
.category-bar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  border-radius: 8px 0 0 8px;  /* MUST match card corners */
  background: var(--cat-imperial);
  z-index: 1;
}
```

**Critical**: Border-radius MUST match parent card's left corners to prevent clipping.

### 4.2 Metal Badge (v3.1)

```css
.metal-badge {
  font-size: 8px;
  font-weight: 700;
  padding: 2px 5px;
  border-radius: 2px;
  text-transform: uppercase;
  color: var(--metal-ag);
  background: var(--metal-ag-subtle);
}

.metal-badge:hover {
  box-shadow: 0 2px 8px var(--metal-glow-color);
}
```

**Content**: `AU`, `AR`, `AE`, `BI` (element abbreviation)

### 4.3 Grade Badge (Outline Style)

```css
.grade-badge {
  font-size: 8px;
  font-weight: 700;
  padding: 2px 5px;
  border-radius: 2px;
  border: 1px solid var(--grade-vf);
  color: var(--grade-vf);
  background: transparent;
}
```

**Content**: `VF`, `XF`, `AU`, `MS`

### 4.4 Certification Badge (Filled Style)

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

**Content**: `NGC`, `PCGS`

### 4.5 Rarity Indicator

```css
.rarity-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--rarity-r2);
}
```

### 4.6 Badge Row Order

**ALWAYS right-align badges in this order:**

```
[Certification] [Grade] [Metal] [Rarity●]
```

- Show certification ONLY if coin is slabbed (NGC/PCGS)
- Always show grade and metal
- Rarity dot only if rarity data exists

---

## 5. Coin Card Layout (v3.1)

### Desktop Horizontal Layout

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

### Exact Dimensions

| Element | Value |
|---------|-------|
| Card min-width | 360px |
| Card height | 170px |
| Image | 160×160px (square) |
| Category bar | 4px wide |
| Content padding | 12px 14px 12px 16px |
| Badge gap | 3px |
| Badge font | 8px |

### Mobile Vertical Layout

```
┌─────────────────────────┐
│ [4px] ┌───────────────┐ │
│  Cat  │   Coin Image  │ │
│  Bar  │   180px tall  │ │
│       │   (3D flip)   │ │
│       └───────────────┘ │
│                         │
│  Ruler Name      Year   │
│  ─────────────────────  │
│  OBV: Legend...         │
│  REV: Legend...         │
│  Reference              │
│  ─────────────────────  │
│  $384 ↑12%   [VF] [AR]  │
└─────────────────────────┘
```

| Element | Value |
|---------|-------|
| Card min-height | 380px |
| Image height | 180px |
| Image width | 100% |
| Content padding | 16px |

### 3D Flip Animation

Cards have a 3D flip effect on hover to show reverse:

```css
/* Flip container */
.flip-container {
  perspective: 1000px;
}

.flip-inner {
  transform-style: preserve-3d;
  transition: transform 0.6s ease-in-out;
}

.flip-container:hover .flip-inner {
  transform: rotateY(180deg);
}

/* Front and back faces */
.flip-front, .flip-back {
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

.flip-back {
  transform: rotateY(180deg);
}
```

---

## 6. Responsive Breakpoints

```css
/* Mobile-first breakpoints */
--breakpoint-sm: 640px;   /* Small tablets */
--breakpoint-md: 768px;   /* Tablets */
--breakpoint-lg: 1024px;  /* Laptops */
--breakpoint-xl: 1280px;  /* Desktops */
--breakpoint-2xl: 1536px; /* Large monitors */
--breakpoint-3xl: 1920px; /* 1080p */
--breakpoint-4xl: 2560px; /* 1440p/4K */
```

### Grid Column Counts

| Screen Size | Cards per Row |
|-------------|---------------|
| Mobile (<640px) | 1 |
| Tablet (640-1024px) | 2 |
| Desktop (1024-1536px) | 3-4 |
| Widescreen (1536-2560px) | 4-5 |
| 4K (>2560px) | 5-6 |

---

## 7. Dashboard Widget Specifications

### Metal Distribution Widget

```typescript
// Interactive badges that act as filters
<div className="metal-badges">
  {metals.map(metal => (
    <button
      key={metal.code}
      onClick={() => setFilter('metal', metal.code)}
      style={{
        background: `var(--metal-${metal.code.toLowerCase()}-subtle)`,
        color: `var(--metal-${metal.code.toLowerCase()})`,
      }}
    >
      {metal.code} {metal.count}
    </button>
  ))}
</div>
```

### Grade Distribution Widget

```typescript
// Horizontal bar with temperature gradient
<div className="grade-spectrum">
  {grades.map(grade => (
    <div
      key={grade.label}
      style={{
        width: `${grade.percentage}%`,
        background: getGradeColor(grade.label),
      }}
      title={`${grade.label}: ${grade.count}`}
    />
  ))}
</div>
```

### Category Donut Chart

- Use category colors for slices
- Interactive: click to filter
- Center shows total count

### Year Histogram

- Brush selection for year range filtering
- X-axis: Years (handle BC with negative numbers)
- Y-axis: Coin count

---

## 8. Animation & Interaction

### Hover Effects

```css
/* Card hover */
.coin-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
}

/* Badge hover glow */
.metal-badge:hover {
  box-shadow: 0 2px 8px var(--metal-glow-color);
}
```

### Transitions

```css
/* Standard transition */
transition: all 0.2s ease;

/* Card hover transition */
transition: transform 0.2s, box-shadow 0.2s;

/* 3D flip transition */
transition: transform 0.6s ease-in-out;
```

---

## 9. AI Implementation Checklist

Before submitting any UI changes, verify:

### Card Components

- [ ] Category bar present (4px left edge)
- [ ] Category bar has `border-radius: 8px 0 0 8px`
- [ ] Image is 160×160px (desktop)
- [ ] 3D flip effect on hover
- [ ] Legends section with OBV/REV labels
- [ ] Badge row order: [Cert] [Grade] [Metal] [Rarity●]
- [ ] Badge font is 8px with 2px 5px padding
- [ ] Price and performance on same line
- [ ] Hover lift (-2px) with enhanced shadow

### Colors

- [ ] Using design tokens (not raw hex)
- [ ] Category uses correct historical color
- [ ] Metal uses correct element color
- [ ] Grade uses temperature scale
- [ ] Rarity uses gemstone scale

### Typography

- [ ] Legends use Cinzel font
- [ ] References use monospace
- [ ] Following hierarchy order

### Responsive

- [ ] Mobile layout (vertical stack)
- [ ] Tablet layout (2 columns)
- [ ] Desktop layout (3-4 columns)
- [ ] No card overlap on resize

---

## 10. File Locations

| Asset | Path |
|-------|------|
| CSS Tokens | `frontend/src/index.css` |
| Tailwind Config | `frontend/tailwind.config.js` |
| Color Utilities | `frontend/src/components/design-system/colors.ts` |
| Metal Badge | `frontend/src/components/ui/badges/MetalBadge.tsx` |
| Grade Badge | `frontend/src/components/ui/badges/GradeBadge.tsx` |
| Coin Card | `frontend/src/components/coins/CoinCardV3.tsx` |
| Coin Table Row | `frontend/src/components/coins/CoinTableRowV3.tsx` |
| Design Spec | `design/CoinStack Design System v3.0.md` |

---

**Previous**: [09-TASK-RECIPES.md](09-TASK-RECIPES.md) - Implementation guides
**Next**: [11-FRONTEND-COMPONENTS.md](11-FRONTEND-COMPONENTS.md) - Component reference
**Related**: [04-FRONTEND-MODULES.md](04-FRONTEND-MODULES.md) - Frontend architecture
