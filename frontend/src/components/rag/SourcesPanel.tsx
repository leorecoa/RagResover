import { Library } from "lucide-react";

import type { Source } from "../../lib/types";
import { EmptyState } from "../ui/EmptyState";
import { SourceCard } from "./SourceCard";

interface SourcesPanelProps {
  sources: Source[];
}

export function SourcesPanel({ sources }: SourcesPanelProps) {
  return (
    <aside className="grid min-h-0 gap-4">
      <div>
        <h2 className="text-base font-black text-white">Fontes</h2>
        <p className="mt-1 text-sm text-slate-500">{sources.length} referencias</p>
      </div>

      <div className="grid min-h-0 gap-3 overflow-auto pr-1">
        {sources.length ? (
          sources.map((source) => <SourceCard key={source.chunk_id} source={source} />)
        ) : (
          <EmptyState
            title="Sem fontes"
            description="Aguardando citacoes recuperadas."
            icon={<Library className="h-5 w-5" aria-hidden="true" />}
            className="min-h-64"
          />
        )}
      </div>
    </aside>
  );
}
