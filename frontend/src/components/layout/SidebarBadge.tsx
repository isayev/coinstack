import { cn } from "@/lib/utils";

interface SidebarBadgeProps {
  count: number;
  variant?: "default" | "warning" | "urgent";
  className?: string;
}

/**
 * SidebarBadge - Badge component for showing pending review counts
 * 
 * Visual states:
 * - Default (1-9): Silver background
 * - Warning (10-49): Amber background
 * - Urgent (50+): Red background with pulse animation
 * 
 * When sidebar is collapsed, shows as dot indicator only.
 */
export function SidebarBadge({ count, variant, className }: SidebarBadgeProps) {
  if (count === 0) return null;

  // Determine variant based on count if not explicitly set
  const effectiveVariant = variant || (
    count >= 50 ? "urgent" :
    count >= 10 ? "warning" :
    "default"
  );

  const variantClasses = {
    default: "bg-[var(--metal-ar)] text-white",
    warning: "bg-[var(--caution)] text-white",
    urgent: "bg-[var(--error)] text-white animate-pulse",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center justify-center",
        "min-w-[20px] h-5 px-1.5",
        "rounded-full text-[11px] font-semibold",
        "transition-all duration-200",
        variantClasses[effectiveVariant],
        className
      )}
      style={{
        animation: effectiveVariant === "urgent" ? "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite" : undefined,
      }}
    >
      {count > 99 ? "99+" : count}
    </span>
  );
}
