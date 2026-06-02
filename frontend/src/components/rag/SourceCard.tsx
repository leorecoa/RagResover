import { BookOpenCheck } from "lucide-react";

import type { Source } from "../../lib/types";
import { compactId, formatScore, getMetadataLabel } from "../../lib/utils";
import { GlassCard } from "../ui/GlassCard";
import { StatusBadge } from "../ui/StatusBadge";

interface SourceCardProps {
  source: Source;
}

export function SourceCard({ source }: SourceCardProps) {
  const page = getMetadataLabel(source.metadata, "page");
  const paragraph = getMetadataLabel(source.metadata, "paragraph");
  const section = getMetadataLabel(source.metadata, "section");

  return (
    <GlassCard className="p-4">
      <div className="flex items-start gap-3">
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-md border border-emerald-300/20 bg-emerald-400/10 text-emerald-100">
          <BookOpenCheck className="h-4 w-4" aria-hidden="true" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <h3 className="truncate text-sm font-black text-white">
                [{source.index}] {source.file_name}
              </h3>
              <p className="mt-1 text-xs text-slate-500">{compactId(source.chunk_id)}</p>
            </div>
            <StatusBadge label={formatScore(source.score)} tone="success" />
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            {page !== "-" ? <StatusBadge label={`page ${page}`} /> : null}
            {paragraph !== "-" ? <StatusBadge label={`paragraph ${paragraph}`} /> : null}
            {section !== "-" ? <StatusBadge label={section} tone="info" /> : null}
          </div>

          <p className="mt-3 line-clamp-5 text-sm leading-6 text-slate-300">
            {source.excerpt}
          </p>
        </div>
      </div>
    </GlassCard>
  );
}
