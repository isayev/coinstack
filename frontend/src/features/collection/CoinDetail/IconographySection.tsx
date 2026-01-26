/**
 * IconographySection - Display iconographic elements from coin designs
 * 
 * Features:
 * - Split view for obverse/reverse iconography
 * - Visual icon indicators
 * - Tooltip explanations
 * - Grouped by type (deity, symbol, object, etc.)
 * 
 * @module features/collection/CoinDetail/IconographySection
 */

import { 
  Crown, 
  Swords, 
  Landmark, 
  Star, 
  Leaf, 
  Bird, 
  Shield, 
  Flame,
  Circle,
  Scroll,
  Award
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface IconographySectionProps {
  /** Obverse iconography elements */
  obverseIconography?: string[] | null;
  /** Reverse iconography elements */
  reverseIconography?: string[] | null;
  /** Category type for styling */
  categoryType?: string;
  /** Additional CSS classes */
  className?: string;
}

export function IconographySection({
  obverseIconography,
  reverseIconography,
  categoryType = 'imperial',
  className,
}: IconographySectionProps) {
  const hasObverse = obverseIconography && obverseIconography.length > 0;
  const hasReverse = reverseIconography && reverseIconography.length > 0;

  if (!hasObverse && !hasReverse) {
    return null;
  }

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

      <h2
        className="text-base font-semibold mb-4 pl-2"
        style={{ color: 'var(--text-primary)' }}
      >
        Iconography
      </h2>

      <div className="pl-2 grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Obverse Iconography */}
        {hasObverse && (
          <div>
            <span
              className="text-[10px] font-bold uppercase tracking-wider block mb-3"
              style={{ color: 'var(--text-muted)' }}
            >
              Obverse
            </span>
            <ul className="space-y-2">
              {obverseIconography.map((item, i) => (
                <IconographyItem key={i} text={item} />
              ))}
            </ul>
          </div>
        )}

        {/* Reverse Iconography */}
        {hasReverse && (
          <div>
            <span
              className="text-[10px] font-bold uppercase tracking-wider block mb-3"
              style={{ color: 'var(--text-muted)' }}
            >
              Reverse
            </span>
            <ul className="space-y-2">
              {reverseIconography.map((item, i) => (
                <IconographyItem key={i} text={item} />
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Individual iconography item with icon
 */
function IconographyItem({ text }: { text: string }) {
  const icon = getIconForText(text);

  return (
    <li
      className="flex items-start gap-2 text-sm"
      style={{ color: 'var(--text-secondary)' }}
    >
      <span
        className="flex-shrink-0 mt-0.5"
        style={{ color: 'var(--text-muted)' }}
      >
        {icon}
      </span>
      <span className="capitalize">{text}</span>
    </li>
  );
}

/**
 * Get appropriate icon for iconography text
 */
function getIconForText(text: string): React.ReactNode {
  const lowerText = text.toLowerCase();

  // Royalty/Authority
  if (lowerText.includes('crown') || lowerText.includes('diadem') || lowerText.includes('laurel')) {
    return <Crown size={14} />;
  }
  if (lowerText.includes('emperor') || lowerText.includes('augustus') || lowerText.includes('caesar')) {
    return <Award size={14} />;
  }

  // Military
  if (lowerText.includes('sword') || lowerText.includes('spear') || lowerText.includes('weapon') || lowerText.includes('military')) {
    return <Swords size={14} />;
  }
  if (lowerText.includes('shield') || lowerText.includes('armor')) {
    return <Shield size={14} />;
  }

  // Architecture
  if (lowerText.includes('temple') || lowerText.includes('column') || lowerText.includes('building') || lowerText.includes('altar')) {
    return <Landmark size={14} />;
  }

  // Nature/Animals
  if (lowerText.includes('eagle') || lowerText.includes('bird') || lowerText.includes('phoenix')) {
    return <Bird size={14} />;
  }
  if (lowerText.includes('branch') || lowerText.includes('olive') || lowerText.includes('palm') || lowerText.includes('wreath')) {
    return <Leaf size={14} />;
  }

  // Religious/Mythological
  if (lowerText.includes('star') || lowerText.includes('celestial') || lowerText.includes('sol')) {
    return <Star size={14} />;
  }
  if (lowerText.includes('fire') || lowerText.includes('torch') || lowerText.includes('flame')) {
    return <Flame size={14} />;
  }

  // Text/Inscriptions
  if (lowerText.includes('legend') || lowerText.includes('inscription') || lowerText.includes('text')) {
    return <Scroll size={14} />;
  }

  // Default
  return <Circle size={14} />;
}

/**
 * Compact inline iconography display (for use in other components)
 */
export function IconographyInline({
  items,
  maxItems = 5,
  className,
}: {
  items: string[] | null | undefined;
  maxItems?: number;
  className?: string;
}) {
  if (!items || items.length === 0) return null;

  const displayItems = items.slice(0, maxItems);
  const remaining = items.length - maxItems;

  return (
    <div className={cn('flex flex-wrap gap-1.5', className)}>
      {displayItems.map((item, i) => (
        <span
          key={i}
          className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded"
          style={{
            background: 'var(--bg-subtle)',
            color: 'var(--text-secondary)',
          }}
          title={item}
        >
          {getIconForText(item)}
          <span className="truncate max-w-[100px]">{item}</span>
        </span>
      ))}
      {remaining > 0 && (
        <span
          className="text-xs px-2 py-0.5"
          style={{ color: 'var(--text-muted)' }}
        >
          +{remaining} more
        </span>
      )}
    </div>
  );
}
