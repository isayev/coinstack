# CoinStack Unified Design System

## Final Specification — Critical Analysis & Synthesis

---

## Executive Comparison

| Aspect | My Proposal | Alternative Proposal | **Final Decision** |
|--------|-------------|---------------------|-------------------|
| Metal colors | Chemically derived, subtle | Gaming-saturated | **MINE** — authenticity matters |
| Metal coverage | 10 metals with alloys | 9 metals, missing nuance | **MINE** — Electrum/Billon/Potin critical |
| Rarity scale | C→S→R1→R2→R3→U | R1→R5 + C/VC (inverted) | **MINE** — their scale is backwards |
| Rarity colors | Gemstone-inspired | Gaming-saturated | **SYNTHESIZE** — refine saturation |
| Grade metaphor | Temperature (cold→hot) | Gem clarity (confusing) | **MINE** — more intuitive |
| Grade colors | Blue→Green→Yellow→Red | Green→Cyan→Blue→Purple | **MINE** — theirs collides with rarity |
| Categories | Era-appropriate | Similar but Imperial=blue | **MINE** — purple is historically correct |
| UI density | 4-5 columns | 6x6 matrix | **SYNTHESIZE** — 5 columns optimal |
| Card design | Category border + metal badge | Inline everything | **SYNTHESIZE** — merge best elements |
| Hover states | Subtle elevation | Expand to 400×480 | **THEIRS** — good density idea |
| Sidebar | Stats + filters | Sparklines + alerts | **SYNTHESIZE** — combine both |

---

## 1. METALS — Final Decision: **My Proposal + Refinements**

### Why Reject Alternative

Their proposal:
```
Orichalcum: #D2691E (chocolate brown) ❌ WRONG
```

Orichalcum was a **golden brass** alloy — Romans specifically noted its gold-like appearance. #D2691E is "chocolate" color, completely inaccurate.

Their proposal also **conflates**:
- Bronze and Copper (different alloys, different appearance)
- Missing Electrum (critical for Greek staters, Coson)
- Missing Billon (essential for 3rd century crisis coins)
- Missing Potin (Celtic coinage)

### Final Metal Palette

```css
:root {
  /* ═══════════════════════════════════════════════════════════════
     PRECIOUS METALS — High value, warm tones
     ═══════════════════════════════════════════════════════════════ */
  
  /* Gold (Au, Z=79) — d-orbital transitions give characteristic color */
  --metal-au: #FFD700;
  --metal-au-subtle: rgba(255, 215, 0, 0.15);
  --metal-au-border: rgba(255, 215, 0, 0.40);
  --metal-au-text: #FFDF4D;
  --metal-au-glow: rgba(255, 215, 0, 0.6);  /* For hover shimmer */
  
  /* Electrum (Au+Ag natural alloy) — Pale gold, NOT yellow */
  --metal-el: #E8D882;
  --metal-el-subtle: rgba(232, 216, 130, 0.15);
  --metal-el-border: rgba(232, 216, 130, 0.40);
  --metal-el-text: #F0E29A;
  
  /* Silver (Ag, Z=47) — Cool white, slight blue undertone */
  --metal-ag: #C0C0C0;
  --metal-ag-subtle: rgba(192, 192, 192, 0.15);
  --metal-ag-border: rgba(192, 192, 192, 0.40);
  --metal-ag-text: #D8D8D8;
  --metal-ag-glow: rgba(192, 192, 192, 0.6);
  
  /* ═══════════════════════════════════════════════════════════════
     BASE METALS — Lower value, earth tones
     ═══════════════════════════════════════════════════════════════ */
  
  /* Orichalcum (Cu+Zn Roman "mountain copper") — GOLDEN brass, NOT brown */
  --metal-or: #C9A227;
  --metal-or-subtle: rgba(201, 162, 39, 0.15);
  --metal-or-border: rgba(201, 162, 39, 0.40);
  --metal-or-text: #DBB842;
  
  /* Brass (Cu+Zn generic) — Yellow-gold but less saturated */
  --metal-br: #B5A642;
  --metal-br-subtle: rgba(181, 166, 66, 0.15);
  --metal-br-border: rgba(181, 166, 66, 0.40);
  --metal-br-text: #C9BC5E;
  
  /* Bronze/Copper (Cu, Z=29) — Characteristic reddish-brown */
  --metal-cu: #CD7F32;
  --metal-cu-subtle: rgba(205, 127, 50, 0.15);
  --metal-cu-border: rgba(205, 127, 50, 0.40);
  --metal-cu-text: #DDA15E;
  
  /* Æ/Aes (generic bronze coinage) — Muted, patinated */
  --metal-ae: #8B7355;
  --metal-ae-subtle: rgba(139, 115, 85, 0.15);
  --metal-ae-border: rgba(139, 115, 85, 0.40);
  --metal-ae-text: #A38D6D;
  
  /* ═══════════════════════════════════════════════════════════════
     DEBASED/ALLOY METALS — Gray tones
     ═══════════════════════════════════════════════════════════════ */
  
  /* Billon (Ag+Cu debased) — Grayish with slight warmth */
  --metal-bi: #9A9A8E;
  --metal-bi-subtle: rgba(154, 154, 142, 0.15);
  --metal-bi-border: rgba(154, 154, 142, 0.40);
  --metal-bi-text: #B0B0A6;
  
  /* Potin (Cu+Sn+Pb Celtic) — Dark gray-brown */
  --metal-po: #5C5C52;
  --metal-po-subtle: rgba(92, 92, 82, 0.15);
  --metal-po-border: rgba(92, 92, 82, 0.40);
  --metal-po-text: #787870;
  
  /* Lead (Pb, Z=82) — Blue-gray characteristic */
  --metal-pb: #6B6B7A;
  --metal-pb-subtle: rgba(107, 107, 122, 0.15);
  --metal-pb-border: rgba(107, 107, 122, 0.40);
  --metal-pb-text: #858594;
}
```

