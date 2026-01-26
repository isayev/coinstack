/**
 * CoinNavigation - Left/right navigation between coin detail pages
 * 
 * Features:
 * - Arrow buttons to navigate prev/next coin
 * - Keyboard shortcuts (left/right arrow keys)
 * - Uses prev_id/next_id from coin API (efficient - no extra queries)
 * - Positioned near images area for easy clicking
 * 
 * @module components/coins/CoinNavigation
 */

import { useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CoinNavigationProps {
  /** Current coin ID (for reference, not used in navigation) */
  currentCoinId: number;
  /** Previous coin ID (from API response) */
  prevId?: number | null;
  /** Next coin ID (from API response) */
  nextId?: number | null;
  /** Additional CSS classes */
  className?: string;
}

export function CoinNavigation({ currentCoinId: _currentCoinId, prevId, nextId, className }: CoinNavigationProps) {
  const navigate = useNavigate();

  const goToPrev = useCallback(() => {
    if (prevId) navigate(`/coins/${prevId}`);
  }, [prevId, navigate]);

  const goToNext = useCallback(() => {
    if (nextId) navigate(`/coins/${nextId}`);
  }, [nextId, navigate]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't interfere with input fields
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      if (e.key === 'ArrowLeft' && prevId) {
        e.preventDefault();
        goToPrev();
      } else if (e.key === 'ArrowRight' && nextId) {
        e.preventDefault();
        goToNext();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [prevId, nextId, goToPrev, goToNext]);

  return (
    <nav 
      className={cn('coin-navigation flex items-center gap-3', className)}
      aria-label="Coin navigation"
      role="navigation"
    >
      {/* Previous button */}
      <NavButton
        direction="prev"
        disabled={!prevId}
        onClick={goToPrev}
        tooltip={prevId ? 'Previous coin (←)' : undefined}
      />

      {/* Next button */}
      <NavButton
        direction="next"
        disabled={!nextId}
        onClick={goToNext}
        tooltip={nextId ? 'Next coin (→)' : undefined}
      />
    </nav>
  );
}

/**
 * Individual navigation button
 */
interface NavButtonProps {
  direction: 'prev' | 'next';
  disabled: boolean;
  onClick: () => void;
  tooltip?: string;
}

function NavButton({ direction, disabled, onClick, tooltip }: NavButtonProps) {
  const Icon = direction === 'prev' ? ChevronLeft : ChevronRight;
  const label = direction === 'prev' ? 'Go to previous coin' : 'Go to next coin';

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={tooltip}
      aria-label={label}
      aria-disabled={disabled}
      className={cn(
        'coin-nav-btn w-10 h-10 rounded-full flex items-center justify-center transition-all',
        'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[var(--accent-primary)]',
        disabled && 'opacity-30 cursor-not-allowed'
      )}
      style={{
        background: disabled ? 'var(--bg-subtle)' : 'var(--bg-elevated)',
        border: '1px solid var(--border-subtle)',
        color: disabled ? 'var(--text-ghost)' : 'var(--text-primary)',
      }}
      onMouseEnter={(e) => {
        if (!disabled) {
          e.currentTarget.style.background = 'var(--bg-hover)';
          e.currentTarget.style.borderColor = 'var(--border-default)';
        }
      }}
      onMouseLeave={(e) => {
        if (!disabled) {
          e.currentTarget.style.background = 'var(--bg-elevated)';
          e.currentTarget.style.borderColor = 'var(--border-subtle)';
        }
      }}
    >
      <Icon size={20} aria-hidden="true" />
    </button>
  );
}

/**
 * Floating navigation arrows that appear on sides of content
 * Alternative placement for image area
 */
interface FloatingNavArrowsProps {
  currentCoinId: number;
  /** Previous coin ID (from API response) */
  prevId?: number | null;
  /** Next coin ID (from API response) */
  nextId?: number | null;
  className?: string;
}

export function FloatingNavArrows({ currentCoinId: _currentCoinId, prevId, nextId, className }: FloatingNavArrowsProps) {
  const navigate = useNavigate();

  const goToPrev = useCallback(() => {
    if (prevId) navigate(`/coins/${prevId}`);
  }, [prevId, navigate]);

  const goToNext = useCallback(() => {
    if (nextId) navigate(`/coins/${nextId}`);
  }, [nextId, navigate]);

  return (
    <div className={cn('floating-nav-arrows relative', className)}>
      {/* Left arrow */}
      <button
        onClick={goToPrev}
        disabled={!prevId}
        className={cn(
          'absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2 z-10',
          'w-10 h-10 rounded-full flex items-center justify-center',
          'transition-all shadow-lg',
          !prevId && 'opacity-0 pointer-events-none'
        )}
        style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-subtle)',
          color: 'var(--text-primary)',
        }}
        title="Previous coin (←)"
      >
        <ChevronLeft size={20} />
      </button>

      {/* Right arrow */}
      <button
        onClick={goToNext}
        disabled={!nextId}
        className={cn(
          'absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 z-10',
          'w-10 h-10 rounded-full flex items-center justify-center',
          'transition-all shadow-lg',
          !nextId && 'opacity-0 pointer-events-none'
        )}
        style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-subtle)',
          color: 'var(--text-primary)',
        }}
        title="Next coin (→)"
      >
        <ChevronRight size={20} />
      </button>
    </div>
  );
}
