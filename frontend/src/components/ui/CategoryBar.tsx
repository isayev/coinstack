/**
 * CategoryBar Component
 * 
 * A visual indicator bar that shows the category/era of a coin
 * using the category color from the design system.
 * 
 * Used in card headers, detail panels, and list items to provide
 * visual categorization at a glance.
 */

import { cn } from '@/lib/utils';

interface CategoryBarProps {
  /** The category type (maps to --cat-{type} CSS variable) */
  categoryType: string;
  /** Position of the bar */
  position?: 'left' | 'top';
  /** Additional CSS classes */
  className?: string;
}

/**
 * Normalize category string to CSS variable name.
 * Handles various input formats and maps to design system category names.
 */
function normalizeCategoryType(category: string): string {
  const normalized = category.toLowerCase().replace(/[\s_-]+/g, '_');
  
  // Map common variations to standard names
  const categoryMap: Record<string, string> = {
    'roman_imperial': 'imperial',
    'roman_republic': 'republic',
    'roman_provincial': 'provincial',
    'greek_imperial': 'provincial',
    'late_roman': 'late',
    'dominate': 'late',
    'judaean': 'judaea',
    'parthian': 'eastern',
    'sasanian': 'eastern',
  };
  
  return categoryMap[normalized] || normalized;
}

/**
 * Category color bar component for visual era/category indication.
 * 
 * @example
 * // Left-positioned bar (default)
 * <CategoryBar categoryType="imperial" />
 * 
 * @example
 * // Top-positioned bar
 * <CategoryBar categoryType="republic" position="top" />
 */
export function CategoryBar({ 
  categoryType, 
  position = 'left', 
  className 
}: CategoryBarProps) {
  const normalizedType = normalizeCategoryType(categoryType);
  
  const positionStyles = position === 'left' 
    ? 'absolute left-0 top-0 bottom-0 w-[6px] rounded-l-xl'
    : 'absolute left-0 right-0 top-0 h-[6px] rounded-t-xl';
  
  return (
    <div
      className={cn(positionStyles, className)}
      style={{ background: `var(--cat-${normalizedType}, var(--cat-other))` }}
      aria-hidden="true"
    />
  );
}
