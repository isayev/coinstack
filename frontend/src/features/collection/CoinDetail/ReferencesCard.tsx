/**
 * ReferencesCard - Display catalog references with validated external links
 * 
 * Features:
 * - Primary reference highlighted
 * - Secondary references as concordance
 * - Validated external links (OCRE, CRRO, RPC)
 * - General search links (ACSearch, CoinArchives, Wildwinds)
 * 
 * @module features/collection/CoinDetail/ReferencesCard
 */

import { memo } from 'react';
import { ExternalLink } from 'lucide-react';
import { buildExternalLinks, formatReference, type CatalogReference } from '@/lib/referenceLinks';
import { cn } from '@/lib/utils';

interface ReferencesCardProps {
  /** Array of catalog references */
  references: CatalogReference[] | null | undefined;
  /** Category type for styling */
  categoryType?: string;
  /** Additional CSS classes */
  className?: string;
}

export const ReferencesCard = memo(function ReferencesCard({ references, categoryType = 'imperial', className }: ReferencesCardProps) {
  // Filter valid references
  const validRefs = (references || []).filter(
    (ref): ref is CatalogReference => ref !== null && ref !== undefined && !!ref.catalog && !!ref.number
  );

  if (validRefs.length === 0) {
    return (
      <div
        className={cn('relative rounded-xl p-5', className)}
        style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        {/* Category bar */}
        <div
          className="absolute left-0 top-0 bottom-0 w-[6px] rounded-l-xl"
          style={{ background: `var(--cat-${categoryType})` }}
        />
        <h2 className="text-base font-semibold mb-4 pl-2" style={{ color: 'var(--text-primary)' }}>
          References
        </h2>
        <p className="text-sm pl-2" style={{ color: 'var(--text-muted)' }}>
          No references recorded
        </p>
      </div>
    );
  }

  // Separate primary and secondary references
  const primaryRef = validRefs.find(r => r.is_primary) || validRefs[0];
  const secondaryRefs = validRefs.filter(r => r !== primaryRef);

  // Build external links
  const externalLinks = buildExternalLinks(validRefs);

  return (
    <div
      className={cn('relative rounded-xl p-5', className)}
      style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      {/* Category bar */}
      <div
        className="absolute left-0 top-0 bottom-0 w-[6px] rounded-l-xl"
        style={{ background: `var(--cat-${categoryType})` }}
      />

      <h2 className="text-base font-semibold mb-4 pl-2" style={{ color: 'var(--text-primary)' }}>
        References
      </h2>

      <div className="pl-2 space-y-4">
        {/* Primary Reference */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span
              className="text-[10px] font-bold uppercase tracking-wider"
              style={{ color: 'var(--text-muted)' }}
            >
              Primary
            </span>
          </div>
          <span
            className="font-mono text-base font-semibold"
            style={{ color: 'var(--text-primary)' }}
          >
            {formatReference(primaryRef)}
          </span>
          {primaryRef.notes && (
            <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
              {primaryRef.notes}
            </p>
          )}
        </div>

        {/* Secondary References (Concordance) */}
        {secondaryRefs.length > 0 && (
          <div>
            <span
              className="text-[10px] font-bold uppercase tracking-wider block mb-1"
              style={{ color: 'var(--text-muted)' }}
            >
              Concordance
            </span>
            <p
              className="font-mono text-sm"
              style={{ color: 'var(--text-secondary)' }}
            >
              {secondaryRefs.map(ref => formatReference(ref)).join(' · ')}
            </p>
          </div>
        )}

        {/* External Links */}
        <div className="pt-3 border-t" style={{ borderColor: 'var(--border-subtle)' }}>
          <span
            className="text-[10px] font-bold uppercase tracking-wider block mb-2"
            style={{ color: 'var(--text-muted)' }}
          >
            External Resources
          </span>
          <div className="flex flex-wrap gap-2">
            {externalLinks.map((link) => (
              <a
                key={link.name}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className={cn(
                  'inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs rounded transition-colors',
                  link.validated && 'ring-1 ring-inset'
                )}
                style={{
                  background: 'var(--bg-subtle)',
                  color: link.validated ? 'var(--text-primary)' : 'var(--text-secondary)',
                  ...(link.validated && { ringColor: 'var(--border-subtle)' }),
                }}
                title={link.validated ? `Validated link for ${link.name}` : `Search on ${link.name}`}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'var(--bg-hover)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'var(--bg-subtle)';
                }}
              >
                {link.name}
                <ExternalLink size={12} />
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
});