### Metal Badge Final Design

**ACCEPT from alternative**: Element symbol styling is good
**REJECT from alternative**: Their oversaturated hover states

```tsx
// Final MetalBadge component
interface MetalBadgeProps {
  metal: Metal;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  showGlow?: boolean;  // For precious metals on hover
}

const METAL_CONFIG: Record<Metal, MetalConfig> = {
  au: { symbol: 'Au', name: 'Gold', atomic: 79, precious: true },
  el: { symbol: 'EL', name: 'Electrum', atomic: null, precious: true },
  ag: { symbol: 'Ag', name: 'Silver', atomic: 47, precious: true },
  or: { symbol: 'Or', name: 'Orichalcum', atomic: null, precious: false },
  br: { symbol: 'Br', name: 'Brass', atomic: null, precious: false },
  cu: { symbol: 'Cu', name: 'Copper', atomic: 29, precious: false },
  ae: { symbol: 'Æ', name: 'Bronze', atomic: null, precious: false },
  bi: { symbol: 'Bi', name: 'Billon', atomic: null, precious: false },
  po: { symbol: 'Po', name: 'Potin', atomic: null, precious: false },
  pb: { symbol: 'Pb', name: 'Lead', atomic: 82, precious: false },
};

export function MetalBadge({ metal, size = 'md', showGlow }: MetalBadgeProps) {
  const config = METAL_CONFIG[metal];
  
  return (
    <div 
      className={cn(
        "font-mono font-bold rounded flex items-center justify-center",
        "transition-all duration-200",
        `bg-metal-${metal}-subtle`,
        `text-metal-${metal}-text`,
        `border border-metal-${metal}-border`,
        // Precious metal shimmer on hover
        config.precious && showGlow && `hover:shadow-[0_0_12px_var(--metal-${metal}-glow)]`,
        // Size variants
        size === 'xs' && 'w-5 h-5 text-[10px]',
        size === 'sm' && 'w-6 h-6 text-xs',
        size === 'md' && 'w-8 h-8 text-sm',
        size === 'lg' && 'w-10 h-10 text-base',
      )}
    >
      {config.symbol}
    </div>
  );
}
```

---

## 2. RARITY — Final Decision: **My Scale, Refined Colors**

### Why Reject Alternative

Their scale is **backwards** from standard numismatic convention:

```
THEIR SCALE (WRONG):
R1 = Unique ← This is NOT standard
R2 = Extremely Rare
...
R5 = Scarce

STANDARD NUMISMATIC (CORRECT):
C  = Common
S  = Scarce  
R1 = Rare
R2 = Very Rare
R3 = Extremely Rare
U  = Unique (or R4/R5 in some systems)
```

