/**
 * DataCard and DataField Components
 * 
 * Reusable card components for displaying coin data with consistent styling.
 * Used across the coin detail page for physical specs, grading, acquisition, etc.
 */

import { ReactNode } from 'react';
import { CategoryBar } from '@/components/ui/CategoryBar';
import { cn } from '@/lib/utils';

/**
 * DataCard - Card component with category color bar
 */
interface DataCardProps {
  /** Category type for color bar */
  categoryType: string;
  /** Card title */
  title: string;
  /** Card content */
  children: ReactNode;
  /** Additional CSS classes */
  className?: string;
}

export function DataCard({ categoryType, title, children, className }: DataCardProps) {
  return (
    <div
      className={cn(
        "relative rounded-xl p-5",
        className
      )}
      style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      {/* Category bar */}
      <CategoryBar categoryType={categoryType} />

      {/* Title */}
      <h2
        className="text-base font-semibold mb-4 pl-2"
        style={{ color: 'var(--text-primary)' }}
      >
        {title}
      </h2>

      {/* Content */}
      <div className="pl-2">
        {children}
      </div>
    </div>
  );
}

/**
 * DataField - Key-value field component
 */
interface DataFieldProps {
  /** Field label */
  label: string;
  /** Field value (displays "—" if null/undefined) */
  value: string | number | null | undefined;
  /** Optional className for the container */
  className?: string;
  /** If true, shows value in monospace font */
  mono?: boolean;
  /** If true, capitalizes the value */
  capitalize?: boolean;
}

export function DataField({ 
  label, 
  value, 
  className,
  mono = false,
  capitalize = true 
}: DataFieldProps) {
  const displayValue = value != null ? String(value) : null;
  
  return (
    <div className={className}>
      <div
        className="text-xs font-semibold uppercase tracking-wider mb-1"
        style={{ color: 'var(--text-muted)' }}
      >
        {label}
      </div>
      <div
        className={cn(
          "text-sm font-medium",
          mono && "font-mono",
          capitalize && "capitalize"
        )}
        style={{ color: displayValue ? 'var(--text-primary)' : 'var(--text-ghost)' }}
      >
        {displayValue || '—'}
      </div>
    </div>
  );
}

/**
 * DataFieldRow - Horizontal row of DataFields with consistent spacing
 */
interface DataFieldRowProps {
  children: ReactNode;
  className?: string;
}

export function DataFieldRow({ children, className }: DataFieldRowProps) {
  return (
    <div className={cn("grid grid-cols-2 gap-4", className)}>
      {children}
    </div>
  );
}
