import { forwardRef } from "react";
import type { TextareaHTMLAttributes } from "react";

import { cn } from "../../lib/utils";

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "w-full resize-none rounded-md border border-white/10 bg-white/[0.07] px-3 py-3 text-sm leading-6 text-slate-100 transition placeholder:text-slate-500 hover:bg-white/[0.09] focus:border-cyan-300/60 focus:bg-white/[0.1]",
      className,
    )}
    {...props}
  />
));

Textarea.displayName = "Textarea";
