/**
 * CoinTable - Redesigned table view for coin collection
 * 
 * Features:
 * - Category indicator bar (4px left border)
 * - Thumbnail with obverse image
 * - Ruler with reign dates context
 * - Primary reference display
 * - Rarity indicator (dot + code)
 * - Value with acquisition price
 * - Configurable column visibility
 * 
 * @module components/coins/CoinTable
 */

import { useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import { CoinListItem, Category } from "@/types/coin";
import { useColumnStore } from "@/stores/columnStore";
import { useFilterStore, SortField } from "@/stores/filterStore";
import { MetalBadge, GradeBadge, RarityIndicator } from "@/components/design-system";
import { ArrowUp, ArrowDown, ImageOff } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";

// ============================================================================
// TYPES
// ============================================================================

interface CoinTableProps {
  coins: CoinListItem[];
  selectedIds?: Set<number>;
  onSelectionChange?: (ids: Set<number>) => void;
}

// ============================================================================
// HELPERS
// ============================================================================

/**
 * Get CSS class for category row tinting
 */
function getCategoryRowClass(category: Category): string {
  const map: Record<Category, string> = {
    republic: "category-row-republic",
    imperial: "category-row-imperial",
    provincial: "category-row-provincial",
    greek: "category-row-greek",
    celtic: "category-row-celtic",
    judaean: "category-row-judaean",
    byzantine: "category-row-byzantine",
    migration: "category-row-other",
    pseudo_roman: "category-row-other",
    other: "category-row-other",
  };
  return map[category] || "category-row-other";
}

/**
 * Get CSS variable for category color
 */
function getCategoryColor(category: Category): string {
  const map: Record<Category, string> = {
    republic: "var(--category-republic)",
    imperial: "var(--category-imperial)",
    provincial: "var(--category-provincial)",
    greek: "var(--category-greek)",
    celtic: "var(--category-celtic)",
    judaean: "var(--category-judaea)",
    byzantine: "var(--category-byzantine)",
    migration: "var(--category-other)",
    pseudo_roman: "var(--category-other)",
    other: "var(--category-other)",
  };
  return map[category] || "var(--category-other)";
}

/**
 * Format year range for display
 */
function formatYearRange(
  start: number | null | undefined,
  end: number | null | undefined,
  isCirca?: boolean
): string {
  if (!start && !end) return "—";
  const prefix = isCirca ? "c. " : "";

  if (start && end && start !== end) {
    const startStr = start < 0 ? `${Math.abs(start)}` : `${start}`;
    const endStr = end < 0 ? `${Math.abs(end)} BC` : `${end} AD`;
    const startSuffix = start < 0 && end > 0 ? " BC" : "";
    return `${prefix}${startStr}${startSuffix}–${endStr}`;
  }

  const year = start || end;
  if (!year) return "—";
  return `${prefix}${Math.abs(year)} ${year < 0 ? "BC" : "AD"}`;
}

/**
 * Format reign dates for ruler context subtitle
 */
function formatReignDates(
  reignStart: number | null | undefined,
  reignEnd: number | null | undefined
): string | null {
  if (!reignStart && !reignEnd) return null;
  return formatYearRange(reignStart, reignEnd, false);
}

/**
 * Format price for display
 */
function formatPrice(price: string | number | null | undefined): string {
  if (price === null || price === undefined) return "—";
  const numPrice = typeof price === "string" ? parseFloat(price) : price;
  if (isNaN(numPrice)) return "—";
  return `$${numPrice.toLocaleString()}`;
}

// ============================================================================
// TABLE HEADER COMPONENT
// ============================================================================

interface TableHeaderCellProps {
  field?: SortField;
  currentSort: SortField;
  sortDir: "asc" | "desc";
  onSort: (field: SortField, dir?: "asc" | "desc") => void;
  sortable: boolean;
  children: React.ReactNode;
  className?: string;
  width?: string;
}

function TableHeaderCell({
  field,
  currentSort,
  sortDir,
  onSort,
  sortable,
  children,
  className,
  width,
}: TableHeaderCellProps) {
  const isActive = sortable && field && currentSort === field;

  return (
    <th
      className={cn(
        "text-left px-3 py-2.5 font-medium text-[11px] uppercase tracking-wide select-none whitespace-nowrap",
        sortable && "cursor-pointer hover:text-[var(--text-secondary)]",
        className
      )}
      style={{
        color: isActive ? "var(--metal-au)" : "var(--text-tertiary)",
        width: width,
        minWidth: width,
      }}
      onClick={() => {
        if (sortable && field) {
          if (isActive) {
            onSort(field, sortDir === "asc" ? "desc" : "asc");
          } else {
            onSort(field, "asc");
          }
        }
      }}
    >
      <div className={cn("flex items-center gap-1", className?.includes("text-right") && "justify-end")}>
        <span>{children}</span>
        {isActive && (sortDir === "asc" ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />)}
      </div>
    </th>
  );
}

// ============================================================================
// THUMBNAIL COMPONENT
// ============================================================================

function CoinThumbnail({ src, alt }: { src?: string | null; alt: string }) {
  if (!src) {
    return (
      <div
        className="w-9 h-9 rounded-full flex items-center justify-center"
        style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)" }}
      >
        <ImageOff className="w-3.5 h-3.5" style={{ color: "var(--text-tertiary)" }} />
      </div>
    );
  }

  return (
    <div
      className="w-9 h-9 rounded-full overflow-hidden"
      style={{ border: "1px solid var(--border-subtle)" }}
    >
      <img src={src} alt={alt} className="w-full h-full object-cover" />
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function CoinTable({ coins, selectedIds = new Set(), onSelectionChange }: CoinTableProps) {
  const navigate = useNavigate();
  const { columns, getVisibleColumns } = useColumnStore();
  const { sortBy, sortDir, setSort } = useFilterStore();
  const visibleColumns = getVisibleColumns();

  // Check if all coins are selected
  const allSelected = coins.length > 0 && coins.every((coin) => selectedIds.has(coin.id));
  const someSelected = coins.some((coin) => selectedIds.has(coin.id)) && !allSelected;

  // Handle select all
  const handleSelectAll = () => {
    if (onSelectionChange) {
      if (allSelected) {
        onSelectionChange(new Set());
      } else {
        onSelectionChange(new Set(coins.map((c) => c.id)));
      }
    }
  };

  // Handle individual selection
  const handleSelectCoin = (coinId: number, checked: boolean) => {
    if (onSelectionChange) {
      const newSelection = new Set(selectedIds);
      if (checked) {
        newSelection.add(coinId);
      } else {
        newSelection.delete(coinId);
      }
      onSelectionChange(newSelection);
    }
  };

  // Column visibility checks
  const isVisible = (columnId: string) => visibleColumns.some((c) => c.id === columnId);
  const getColumn = (columnId: string) => columns.find((c) => c.id === columnId);

  return (
    <div
      className="rounded-lg overflow-hidden"
      style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)" }}
    >
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ background: "var(--bg-card)", borderBottom: "1px solid var(--border-subtle)" }}>
              {/* Category bar - always visible, no header */}
              {isVisible("category") && <th className="w-1 p-0" />}

              {/* Checkbox column */}
              {isVisible("checkbox") && (
                <th className="w-8 px-2 py-2.5">
                  <Checkbox
                    checked={allSelected}
                    // @ts-expect-error - indeterminate is valid but not in types
                    indeterminate={someSelected}
                    onCheckedChange={handleSelectAll}
                    className="data-[state=checked]:bg-[var(--metal-au)] data-[state=checked]:border-[var(--metal-au)]"
                  />
                </th>
              )}

              {/* Thumbnail - no header */}
              {isVisible("thumbnail") && <th className="w-10 px-1" />}

              {/* Metal - icon column, minimal header */}
              {isVisible("metal") && (
                <TableHeaderCell
                  field={getColumn("metal")?.sortField}
                  currentSort={sortBy}
                  sortDir={sortDir}
                  onSort={setSort}
                  sortable={getColumn("metal")?.sortable ?? true}
                  width="40px"
                >
                  Metal
                </TableHeaderCell>
              )}

              {/* Grade - icon column */}
              {isVisible("grade") && (
                <TableHeaderCell
                  field={getColumn("grade")?.sortField}
                  currentSort={sortBy}
                  sortDir={sortDir}
                  onSort={setSort}
                  sortable={getColumn("grade")?.sortable ?? true}
                  width="50px"
                >
                  Grade
                </TableHeaderCell>
              )}

              {/* Ruler */}
              {isVisible("ruler") && (
                <TableHeaderCell
                  field={getColumn("ruler")?.sortField}
                  currentSort={sortBy}
                  sortDir={sortDir}
                  onSort={setSort}
                  sortable={getColumn("ruler")?.sortable ?? true}
                  width="160px"
                >
                  Ruler
                </TableHeaderCell>
              )}

              {/* Date */}
              {isVisible("date") && (
                <TableHeaderCell
                  field={getColumn("date")?.sortField}
                  currentSort={sortBy}
                  sortDir={sortDir}
                  onSort={setSort}
                  sortable={getColumn("date")?.sortable ?? true}
                  width="90px"
                >
                  Date
                </TableHeaderCell>
              )}

              {/* Denomination */}
              {isVisible("denomination") && (
                <TableHeaderCell
                  field={getColumn("denomination")?.sortField}
                  currentSort={sortBy}
                  sortDir={sortDir}
                  onSort={setSort}
                  sortable={getColumn("denomination")?.sortable ?? true}
                  width="90px"
                >
                  Denom
                </TableHeaderCell>
              )}

              {/* Obverse */}
              {isVisible("obverse") && (
                <TableHeaderCell
                  field={getColumn("obverse")?.sortField}
                  currentSort={sortBy}
                  sortDir={sortDir}
                  onSort={setSort}
                  sortable={getColumn("obverse")?.sortable ?? false}
                  width="150px"
                >
                  Obverse
                </TableHeaderCell>
              )}

              {/* Reverse */}
              {isVisible("reverse") && (
                <TableHeaderCell
                  field={getColumn("reverse")?.sortField}
                  currentSort={sortBy}
                  sortDir={sortDir}
                  onSort={setSort}
                  sortable={getColumn("reverse")?.sortable ?? false}
                  width="150px"
                >
                  Reverse
                </TableHeaderCell>
              )}

              {/* Mint */}
              {isVisible("mint") && (
                <TableHeaderCell
                  field={getColumn("mint")?.sortField}
                  currentSort={sortBy}
                  sortDir={sortDir}
                  onSort={setSort}
                  sortable={getColumn("mint")?.sortable ?? false}
                  width="80px"
                >
                  Mint
                </TableHeaderCell>
              )}

              {/* Reference */}
              {isVisible("reference") && (
                <TableHeaderCell
                  field={getColumn("reference")?.sortField}
                  currentSort={sortBy}
                  sortDir={sortDir}
                  onSort={setSort}
                  sortable={getColumn("reference")?.sortable ?? false}
                  width="100px"
                >
                  Reference
                </TableHeaderCell>
              )}

              {/* Rarity */}
              {isVisible("rarity") && (
                <TableHeaderCell
                  field={getColumn("rarity")?.sortField}
                  currentSort={sortBy}
                  sortDir={sortDir}
                  onSort={setSort}
                  sortable={getColumn("rarity")?.sortable ?? true}
                  width="50px"
                >
                  Rarity
                </TableHeaderCell>
              )}

              {/* Value */}
              {isVisible("value") && (
                <TableHeaderCell
                  field={getColumn("value")?.sortField}
                  currentSort={sortBy}
                  sortDir={sortDir}
                  onSort={setSort}
                  sortable={getColumn("value")?.sortable ?? true}
                  width="80px"
                  className="text-right"
                >
                  Value
                </TableHeaderCell>
              )}

              {/* Optional columns */}
              {isVisible("weight") && (
                <TableHeaderCell
                  field={getColumn("weight")?.sortField}
                  currentSort={sortBy}
                  sortDir={sortDir}
                  onSort={setSort}
                  sortable={getColumn("weight")?.sortable ?? true}
                  width="60px"
                  className="text-right"
                >
                  Weight
                </TableHeaderCell>
              )}

              {isVisible("diameter") && (
                <TableHeaderCell
                  field={getColumn("diameter")?.sortField}
                  currentSort={sortBy}
                  sortDir={sortDir}
                  onSort={setSort}
                  sortable={getColumn("diameter")?.sortable ?? false}
                  width="60px"
                  className="text-right"
                >
                  Diam
                </TableHeaderCell>
              )}

              {isVisible("dieAxis") && (
                <TableHeaderCell
                  field={getColumn("dieAxis")?.sortField}
                  currentSort={sortBy}
                  sortDir={sortDir}
                  onSort={setSort}
                  sortable={getColumn("dieAxis")?.sortable ?? false}
                  width="50px"
                >
                  Axis
                </TableHeaderCell>
              )}

              {isVisible("acquired") && (
                <TableHeaderCell
                  field={getColumn("acquired")?.sortField}
                  currentSort={sortBy}
                  sortDir={sortDir}
                  onSort={setSort}
                  sortable={getColumn("acquired")?.sortable ?? true}
                  width="100px"
                >
                  Acquired
                </TableHeaderCell>
              )}

              {isVisible("provenance") && (
                <TableHeaderCell
                  field={getColumn("provenance")?.sortField}
                  currentSort={sortBy}
                  sortDir={sortDir}
                  onSort={setSort}
                  sortable={getColumn("provenance")?.sortable ?? false}
                  width="150px"
                >
                  Provenance
                </TableHeaderCell>
              )}
            </tr>
          </thead>
          <tbody>
            {coins.map((coin) => (
              <tr
                key={coin.id}
                className={cn(
                  "cursor-pointer transition-colors",
                  getCategoryRowClass(coin.category)
                )}
                style={{ borderBottom: "1px solid var(--border-subtle)" }}
                onClick={() => navigate(`/coins/${coin.id}`)}
                onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg-elevated)")}
                onMouseLeave={(e) => {
                  // Reset to category row tint
                  e.currentTarget.style.background = "";
                }}
              >
                {/* Category bar */}
                {isVisible("category") && (
                  <td className="p-0 w-1">
                    <div
                      className="w-1 h-full min-h-[48px]"
                      style={{ background: getCategoryColor(coin.category) }}
                    />
                  </td>
                )}

                {/* Checkbox */}
                {isVisible("checkbox") && (
                  <td className="px-2 py-2" onClick={(e) => e.stopPropagation()}>
                    <Checkbox
                      checked={selectedIds.has(coin.id)}
                      onCheckedChange={(checked) => handleSelectCoin(coin.id, checked as boolean)}
                      className="data-[state=checked]:bg-[var(--metal-au)] data-[state=checked]:border-[var(--metal-au)]"
                    />
                  </td>
                )}

                {/* Thumbnail */}
                {isVisible("thumbnail") && (
                  <td className="px-1 py-1">
                    <CoinThumbnail src={coin.primary_image} alt={coin.issuing_authority} />
                  </td>
                )}

                {/* Metal */}
                {isVisible("metal") && (
                  <td className="px-2 py-2">
                    <MetalBadge metal={coin.metal} size="xs" />
                  </td>
                )}

                {/* Grade */}
                {isVisible("grade") && (
                  <td className="px-2 py-2">
                    {coin.grade ? (
                      <GradeBadge grade={coin.grade} size="xs" />
                    ) : (
                      <span style={{ color: "var(--text-tertiary)" }}>—</span>
                    )}
                  </td>
                )}

                {/* Ruler */}
                {isVisible("ruler") && (
                  <td className="px-3 py-2">
                    <div className="flex flex-col">
                      <div className="flex items-center gap-1.5">
                        <span className="font-medium" style={{ color: "var(--text-primary)" }}>
                          {coin.issuing_authority}
                        </span>
                        {coin.is_test_cut && (
                          <span
                            className="text-[9px] px-1 py-0 rounded font-medium"
                            style={{ background: "rgba(255, 69, 58, 0.2)", color: "#FF453A" }}
                          >
                            TC
                          </span>
                        )}
                      </div>
                      {(coin.reign_start || coin.reign_end) && (
                        <span className="text-[11px]" style={{ color: "var(--text-tertiary)" }}>
                          {formatReignDates(coin.reign_start, coin.reign_end)}
                        </span>
                      )}
                    </div>
                  </td>
                )}

                {/* Date */}
                {isVisible("date") && (
                  <td
                    className="px-3 py-2 tabular-nums text-[12px] whitespace-nowrap"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {formatYearRange(coin.mint_year_start, coin.mint_year_end, coin.is_circa)}
                  </td>
                )}

                {/* Denomination */}
                {isVisible("denomination") && (
                  <td className="px-3 py-2 text-[12px]" style={{ color: "var(--text-secondary)" }}>
                    {coin.denomination}
                  </td>
                )}

                {/* Obverse */}
                {isVisible("obverse") && (
                  <td
                    className="px-3 py-2 text-[11px] max-w-[150px]"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {coin.obverse_legend ? (
                      <span className="line-clamp-2" title={coin.obverse_legend}>
                        {coin.obverse_legend}
                      </span>
                    ) : (
                      <span style={{ color: "var(--text-tertiary)" }}>—</span>
                    )}
                  </td>
                )}

                {/* Reverse */}
                {isVisible("reverse") && (
                  <td
                    className="px-3 py-2 text-[11px] max-w-[150px]"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {coin.reverse_legend ? (
                      <span className="line-clamp-2" title={coin.reverse_legend}>
                        {coin.reverse_legend}
                      </span>
                    ) : (
                      <span style={{ color: "var(--text-tertiary)" }}>—</span>
                    )}
                  </td>
                )}

                {/* Mint */}
                {isVisible("mint") && (
                  <td className="px-3 py-2 text-[12px]" style={{ color: "var(--text-secondary)" }}>
                    {coin.mint_name || "—"}
                  </td>
                )}

                {/* Reference */}
                {isVisible("reference") && (
                  <td className="px-3 py-2">
                    {coin.primary_reference ? (
                      <span
                        className="font-serif text-[12px]"
                        style={{ color: "var(--metal-au)" }}
                      >
                        {coin.primary_reference}
                      </span>
                    ) : (
                      <span style={{ color: "var(--text-tertiary)" }}>—</span>
                    )}
                  </td>
                )}

                {/* Rarity */}
                {isVisible("rarity") && (
                  <td className="px-3 py-2">
                    {coin.rarity ? (
                      <div className="flex items-center gap-1">
                        <RarityIndicator rarity={coin.rarity} variant="dot" showTooltip={false} />
                        <span className="text-[11px]" style={{ color: "var(--text-tertiary)" }}>
                          {coin.rarity === "common"
                            ? "C"
                            : coin.rarity === "scarce"
                            ? "S"
                            : coin.rarity === "rare"
                            ? "R1"
                            : coin.rarity === "very_rare"
                            ? "R2"
                            : coin.rarity === "extremely_rare"
                            ? "R3"
                            : "U"}
                        </span>
                      </div>
                    ) : (
                      <span style={{ color: "var(--text-tertiary)" }}>—</span>
                    )}
                  </td>
                )}

                {/* Value */}
                {isVisible("value") && (
                  <td className="px-3 py-2 text-right">
                    <div className="flex flex-col items-end">
                      <span
                        className="font-medium tabular-nums"
                        style={{ color: "var(--text-primary)" }}
                      >
                        {formatPrice(coin.estimated_value_usd)}
                      </span>
                      {coin.acquisition_price && (
                        <span className="text-[10px]" style={{ color: "var(--text-tertiary)" }}>
                          paid {formatPrice(coin.acquisition_price)}
                        </span>
                      )}
                    </div>
                  </td>
                )}

                {/* Optional: Weight */}
                {isVisible("weight") && (
                  <td
                    className="px-3 py-2 text-right tabular-nums text-[12px]"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {coin.weight_g ? `${coin.weight_g}g` : "—"}
                  </td>
                )}

                {/* Optional: Diameter */}
                {isVisible("diameter") && (
                  <td
                    className="px-3 py-2 text-right tabular-nums text-[12px]"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {coin.diameter_mm ? `${coin.diameter_mm}mm` : "—"}
                  </td>
                )}

                {/* Optional: Die Axis */}
                {isVisible("dieAxis") && (
                  <td className="px-3 py-2 text-[12px]" style={{ color: "var(--text-secondary)" }}>
                    {coin.die_axis !== null && coin.die_axis !== undefined ? `${coin.die_axis}h` : "—"}
                  </td>
                )}

                {/* Optional: Acquired */}
                {isVisible("acquired") && (
                  <td className="px-3 py-2 text-[12px]" style={{ color: "var(--text-secondary)" }}>
                    {coin.acquisition_date || "—"}
                  </td>
                )}

                {/* Optional: Provenance */}
                {isVisible("provenance") && (
                  <td
                    className="px-3 py-2 text-[12px] truncate max-w-[150px]"
                    style={{ color: "var(--text-secondary)" }}
                    title={coin.acquisition_source || undefined}
                  >
                    {coin.acquisition_source || "—"}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
