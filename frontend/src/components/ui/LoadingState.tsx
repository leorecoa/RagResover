import { LoaderCircle } from "lucide-react";

import { cn } from "../../lib/utils";

interface LoadingStateProps {
  label?: string;
  className?: string;
}

export function LoadingState({
  label = "Carregando",
  className,
}: LoadingStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-32 items-center justify-center gap-3 rounded-lg border border-white/10 bg-white/[0.04] text-sm font-bold text-slate-300",
        className,
      )}
    >
      <LoaderCircle className="h-5 w-5 animate-spin text-cyan-200" aria-hidden="true" />
      {label}
    </div>
  );
}
