/**
 * DieAxisClock - SVG clock visualization for coin die axis
 * 
 * Die axis represents the orientation between obverse and reverse dies,
 * measured in clock positions (0-12h). Most Roman coins have 6h or 12h die axis.
 * 
 * @module components/coins/DieAxisClock
 */

import { cn } from '@/lib/utils';

interface DieAxisClockProps {
  /** Die axis value (0-12 clock hours) */
  axis: number | null | undefined;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Allow clicking to set value (edit mode) */
  interactive?: boolean;
  /** Callback when axis changes (edit mode) */
  onChange?: (axis: number) => void;
  /** Additional CSS classes */
  className?: string;
}

const SIZES = {
  sm: 32,
  md: 48,
  lg: 64,
};

export function DieAxisClock({
  axis,
  size = 'md',
  interactive = false,
  onChange,
  className,
}: DieAxisClockProps) {
  const diameter = SIZES[size];
  const center = diameter / 2;
  const radius = center - 4;

  // Handle null/undefined axis
  const displayAxis = axis ?? 12; // Default to 12h if not set
  const hasValue = axis !== null && axis !== undefined;

  // Convert clock hour to angle (12 o'clock = -90°, 6 o'clock = 90°)
  const angle = (displayAxis * 30 - 90) * (Math.PI / 180);
  const arrowLength = radius - 6;
  const arrowX = center + arrowLength * Math.cos(angle);
  const arrowY = center + arrowLength * Math.sin(angle);

  const handleClick = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!interactive || !onChange) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left - center;
    const y = e.clientY - rect.top - center;
    const clickAngle = Math.atan2(y, x) * (180 / Math.PI);
    // Convert angle to clock hour (add 90 to shift from math coords to clock coords)
    let hour = Math.round(((clickAngle + 90 + 360) % 360) / 30);
    if (hour === 0) hour = 12;
    onChange(hour);
  };

  return (
    <svg
      width={diameter}
      height={diameter}
      viewBox={`0 0 ${diameter} ${diameter}`}
      className={cn(
        'die-axis-clock',
        interactive && 'cursor-pointer hover:opacity-80',
        !hasValue && 'opacity-50',
        className
      )}
      onClick={handleClick}
      role={interactive ? 'button' : 'img'}
      aria-label={hasValue ? `Die axis: ${displayAxis} o'clock` : 'Die axis: unknown'}
    >
      {/* Clock face */}
      <circle
        cx={center}
        cy={center}
        r={radius}
        fill="var(--bg-subtle)"
        stroke="var(--border-subtle)"
        strokeWidth={1}
      />

      {/* Hour markers (12, 3, 6, 9) */}
      {[12, 3, 6, 9].map((hour) => {
        const markerAngle = (hour * 30 - 90) * (Math.PI / 180);
        const markerX = center + (radius - 4) * Math.cos(markerAngle);
        const markerY = center + (radius - 4) * Math.sin(markerAngle);
        const isHighlight = hour === 12 || hour === 6;
        return (
          <circle
            key={hour}
            cx={markerX}
            cy={markerY}
            r={isHighlight ? 2.5 : 1.5}
            fill={isHighlight ? 'var(--text-secondary)' : 'var(--text-muted)'}
          />
        );
      })}

      {/* Arrow line */}
      {hasValue && (
        <>
          <line
            x1={center}
            y1={center}
            x2={arrowX}
            y2={arrowY}
            stroke="var(--cat-imperial)"
            strokeWidth={2}
            strokeLinecap="round"
          />

          {/* Arrow head (small circle) */}
          <circle
            cx={arrowX}
            cy={arrowY}
            r={3}
            fill="var(--cat-imperial)"
          />
        </>
      )}

      {/* Center dot */}
      <circle
        cx={center}
        cy={center}
        r={3}
        fill={hasValue ? 'var(--text-muted)' : 'var(--text-ghost)'}
      />

      {/* "?" indicator if no value */}
      {!hasValue && (
        <text
          x={center}
          y={center + 1}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize={size === 'sm' ? 10 : size === 'md' ? 12 : 14}
          fill="var(--text-muted)"
          fontWeight="bold"
        >
          ?
        </text>
      )}
    </svg>
  );
}

/**
 * DieAxisDisplay - Inline display with clock + text
 */
interface DieAxisDisplayProps {
  axis: number | null | undefined;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

export function DieAxisDisplay({
  axis,
  size = 'md',
  showLabel = true,
  className,
}: DieAxisDisplayProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <DieAxisClock axis={axis} size={size} />
      {showLabel && (
        <span
          className="text-sm font-mono"
          style={{ color: axis != null ? 'var(--text-primary)' : 'var(--text-muted)' }}
        >
          {axis != null ? `↑${axis}h` : '—'}
        </span>
      )}
    </div>
  );
}