RIC and most catalogs use R1→R5 where **R1 is LEAST rare** (just "rare"), not most. Their inversion would confuse any serious collector.

Their color choices also have issues:
- Green for Common collides with Grade scale
- Saturated gaming colors don't fit numismatic aesthetic

### Final Rarity Palette

**SYNTHESIZE**: Keep gemstone metaphor, but use my scale and more refined saturation:

```css
:root {
  /* ═══════════════════════════════════════════════════════════════
     RARITY SCALE — Gemstone-inspired, increasing intensity
     Based on standard RIC/BMCRE conventions
     ═══════════════════════════════════════════════════════════════ */
  
  /* Common (C) — Quartz/Smoky quartz (neutral, abundant) */
  --rarity-c: #8E8E93;
  --rarity-c-bg: rgba(142, 142, 147, 0.15);
  --rarity-c-name: "Quartz";
  
  /* Scarce (S) — Amethyst (first tier of "interesting") */
  --rarity-s: #9D7DD8;
  --rarity-s-bg: rgba(157, 125, 216, 0.15);
  --rarity-s-name: "Amethyst";
  
  /* Rare (R1) — Sapphire (genuinely uncommon) */
  --rarity-r1: #5B7FE8;
  --rarity-r1-bg: rgba(91, 127, 232, 0.15);
  --rarity-r1-name: "Sapphire";
  
  /* Very Rare (R2) — Emerald (significant scarcity) */
  --rarity-r2: #34C77B;
  --rarity-r2-bg: rgba(52, 199, 123, 0.15);
  --rarity-r2-name: "Emerald";
  
  /* Extremely Rare (R3) — Ruby (exceptional) */
  --rarity-r3: #E8475B;
  --rarity-r3-bg: rgba(232, 71, 91, 0.15);
  --rarity-r3-name: "Ruby";
  
  /* Unique (U) — Diamond (one-of-a-kind, prismatic) */
  --rarity-u: #FFFFFF;
  --rarity-u-bg: linear-gradient(
    135deg,
    rgba(232, 71, 91, 0.1),    /* Ruby */
    rgba(255, 193, 7, 0.1),    /* Topaz */
    rgba(52, 199, 123, 0.1),   /* Emerald */
    rgba(91, 127, 232, 0.1),   /* Sapphire */
    rgba(157, 125, 216, 0.1)   /* Amethyst */
  );
  --rarity-u-border: linear-gradient(135deg, #E8475B, #FFC107, #34C77B, #5B7FE8, #9D7DD8);
}
```

### Rarity Component

```tsx
// Final RarityIndicator component
type Rarity = 'c' | 's' | 'r1' | 'r2' | 'r3' | 'u';

const RARITY_CONFIG: Record<Rarity, RarityConfig> = {
  c:  { code: 'C',  label: 'Common',          gem: 'Quartz',   icon: '●' },
  s:  { code: 'S',  label: 'Scarce',          gem: 'Amethyst', icon: '●' },
  r1: { code: 'R1', label: 'Rare',            gem: 'Sapphire', icon: '●' },
  r2: { code: 'R2', label: 'Very Rare',       gem: 'Emerald',  icon: '●' },
  r3: { code: 'R3', label: 'Extremely Rare',  gem: 'Ruby',     icon: '●' },
  u:  { code: 'U',  label: 'Unique',          gem: 'Diamond',  icon: '◆' },
};

export function RarityIndicator({ rarity, variant = 'dot' }: Props) {
  const config = RARITY_CONFIG[rarity];
  
  if (variant === 'dot') {
    return (
      <Tooltip content={`${config.label} (${config.gem})`}>
        <span 
          className={cn(
            "text-sm cursor-help",
            `text-rarity-${rarity}`,
            rarity === 'u' && "animate-pulse"  // Unique gets subtle animation
          )}
        >
          {config.icon}
        </span>
      </Tooltip>
    );
  }
  
  // Badge variant
  return (
    <span className={cn(
      "px-2 py-0.5 rounded text-xs font-semibold",
      `bg-rarity-${rarity}-bg`,
      `text-rarity-${rarity}`,
      rarity === 'u' && "border border-transparent bg-clip-padding",
      rarity === 'u' && "relative before:absolute before:inset-0 before:rounded before:p-[1px]",
      rarity === 'u' && "before:bg-gradient-to-r before:from-red-500 before:via-yellow-500 before:to-blue-500"
    )}>
      {config.code}
    </span>
  );
}
```

---

## 3. GRADES — Final Decision: **My Temperature Scale**

### Why Reject Alternative

Their "Gem Clarity" scale has critical problems:

1. **Color collision**: Green for MS (Mint State) collides with their Green for Common rarity
2. **Counterintuitive progression**: Purple→Blue→Cyan→Green doesn't map to "better"
3. **No clear metaphor**: "Gem clarity" doesn't translate visually

My temperature scale is **immediately intuitive**:
- Poor = ❄️ Cold (blue)
- Mint = 🔥 Hot (red/gold)

Everyone understands "red hot" = good, "ice cold" = bad.

### Final Grade Palette

```css
:root {
  /* ═══════════════════════════════════════════════════════════════
     GRADE SCALE — Temperature metaphor (Cold → Hot)
     Maps to: Poor (1) → Mint State (10)
     ═══════════════════════════════════════════════════════════════ */
  
  /* Poor/Fair (1-2) — Freezing blue */
  --grade-poor: #5AC8FA;
  --grade-poor-bg: rgba(90, 200, 250, 0.15);
  
  /* Good/Very Good (3-4) — Cold teal */
  --grade-good: #64D2FF;
  --grade-good-bg: rgba(100, 210, 255, 0.15);
  
  /* Fine/Very Fine (5-6) — Neutral/warm green */
  --grade-fine: #34C759;
  --grade-fine-bg: rgba(52, 199, 89, 0.15);
  
  /* Extremely Fine (7) — Warm yellow */
  --grade-ef: #FFD60A;
  --grade-ef-bg: rgba(255, 214, 10, 0.15);
  
  /* About Uncirculated (8) — Hot orange */
  --grade-au: #FF9F0A;
  --grade-au-bg: rgba(255, 159, 10, 0.15);
  
  /* Mint State/FDC (9-10) — Fire red */
  --grade-ms: #FF6B6B;
  --grade-ms-bg: rgba(255, 107, 107, 0.15);
  
  /* Certification services (brand colors) */
  --grade-ngc: #1A73E8;
  --grade-ngc-bg: rgba(26, 115, 232, 0.15);
  --grade-pcgs: #2E7D32;
  --grade-pcgs-bg: rgba(46, 125, 50, 0.15);
}
```

### Grade Component

**SYNTHESIZE from alternative**: Their numeric scale idea (6.5/10) is good for detail views

```tsx
// Final GradeBadge component
interface GradeBadgeProps {
  grade: string;           // "VF", "EF", "MS"
  numericGrade?: number;   // 65 for MS65
  service?: 'NGC' | 'PCGS';
  showScale?: boolean;     // Show /10 rating
}

const GRADE_MAP: Record<string, GradeConfig> = {
  'P':   { tier: 'poor', numeric: 1, label: 'Poor' },
  'FR':  { tier: 'poor', numeric: 1.5, label: 'Fair' },
  'AG':  { tier: 'poor', numeric: 2, label: 'About Good' },
  'G':   { tier: 'good', numeric: 3, label: 'Good' },
  'VG':  { tier: 'good', numeric: 4, label: 'Very Good' },
  'F':   { tier: 'fine', numeric: 5, label: 'Fine' },
  'VF':  { tier: 'fine', numeric: 6, label: 'Very Fine' },
  'EF':  { tier: 'ef', numeric: 7, label: 'Extremely Fine' },
  'XF':  { tier: 'ef', numeric: 7, label: 'Extremely Fine' },
  'AU':  { tier: 'au', numeric: 8, label: 'About Uncirculated' },
  'MS':  { tier: 'ms', numeric: 9, label: 'Mint State' },
  'FDC': { tier: 'ms', numeric: 10, label: 'Fleur de Coin' },
};

export function GradeBadge({ grade, numericGrade, service, showScale }: GradeBadgeProps) {
  const baseGrade = grade.replace(/\d+/g, '').toUpperCase();
  const config = GRADE_MAP[baseGrade];
  
  return (
    <div className={cn(
      "inline-flex items-center gap-1 px-2 py-0.5 rounded text-sm font-medium",
      `bg-grade-${config.tier}-bg`,
      service ? `text-grade-${service.toLowerCase()}` : `text-grade-${config.tier}`
    )}>
      {/* Service badge */}
      {service && (
        <span className="font-bold text-xs">{service}</span>
      )}
      
      {/* Grade text */}
      <span>{grade}</span>
      
      {/* Numeric for certified */}
      {numericGrade && (
        <span className="text-text-tertiary">{numericGrade}</span>
      )}
      
      {/* Optional /10 scale */}
      {showScale && !numericGrade && (
        <span className="text-text-tertiary text-xs">
          {config.numeric}/10
        </span>
      )}
    </div>
  );
}
```

