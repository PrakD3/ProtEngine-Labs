import { cn } from "@/app/lib/utils";
import type { HTMLAttributes } from "react";

const ScrollArea = ({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("overflow-auto scrollbar-thin", className)} {...props}>
    {children}
  </div>
);

export { ScrollArea };
