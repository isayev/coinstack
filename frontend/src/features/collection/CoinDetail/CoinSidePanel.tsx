/**
 * CoinSidePanel - Individual obverse/reverse panel with image, legend, description
 * 
 * Features:
 * - Zoomable image with click-to-expand
 * - Metal badge overlay (obverse only)
 * - Legend with copy button and AI expand button
 * - Expanded legend (collapsible)
 * - Description section
 * - Iconography section (bullet list)
 * 
 * @module features/collection/CoinDetail/CoinSidePanel
 */

import { useState, memo } from 'react';
import { Copy, Check, Sparkles, ZoomIn, ImagePlus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { MetalBadge } from '@/components/ui/badges/MetalBadge';
import { ImageZoom } from '@/components/coins/ImageZoom';
import { cn } from '@/lib/utils';

interface CoinSidePanelProps {
  side: 'obverse' | 'reverse';
  image?: string;
  legend?: string | null;
  legendExpanded?: string | null;
  description?: string | null;
  iconography?: string[] | null;
  exergue?: string | null;
  metal?: string;
  /** Opens add-images dialog when this side has no image */
  onAddImage?: () => void;
  onEnrichLegend?: () => void;
  isEnriching?: boolean;
  className?: string;
}

export const CoinSidePanel = memo(function CoinSidePanel({
  side,
  image,
  legend,
  legendExpanded,
  description,
  iconography,
  exergue,
  metal,
  onAddImage,
  onEnrichLegend,
  isEnriching = false,
  className,
}: CoinSidePanelProps) {
  const [copied, setCopied] = useState(false);
  const [showExpanded, setShowExpanded] = useState(!!legendExpanded);

  const handleCopyLegend = async () => {
    if (!legend) return;
    await navigator.clipboard.writeText(legend);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={cn('coin-side-panel rounded-xl overflow-hidden', className)}
      style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      {/* Header */}
      <div
        className="px-4 py-3 border-b"
        style={{ borderColor: 'var(--border-subtle)' }}
      >
        <h3
          className="text-[11px] font-bold tracking-[1px] uppercase"
          style={{ color: 'var(--text-muted)' }}
        >
          {side === 'obverse' ? 'OBVERSE' : 'REVERSE'}
        </h3>
      </div>

      {/* Image Container */}
      <div className="relative">
        {image ? (
          <div className="relative aspect-square bg-[var(--bg-subtle)]">
            <ImageZoom
              src={image}
              alt={`${side} view`}
              className="w-full h-full"
            />
            {/* Metal badge overlay (obverse only) */}
            {side === 'obverse' && metal && (
              <div className="absolute top-3 right-3 z-10">
                <MetalBadge metal={metal as any} size="lg" showGlow />
              </div>
            )}
          </div>
        ) : (
          <div
            className="aspect-square flex items-center justify-center"
            style={{ background: 'var(--bg-subtle)' }}
          >
            {onAddImage ? (
              <Button
                type="button"
                variant="outline"
                className="gap-2"
                onClick={onAddImage}
                style={{
                  color: 'var(--text-secondary)',
                  borderColor: 'var(--border-subtle)',
                }}
              >
                <ImagePlus className="w-5 h-5" />
                Add {side} image
              </Button>
            ) : (
              <div className="text-center" style={{ color: 'var(--text-ghost)' }}>
                <ZoomIn className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No {side} image</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Content sections */}
      <div className="p-4 space-y-4">
        {/* Legend section */}
        {legend && (
          <div className="coin-side-panel__section">
            <div className="flex items-center justify-between mb-2">
              <span
                className="text-[10px] font-bold tracking-[0.5px] uppercase"
                style={{ color: 'var(--text-muted)' }}
              >
                LEGEND
              </span>
              <div className="flex items-center gap-1">
                <button
                  className="p-1.5 rounded hover:bg-[var(--bg-hover)] transition-colors"
                  onClick={handleCopyLegend}
                  title="Copy legend"
                  style={{ color: 'var(--text-muted)' }}
                >
                  {copied ? <Check size={14} /> : <Copy size={14} />}
                </button>
                {!legendExpanded && onEnrichLegend && (
                  <button
                    className="p-1.5 rounded hover:bg-[var(--bg-hover)] transition-colors disabled:opacity-50"
                    onClick={onEnrichLegend}
                    disabled={isEnriching}
                    title="Expand legend with AI"
                    style={{ color: 'var(--accent-ai, #a855f7)' }}
                  >
                    <Sparkles size={14} className={isEnriching ? 'animate-pulse' : ''} />
                  </button>
                )}
              </div>
            </div>

            <p
              className="font-mono text-sm leading-relaxed break-words"
              style={{ color: 'var(--text-primary)' }}
            >
              {legend}
            </p>

            {legendExpanded && (
              <details
                className="mt-2"
                open={showExpanded}
                onToggle={(e) => setShowExpanded(e.currentTarget.open)}
              >
                <summary
                  className="text-xs cursor-pointer hover:underline"
                  style={{ color: 'var(--text-link, #60a5fa)' }}
                >
                  {showExpanded ? 'Hide expansion' : 'Show expansion'}
                </summary>
                <p
                  className="mt-2 text-sm pl-3 border-l-2"
                  style={{
                    color: 'var(--text-secondary)',
                    borderColor: 'var(--border-subtle)',
                  }}
                >
                  {legendExpanded}
                </p>
              </details>
            )}
          </div>
        )}

        {/* Description section */}
        {description && (
          <div className="coin-side-panel__section">
            <span
              className="text-[10px] font-bold tracking-[0.5px] uppercase block mb-2"
              style={{ color: 'var(--text-muted)' }}
            >
              DESCRIPTION
            </span>
            <p
              className="text-sm leading-relaxed"
              style={{ color: 'var(--text-secondary)' }}
            >
              {description}
            </p>
          </div>
        )}

        {/* Exergue (reverse only) */}
        {side === 'reverse' && exergue && (
          <div className="coin-side-panel__section">
            <span
              className="text-[10px] font-bold tracking-[0.5px] uppercase block mb-2"
              style={{ color: 'var(--text-muted)' }}
            >
              EXERGUE
            </span>
            <p
              className="font-mono text-sm"
              style={{ color: 'var(--text-primary)' }}
            >
              {exergue}
            </p>
          </div>
        )}

        {/* Iconography section */}
        {iconography && iconography.length > 0 && (
          <div className="coin-side-panel__section">
            <span
              className="text-[10px] font-bold tracking-[0.5px] uppercase block mb-2"
              style={{ color: 'var(--text-muted)' }}
            >
              ICONOGRAPHY
            </span>
            <ul
              className="text-sm space-y-1 pl-4"
              style={{ color: 'var(--text-secondary)' }}
            >
              {iconography.map((item, i) => (
                <li key={i} className="list-disc">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
});
