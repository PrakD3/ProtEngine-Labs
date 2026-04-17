import { cn } from "@/app/lib/utils";
import type { LabelHTMLAttributes } from "react";
const Label = ({ className, ...props }: LabelHTMLAttributes<HTMLLabelElement>) => (
  <label className={cn("text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70", className)} {...props} />
);
export { Label };
