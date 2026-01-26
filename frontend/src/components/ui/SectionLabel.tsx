/**
 * SectionLabel Component
 * 
 * A consistent label component for section headers in cards and panels.
 * Uses the design system typography and color standards.
 */

import { cn } from '@/lib/utils';
import { ReactNode } from 'react';

interface SectionLabelProps {
  /** Label content */
  children: ReactNode;
  /** Additional CSS classes */
  className?: string;
  /** Size variant */
  size?: 'sm' | 'md';
}

/**
 * Section label for card headers and data sections.
 * 
 * @example
 * <SectionLabel>PHYSICAL SPECIFICATIONS</SectionLabel>
 * 
 * @example
 * <SectionLabel size="sm">Weight</SectionLabel>
 */
export function SectionLabel({ 
  children, 
  className,
  size = 'md'
}: SectionLabelProps) {
  const sizeStyles = size === 'sm'
    ? 'text-[11px]'  // Slightly smaller for inline labels
    : 'text-xs';     // Standard 12px for section headers
  
  return (
    <span
      className={cn(
        sizeStyles,
        "font-bold uppercase tracking-wider block mb-2",
        className
      )}
      style={{ color: 'var(--text-muted)' }}
    >
      {children}
    </span>
  );
}

/**
 * Inline label for key-value pairs within data sections.
 * Does not have bottom margin.
 */
export function InlineLabel({ 
  children, 
  className 
}: { children: ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        "text-[11px] font-medium uppercase tracking-wide",
        className
      )}
      style={{ color: 'var(--text-muted)' }}
    >
      {children}
    </span>
  );
}
