import { cn } from "../../lib/utils";

type StatusTone = "success" | "warning" | "danger" | "neutral" | "info";

interface StatusBadgeProps {
  label: string;
  tone?: StatusTone;
  className?: string;
}

const toneClasses: Record<StatusTone, string> = {
  success: "border-emerald-300/25 bg-emerald-400/12 text-emerald-200",
  warning: "border-amber-300/25 bg-amber-400/12 text-amber-200",
  danger: "border-rose-300/25 bg-rose-400/12 text-rose-200",
  neutral: "border-white/10 bg-white/8 text-slate-300",
  info: "border-cyan-300/25 bg-cyan-400/12 text-cyan-200",
};

export function StatusBadge({
  label,
  tone = "neutral",
  className,
}: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex min-h-7 items-center rounded-full border px-2.5 text-xs font-bold",
        toneClasses[tone],
        className,
      )}
    >
      {label}
    </span>
  );
}
