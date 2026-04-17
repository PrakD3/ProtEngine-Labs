import { cn } from "@/app/lib/utils";
import type { HTMLAttributes } from "react";
function Skeleton({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("animate-pulse rounded-md bg-[var(--muted)]", className)} {...props} />;
}
export { Skeleton };