---

## 4. CATEGORIES — Final Decision: **My Palette with Minor Adjustments**

### Why Reject Alternative's Imperial Color

Their choice:
```
Imperial: #1976D2 (blue) ❌ WRONG
```

**Imperial purple** (Tyrian purple) was THE color of Roman emperors. It was illegal for non-emperors to wear. Using blue for Imperial misses this fundamental historical association.

### Final Category Palette

```css
:root {
  /* ═══════════════════════════════════════════════════════════════
     CATEGORIES — Era-appropriate, historically informed
     ═══════════════════════════════════════════════════════════════ */
  
  /* Republic (509-27 BC) — Terracotta/Roman brick red */
  --category-republic: #C0392B;
  --category-republic-subtle: rgba(192, 57, 43, 0.15);
  
  /* Imperial (27 BC - 284 AD) — Tyrian purple */
  --category-imperial: #8E44AD;
  --category-imperial-subtle: rgba(142, 68, 173, 0.15);
  
  /* Provincial (Greek Imperial) — Aegean blue */
  --category-provincial: #2980B9;
  --category-provincial-subtle: rgba(41, 128, 185, 0.15);
  
  /* Late Roman/Dominate (284-491 AD) — Byzantine gold */
  --category-late: #D4AF37;
  --category-late-subtle: rgba(212, 175, 55, 0.15);
  
  /* Greek (pre-Roman) — Olive (Mediterranean) */
  --category-greek: #7D8C4E;
  --category-greek-subtle: rgba(125, 140, 78, 0.15);
  
  /* Celtic — Forest green (Northern Europe) */
  --category-celtic: #27AE60;
  --category-celtic-subtle: rgba(39, 174, 96, 0.15);
  
  /* Judaean — Desert sand/stone */
  --category-judaea: #C2956E;
  --category-judaea-subtle: rgba(194, 149, 110, 0.15);
  
  /* Eastern (Parthian/Sasanian) — Persian turquoise */
  --category-eastern: #17A589;
  --category-eastern-subtle: rgba(23, 165, 137, 0.15);
  
  /* Byzantine (491+ AD) — Imperial crimson + gold */
  --category-byzantine: #922B21;
  --category-byzantine-subtle: rgba(146, 43, 33, 0.15);
}
```

---

## 5. UI/UX — Final Decision: **Synthesize Best of Both**

### Grid Density

**REJECT 6×6**: Too small on typical 1920×1080 monitors. Cards become unreadable.

**ACCEPT 5 columns** as optimal balance:
```
1920px viewport:
- Sidebar: 260px
- Content: 1660px
- 5 columns × 280px + gaps = ~1500px
- Comfortable padding
```

### Card Design — Synthesized

**ACCEPT from alternative**:
- Price trend inline (theirs: `$384 → $320 (-17%)`)
- Quick action buttons on hover
- Mini chart concept

**ACCEPT from mine**:
- Category-colored left border (instant visual categorization)
- Metal badge as element symbol
- Empty state with coin silhouette

**Final Card Layout**:

