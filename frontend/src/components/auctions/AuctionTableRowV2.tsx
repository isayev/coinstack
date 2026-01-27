/**
 * AuctionTableRowV2 - Grid-based row for Auction List
 * 
 * Layout:
 * Image | House | Sale | Lot | Date | Price | Status | Link
 */

import { AuctionListItem } from "@/hooks/useAuctions";
import { ExternalLink, Gavel, Calendar, Hash } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export interface AuctionTableRowV2Props {
    auction: AuctionListItem;
    onClick?: (auction: AuctionListItem) => void;
    className?: string;
}

// 48px img | 140px House | 1fr Sale | 80px Lot | 100px Date | 100px Price | 80px Status | 40px Link
const AUCTION_GRID_LAYOUT = "48px minmax(120px, 140px) 1fr 80px 100px 100px 80px 40px";

export function AuctionTableRowV2({
    auction,
    onClick,
    className,
}: AuctionTableRowV2Props) {

    const handleLinkClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        window.open(auction.url, "_blank");
    };

    return (
        <div
            className={cn(
                'relative group cursor-pointer border-b border-[var(--border-subtle)] transition-all hover:bg-[var(--bg-hover)] hidden md:grid items-center gap-4 px-4 py-2',
                className
            )}
            style={{
                height: '64px', // Slightly taller for auction rows
                gridTemplateColumns: AUCTION_GRID_LAYOUT,
            }}
            onClick={() => onClick?.(auction)}
        >
            {/* 1. Image / Thumbnail */}
            <div className="w-12 h-12 rounded overflow-hidden bg-[var(--bg-elevated)] relative flex-shrink-0">
                {auction.thumbnail ? (
                    <img
                        src={auction.thumbnail}
                        alt="Lot"
                        className="w-full h-full object-cover transition-transform group-hover:scale-110"
                        loading="lazy"
                    />
                ) : (
                    <div className="flex items-center justify-center w-full h-full text-[var(--text-ghost)]">
                        <Gavel className="w-5 h-5" />
                    </div>
                )}
            </div>

            {/* 2. Auction House */}
            <div className="font-semibold text-sm truncate">
                {auction.auction_house}
            </div>

            {/* 3. Sale Name (Truncated) */}
            <div className="text-sm text-muted-foreground truncate" title={auction.sale_name || ''}>
                {auction.sale_name || '—'}
            </div>

            {/* 4. Lot Number */}
            <div className="font-mono text-sm flex items-center gap-1 text-muted-foreground">
                <Hash className="w-3 h-3 opacity-50" />
                {auction.lot_number || '?'}
            </div>

            {/* 5. Date */}
            <div className="text-sm text-muted-foreground flex items-center gap-1">
                <Calendar className="w-3 h-3 opacity-50" />
                <span className="truncate">{auction.auction_date || '—'}</span>
            </div>

            {/* 6. Price */}
            <div className="text-right font-medium text-sm tabular-nums">
                {auction.hammer_price !== null ? (
                    <span>
                        {new Intl.NumberFormat('en-US', {
                            style: 'currency',
                            currency: auction.currency || 'USD',
                            minimumFractionDigits: 0,
                            maximumFractionDigits: 0,
                        }).format(auction.hammer_price)}
                    </span>
                ) : (
                    <span className="text-muted-foreground">—</span>
                )}
            </div>

            {/* 7. Status */}
            <div className="flex justify-center">
                {auction.hammer_price !== null ? (
                    <Badge variant="secondary" className="text-[10px] bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500/20 border-emerald-200">
                        Sold
                    </Badge>
                ) : (
                    <Badge variant="outline" className="text-[10px] text-muted-foreground">
                        Unsold
                    </Badge>
                )}
            </div>

            {/* 8. Link */}
            <div className="flex justify-center">
                <button
                    onClick={handleLinkClick}
                    className="p-2 rounded-full hover:bg-[var(--bg-active)] text-muted-foreground hover:text-primary transition-colors"
                    title="Open Auction Link"
                >
                    <ExternalLink className="w-4 h-4" />
                </button>
            </div>
        </div>
    );
}

export interface AuctionTableHeaderV2Props {
    sortColumn?: string;
    sortDirection?: 'asc' | 'desc';
    onSort?: (column: string) => void;
}

export function AuctionTableHeaderV2({
    sortColumn,
    sortDirection,
    onSort,
}: AuctionTableHeaderV2Props) {

    const SortIcon = ({ column }: { column: string }) => {
        if (sortColumn !== column) return <span className="opacity-30 ml-1 text-[10px]">⇅</span>;
        return sortDirection === 'asc' ? <span className="ml-1 text-primary text-[10px]">↑</span> : <span className="ml-1 text-primary text-[10px]">↓</span>;
    };

    const HeaderCell = ({
        label,
        sortKey,
        align = 'left'
    }: {
        label: string,
        sortKey?: string,
        align?: 'left' | 'center' | 'right'
    }) => (
        <div
            className={cn(
                "text-[10px] font-bold uppercase tracking-wider text-muted-foreground select-none flex items-center",
                align === 'center' && "justify-center",
                align === 'right' && "justify-end"
            )}
            onClick={() => sortKey && onSort?.(sortKey)}
            style={{ cursor: sortKey ? 'pointer' : 'default' }}
        >
            {label}
            {sortKey && <SortIcon column={sortKey} />}
        </div>
    );

    return (
        <div
            className="sticky top-0 z-10 border-b shadow-sm hidden md:grid items-center gap-4 px-4"
            style={{
                background: 'var(--bg-elevated)',
                borderColor: 'var(--border-subtle)',
                height: '40px',
                gridTemplateColumns: AUCTION_GRID_LAYOUT,
            }}
        >
            <div /> {/* Image spacer */}
            <HeaderCell label="House" sortKey="auction_house" />
            <HeaderCell label="Sale" sortKey="sale_name" />
            <HeaderCell label="Lot" sortKey="lot_number" />
            <HeaderCell label="Date" sortKey="auction_date" />
            <HeaderCell label="Hammer" sortKey="hammer_price" align="right" />
            <HeaderCell label="Status" align="center" />
            <div /> {/* Link spacer */}
        </div>
    );
}
