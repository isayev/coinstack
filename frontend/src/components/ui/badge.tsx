import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
        
        // Metal variants
        gold: "border-metal-gold/40 bg-metal-gold/15 text-metal-gold hover:bg-metal-gold/20",
        silver: "border-metal-silver/40 bg-metal-silver/15 text-metal-silver hover:bg-metal-silver/20",
        bronze: "border-metal-bronze/40 bg-metal-bronze/15 text-metal-bronze hover:bg-metal-bronze/20",
        
        // Grade variants
        "grade-ms": "border-grade-ms/40 bg-grade-ms/15 text-grade-ms",
        "grade-au": "border-grade-au/40 bg-grade-au/15 text-grade-au",
        "grade-ef": "border-grade-ef/40 bg-grade-ef/15 text-grade-ef",
        "grade-fine": "border-grade-fine/40 bg-grade-fine/15 text-grade-fine",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }