# Design Audit Issue Log

**Source:** DESIGN-AUDIT-REPORT.md  
**Severity:** 1 = cosmetic / low, 5 = critical / high.  
**Status:** Done = fixed in Phase A (Jan 2026); Open = not yet addressed.

| ID | Category | Location | Description | Severity | Status |
|----|----------|----------|-------------|----------|--------|
| VC-001 | Visual consistency | index.css | Certification colors defined twice; latter block overrides NGC/PCGS. | 4 | **Done** |
| VC-002 | Visual consistency | Design doc vs code | 10-DESIGN-SYSTEM grade-ms/rarity-r3 values differ from index.css. | 3 | **Done** |
| VC-003 | Visual consistency | Badges | Generic Badge vs MetalBadge/GradeBadge use different token systems. | 2 | **Done** |
| VC-004 | Visual consistency | Radius | Mixed rounded-lg / rounded-md; Tailwind radius tokens vs spec. | 2 | **Done** |
| VC-005 | Visual consistency | Focus | Base outline vs shadcn ring differ. | 2 | **Done** |
| VC-006 | Visual consistency | Cert tokens | grade-ngc/grade-pcgs vs cert-ngc/cert-pcgs; cert-* overridden later. | 4 | **Done** |
| HR-001 | Hierarchy | Empty states | No single “empty state title” token. | 1 | Open |
| HR-002 | Hierarchy | ReviewQueuePage | OK. | 0 | — |
| HR-003 | Hierarchy | Tables | Dense rows may need stronger hover/selected state. | 2 |
| HR-004 | Hierarchy | AIReviewTab | Raw Tailwind blue-500/10, purple-500/10 instead of tokens. | 3 | **Done** |
| IF-001 | Interaction | Buttons | OK. | 0 | — |
| IF-002 | Interaction | CoinCard | OK. | 0 | — |
| IF-003 | Interaction | Loading | No unified skeleton pattern for card/table chunks. | 2 | **Done** |
| IF-004 | Interaction | Review queue | Green/red icon buttons use Tailwind instead of semantic tokens. | 2 | **Done** |
| IF-005 | Interaction | Touch targets | Sidebar nav and some icon-only buttons may be &lt; 44px. | 3 | **Done** |
| LS-001 | Layout | Card padding | Spec 12/14/12/16 vs Tailwind p-6. | 2 | **Done** |
| LS-002 | Layout | Content width | No single max-width token for main content. | 2 | **Done** |
| LS-003 | Layout | Grid | Breakpoints documented but not tokenized. | 1 | Open |
| IA-001 | IA | Review vs Audit | OK. | 0 | — |
| IA-002 | IA | Filters | Search/URL not synced with collection filters. | 3 | **Done** |
| IA-003 | IA | Badge order | OK. | 0 | — |

**Quick-win targets (all done):** VC-001, VC-002, VC-006, HR-004, IF-004.
