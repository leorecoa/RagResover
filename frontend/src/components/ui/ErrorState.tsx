import { AlertTriangle } from "lucide-react";

import { cn } from "../../lib/utils";

interface ErrorStateProps {
  title?: string;
  message: string;
  className?: string;
}

export function ErrorState({
  title = "Erro",
  message,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex gap-3 rounded-lg border border-rose-300/20 bg-rose-500/10 p-4 text-sm text-rose-100",
        className,
      )}
    >
      <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-rose-200" aria-hidden="true" />
      <div>
        <p className="font-bold text-rose-50">{title}</p>
        <p className="mt-1 leading-6 text-rose-100/85">{message}</p>
      </div>
    </div>
  );
}