```
┌──────────────────────────────────────────────────────────────────┐
│  UNIFIED CARD DESIGN (280px × 380px)                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │▌                                        [Au] ●R2 [VF]     │  │
│  │▌  ┌──────────────────────────────────────────────────┐    │  │
│  │▌  │                                                  │    │  │
│  │▌  │                                                  │    │  │
│  │▌  │            [Coin Image / Obverse]                │    │  │
│  │▌  │                 200 × 200                        │    │  │
│  │▌  │                                                  │    │  │
│  │▌  │                                                  │    │  │
│  │▌  └──────────────────────────────────────────────────┘    │  │
│  │▌                                                          │  │
│  │▌  Antoninus Pius                                          │  │
│  │▌  Denarius · Rome · 138-161 AD                            │  │
│  │▌                                                          │  │
│  │▌  ┌────────────────────────────────────────────────────┐  │  │
│  │▌  │ RIC III 61                          $125 → $140 ▲ │  │  │
│  │▌  │ [Heritage '24]                              +12%  │  │  │
│  │▌  └────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  Hover state reveals:                                            │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  [Edit] [Comps] [✨ Expand Legend] [Share]                 │  │
│  │  ▁▂▃▅▇█▇▅ 30-day price trend                              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  Legend:                                                         │
│  ▌ = 4px category border (Imperial purple)                       │
│  [Au] = Metal badge (element style)                              │
│  ●R2 = Rarity dot + code                                        │
│  [VF] = Grade badge (temperature colored)                        │
│  ▲ = Price trend indicator (green up, red down)                  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Sidebar — Synthesized

**ACCEPT from alternative**:
- Sparkline charts for trends
- Alert badges
- Collection value prominently displayed

**ACCEPT from mine**:
- Metal filter chips with element styling
- Year range histogram

```
┌────────────────────────────────────────────────────────────────┐
│  UNIFIED SIDEBAR (260px)                                       │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 🔍 Search coins...                              ⌘K        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  📊 Collection                              110 coins     │ │
│  │  ════════════════════════════════════════════════════════ │ │
│  │  Value: $28,450 (+12% MoM)  ▁▂▃▅▇█▇▅ ← Sparkline         │ │
│  │  Avg Grade: VF · Best ROI: +42% (Nero denarius)          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ▼ Metal                                              [Clear]  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  [Au 12] [Ag 45] [Æ 48] [Bi 5]                           │ │
│  │   ████    ○○○○    ○○○○   ○○○                   (chips)   │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ▼ Category                                                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  [●] Imperial (67)      ████████████████████              │ │
│  │  [ ] Provincial (28)    ████████                          │ │
│  │  [ ] Republic (12)      ████                              │ │
│  │  [ ] Celtic (3)         █                                 │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ▼ Year Range                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  44 BC ─────────●──────────────● 476 AD                   │ │
│  │                                                            │ │
│  │  Distribution: ▁▂▃▅▇█▇▅▄▃▂▁▁▁▂▃▄▃▂▁                       │ │
│  │                ↑ Peak: Antonine period                    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ▶ Ruler (52 values)                                           │
│  ▶ Mint (18 values)                                            │
│  ▶ Denomination (12 values)                                    │
│  ▶ Grade                                                       │
│  ▶ Rarity                                                      │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│  🔔 Alerts (3)                                                  │
│  • New comp: RIC I 207 sold $420 (+15%)                        │
│  • Price drop: Nero denarius -8%                               │
│  • Die match found: Your RIC III 61                            │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### Coin Detail — Synthesized

**ACCEPT from alternative**: Tabbed layout with specific tabs
**ENHANCE with my additions**: LLM confidence indicators, legend expansion integration

