import type { HTMLAttributes } from "react";

import { cn } from "../../lib/utils";

interface GlassCardProps extends HTMLAttributes<HTMLDivElement> {
  elevated?: boolean;
}

export function GlassCard({
  className,
  elevated = false,
  ...props
}: GlassCardProps) {
  return (
    <div
      className={cn(
        "glass-surface rounded-lg",
        elevated && "shadow-glow",
        className,
      )}
      {...props}
    />
  );
}
