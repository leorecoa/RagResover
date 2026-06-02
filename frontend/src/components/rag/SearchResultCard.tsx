import { FileText } from "lucide-react";

import type { SearchResult } from "../../lib/types";
import { compactId, formatScore, getMetadataLabel } from "../../lib/utils";
import { GlassCard } from "../ui/GlassCard";
import { StatusBadge } from "../ui/StatusBadge";

interface SearchResultCardProps {
  result: SearchResult;
}

export function SearchResultCard({ result }: SearchResultCardProps) {
  const page = getMetadataLabel(result.metadata, "page");
  const paragraph = getMetadataLabel(result.metadata, "paragraph");
  const source = getMetadataLabel(result.metadata, "source");
  const contentType = getMetadataLabel(result.metadata, "content_type");

  return (
    <GlassCard className="p-4 transition hover:border-cyan-300/20 hover:bg-white/[0.08]">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 gap-3">
          <div className="grid h-10 w-10 shrink-0 place-items-center rounded-md border border-violet-300/20 bg-violet-400/10 text-violet-100">
            <FileText className="h-5 w-5" aria-hidden="true" />
          </div>
          <div className="min-w-0">
            <h3 className="truncate text-sm font-black text-white">{result.file_name}</h3>
            <p className="mt-1 text-xs text-slate-500">
              {compactId(result.document_id)} / {compactId(result.chunk_id)}
            </p>
          </div>
        </div>
        <StatusBadge label={`score ${formatScore(result.score)}`} tone="info" />
      </div>

      <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-slate-300">
        {result.content}
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        <StatusBadge label={`source ${source}`} />
        <StatusBadge label={`type ${contentType}`} />
        {page !== "-" ? <StatusBadge label={`page ${page}`} tone="success" /> : null}
        {paragraph !== "-" ? (
          <StatusBadge label={`paragraph ${paragraph}`} tone="success" />
        ) : null}
      </div>
    </GlassCard>
  );
}
