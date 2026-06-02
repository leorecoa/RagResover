import type { ReactNode } from "react";
import { Inbox } from "lucide-react";

import { cn } from "../../lib/utils";

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  className?: string;
}

export function EmptyState({
  title,
  description,
  icon,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "grid min-h-48 place-items-center rounded-lg border border-dashed border-white/12 bg-white/[0.04] p-8 text-center",
        className,
      )}
    >
      <div className="grid max-w-sm gap-3 justify-items-center">
        <div className="grid h-11 w-11 place-items-center rounded-md border border-white/10 bg-white/10 text-cyan-200">
          {icon ?? <Inbox className="h-5 w-5" aria-hidden="true" />}
        </div>
        <div>
          <h3 className="text-base font-bold text-white">{title}</h3>
          {description ? (
            <p className="mt-1 text-sm leading-6 text-slate-400">{description}</p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