```
┌────────────────────────────────────────────────────────────────────────────┐
│  COIN DETAIL VIEW                                                          │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ← Back to Collection                                                       │
│                                                                             │
│  ┌─────────────────────────────────────┬──────────────────────────────────┐│
│  │                                     │  Antoninus Pius                   ││
│  │                                     │  ══════════════════════════════  ││
│  │      [Obverse Image]                │  👑 Imperial · [Au] Gold         ││
│  │         400 × 400                   │                                   ││
│  │      [Click to zoom]                │  Denarius                         ││
│  │                                     │  Rome · 138-161 AD                ││
│  │  ┌───────┐ ┌───────┐               │                                   ││
│  │  │  Obv  │ │  Rev  │               │  ┌──────┐ ┌──────┐ ┌───────────┐ ││
│  │  └───────┘ └───────┘               │  │  VF  │ │ ●R2  │ │ RIC III 61│ ││
│  │                                     │  └──────┘ └──────┘ └───────────┘ ││
│  │                                     │                                   ││
│  │                                     │  Value: $125 → $140 ▲12%         ││
│  │                                     │  Acquired: $95 (Heritage, 2024)  ││
│  └─────────────────────────────────────┴──────────────────────────────────┘│
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ [📷 Images] [💰 Market] [📖 Catalog] [🏷️ Provenance] [🔬 Analysis]  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  📖 Catalog Tab:                                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Obverse Legend                                                      │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │  ANTONINVS AVG PIVS P P TR P COS III                           │  │  │
│  │  │                                                                 │  │  │
│  │  │  [✨ Expand Legend]                                             │  │  │
│  │  │                                                                 │  │  │
│  │  │  → Antoninus Augustus Pius Pater Patriae                       │  │  │
│  │  │    Tribunicia Potestate Consul III                             │  │  │
│  │  │                                                                 │  │  │
│  │  │  "Antoninus Augustus, the Pious, Father of the Fatherland,     │  │  │
│  │  │   holding Tribunician Power, Consul for the third time"        │  │  │
│  │  │                                                     [95% conf] │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                      │  │
│  │  References                                                          │  │
│  │  • RIC III 61 ✓ [View in OCRE]                                      │  │
│  │  • BMC 156                                                           │  │
│  │  • RSC 456                                                           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Final Tailwind Configuration

```js
// tailwind.config.js — FINAL UNIFIED
module.exports = {
  theme: {
    extend: {
      colors: {
        // ═══════════════════════════════════════════════════════════
        // METALS — Chemically derived
        // ═══════════════════════════════════════════════════════════
        metal: {
          au: { DEFAULT: '#FFD700', subtle: 'rgba(255,215,0,0.15)', border: 'rgba(255,215,0,0.4)', text: '#FFDF4D' },
          el: { DEFAULT: '#E8D882', subtle: 'rgba(232,216,130,0.15)', border: 'rgba(232,216,130,0.4)', text: '#F0E29A' },
          ag: { DEFAULT: '#C0C0C0', subtle: 'rgba(192,192,192,0.15)', border: 'rgba(192,192,192,0.4)', text: '#D8D8D8' },
          or: { DEFAULT: '#C9A227', subtle: 'rgba(201,162,39,0.15)', border: 'rgba(201,162,39,0.4)', text: '#DBB842' },
          br: { DEFAULT: '#B5A642', subtle: 'rgba(181,166,66,0.15)', border: 'rgba(181,166,66,0.4)', text: '#C9BC5E' },
          cu: { DEFAULT: '#CD7F32', subtle: 'rgba(205,127,50,0.15)', border: 'rgba(205,127,50,0.4)', text: '#DDA15E' },
          ae: { DEFAULT: '#8B7355', subtle: 'rgba(139,115,85,0.15)', border: 'rgba(139,115,85,0.4)', text: '#A38D6D' },
          bi: { DEFAULT: '#9A9A8E', subtle: 'rgba(154,154,142,0.15)', border: 'rgba(154,154,142,0.4)', text: '#B0B0A6' },
          po: { DEFAULT: '#5C5C52', subtle: 'rgba(92,92,82,0.15)', border: 'rgba(92,92,82,0.4)', text: '#787870' },
          pb: { DEFAULT: '#6B6B7A', subtle: 'rgba(107,107,122,0.15)', border: 'rgba(107,107,122,0.4)', text: '#858594' },
        },
        
        // ═══════════════════════════════════════════════════════════
        // RARITY — Gemstone-inspired
        // ═══════════════════════════════════════════════════════════
        rarity: {
          c:  { DEFAULT: '#8E8E93', bg: 'rgba(142,142,147,0.15)' },
          s:  { DEFAULT: '#9D7DD8', bg: 'rgba(157,125,216,0.15)' },
          r1: { DEFAULT: '#5B7FE8', bg: 'rgba(91,127,232,0.15)' },
          r2: { DEFAULT: '#34C77B', bg: 'rgba(52,199,123,0.15)' },
          r3: { DEFAULT: '#E8475B', bg: 'rgba(232,71,91,0.15)' },
          u:  { DEFAULT: '#FFFFFF', bg: 'rgba(255,255,255,0.1)' },
        },
        
        // ═══════════════════════════════════════════════════════════
        // GRADES — Temperature scale
        // ═══════════════════════════════════════════════════════════
        grade: {
          poor: { DEFAULT: '#5AC8FA', bg: 'rgba(90,200,250,0.15)' },
          good: { DEFAULT: '#64D2FF', bg: 'rgba(100,210,255,0.15)' },
          fine: { DEFAULT: '#34C759', bg: 'rgba(52,199,89,0.15)' },
          ef:   { DEFAULT: '#FFD60A', bg: 'rgba(255,214,10,0.15)' },
          au:   { DEFAULT: '#FF9F0A', bg: 'rgba(255,159,10,0.15)' },
          ms:   { DEFAULT: '#FF6B6B', bg: 'rgba(255,107,107,0.15)' },
          ngc:  { DEFAULT: '#1A73E8', bg: 'rgba(26,115,232,0.15)' },
          pcgs: { DEFAULT: '#2E7D32', bg: 'rgba(46,125,50,0.15)' },
        },
        
        // ═══════════════════════════════════════════════════════════
        // CATEGORIES — Era-appropriate
        // ═══════════════════════════════════════════════════════════
        category: {
          republic:   { DEFAULT: '#C0392B', subtle: 'rgba(192,57,43,0.15)' },
          imperial:   { DEFAULT: '#8E44AD', subtle: 'rgba(142,68,173,0.15)' },
          provincial: { DEFAULT: '#2980B9', subtle: 'rgba(41,128,185,0.15)' },
          late:       { DEFAULT: '#D4AF37', subtle: 'rgba(212,175,55,0.15)' },
          greek:      { DEFAULT: '#7D8C4E', subtle: 'rgba(125,140,78,0.15)' },
          celtic:     { DEFAULT: '#27AE60', subtle: 'rgba(39,174,96,0.15)' },
          judaea:     { DEFAULT: '#C2956E', subtle: 'rgba(194,149,110,0.15)' },
          eastern:    { DEFAULT: '#17A589', subtle: 'rgba(23,165,137,0.15)' },
          byzantine:  { DEFAULT: '#922B21', subtle: 'rgba(146,43,33,0.15)' },
        },
      },
    },
  },
};
```

---

## 7. Summary of Decisions

| Element | Decision | Rationale |
|---------|----------|-----------|
| Metal Au | #FFD700 | **Both agree** |
| Metal Ag | #C0C0C0 | **Both agree** |
| Metal Orichalcum | **#C9A227 (mine)** | Their #D2691E is chocolate, not golden brass |
| Electrum/Billon/Potin | **Include (mine)** | Essential for numismatic accuracy |
| Rarity scale | **C→S→R1→R2→R3→U (mine)** | Their R1=Unique is backwards |
| Rarity colors | **Refined gemstone** | Keep metaphor, reduce saturation |
| Grade metaphor | **Temperature (mine)** | Intuitive cold→hot mapping |
| Grade colors | **Blue→Green→Yellow→Red (mine)** | Their green MS collides with rarity |
| Imperial color | **#8E44AD purple (mine)** | Tyrian purple is historically correct |
| Grid density | **5 columns (synthesized)** | Balance between theirs (6) and current (4) |
| Card design | **Synthesized** | Category border + price trend + hover actions |
| Sidebar | **Synthesized** | Sparklines + element chips + year histogram |
| Hover expand | **Accept (theirs)** | Good density idea |
| LegendExpander button | **Accept (theirs)** | Good UX addition |
| Price trend inline | **Accept (theirs)** | Useful at-a-glance info |

---

## 8. Implementation Priority (Revised)

| Day | Focus | Components |
|-----|-------|------------|
| **1** | Color system | CSS variables, Tailwind config |
| **2** | Core badges | MetalBadge, GradeBadge, RarityIndicator |
| **3** | Card redesign | CoinCard with category border, hover state |
| **4** | Sidebar filters | Metal chips, year histogram, sparklines |
| **5** | Detail view | Tabbed layout, LegendExpander integration |
| **6** | Responsive | 5→3→1 column breakpoints |
| **7** | Polish | Animations, accessibility, dark mode fine-tuning |

---

*Unified Design System v1.0 — January 2026*
*Synthesized from two proposals with numismatic accuracy as priority*
