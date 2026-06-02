import { forwardRef } from "react";
import type { InputHTMLAttributes } from "react";

import { cn } from "../../lib/utils";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type = "text", ...props }, ref) => (
    <input
      ref={ref}
      type={type}
      className={cn(
        "h-11 w-full rounded-md border border-white/10 bg-white/[0.07] px-3 text-sm text-slate-100 transition placeholder:text-slate-500 hover:bg-white/[0.09] focus:border-cyan-300/60 focus:bg-white/[0.1]",
        className,
      )}
      {...props}
    />
  ),
);

Input.displayName = "Input";
