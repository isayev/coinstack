/**
 * TableRowSkeleton — shared loading row for table/list views (IF-003).
 * Matches table row height (h-14) and uses design token --bg-elevated.
 */
import { Skeleton } from "@/components/ui/skeleton";

export function TableRowSkeleton() {
  return (
    <Skeleton
      className="h-14 w-full rounded-md"
      style={{ background: "var(--bg-elevated)" }}
    />
  );
}
