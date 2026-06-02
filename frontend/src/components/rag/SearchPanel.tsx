import { useState } from "react";
import { Search, SlidersHorizontal } from "lucide-react";

import { searchDocuments } from "../../lib/api";
import type {
  ApiRequestOptions,
  RetrievalDiagnostics,
  SearchResponse,
} from "../../lib/types";
import {
  buildSourceFilter,
  clampTopK,
  getProviderLabel,
  parseOptionalThreshold,
} from "../../lib/utils";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { GlassCard } from "../ui/GlassCard";
import { Input } from "../ui/Input";
import { LoadingState } from "../ui/LoadingState";
import { StatusBadge } from "../ui/StatusBadge";
import { SearchResultCard } from "./SearchResultCard";

interface SearchPanelProps extends ApiRequestOptions {
  onSearched: (response: SearchResponse) => void;
  onDiagnostics: (diagnostics?: RetrievalDiagnostics | null) => void;
}

export function SearchPanel({
  tenantId,
  apiToken,
  onSearched,
  onDiagnostics,
}: SearchPanelProps) {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [threshold, setThreshold] = useState("");
  const [source, setSource] = useState("");
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      setError("Digite uma busca.");
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const nextResponse = await searchDocuments(
        {
          query: trimmedQuery,
          top_k: clampTopK(topK),
          score_threshold: parseOptionalThreshold(threshold),
          metadata_filters: buildSourceFilter(source),
        },
        { tenantId, apiToken },
      );
      setResponse(nextResponse);
      onSearched(nextResponse);
      onDiagnostics(nextResponse.diagnostics);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Falha ao buscar documentos.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="grid gap-5">
      <GlassCard className="p-5 lg:p-6" elevated>
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end">
          <label className="field-label xl:flex-1">
            Busca semantica
            <Input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Ex.: politicas de retencao"
              aria-label="Consulta de busca semantica"
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  void handleSearch();
                }
              }}
            />
          </label>
          <label className="field-label xl:w-28">
            Top K
            <Input
              type="number"
              min={1}
              max={20}
              value={topK}
              onChange={(event) => setTopK(Number(event.target.value))}
              aria-label="Quantidade de resultados"
            />
          </label>
          <label className="field-label xl:w-40">
            Threshold
            <Input
              value={threshold}
              onChange={(event) => setThreshold(event.target.value)}
              placeholder="-1 a 1"
              aria-label="Score threshold"
            />
          </label>
          <label className="field-label xl:w-56">
            Source
            <Input
              value={source}
              onChange={(event) => setSource(event.target.value)}
              placeholder="manual.pdf"
              aria-label="Filtro por source"
            />
          </label>
          <Button
            onClick={handleSearch}
            disabled={isLoading}
            icon={<Search className="h-4 w-4" aria-hidden="true" />}
          >
            Buscar
          </Button>
        </div>
      </GlassCard>

      {response?.diagnostics ? (
        <GlassCard className="flex flex-wrap items-center gap-2 p-4">
          <SlidersHorizontal className="h-4 w-4 text-cyan-200" aria-hidden="true" />
          <StatusBadge label={`provider ${getProviderLabel(response.diagnostics)}`} tone="info" />
          <StatusBadge label={`returned ${response.diagnostics.returned_count ?? 0}`} />
          <StatusBadge label={`fetch ${response.diagnostics.fetch_limit ?? "-"}`} />
          <StatusBadge label={`tenant ${response.diagnostics.tenant_id ?? tenantId ?? "-"}`} />
        </GlassCard>
      ) : null}

      {error ? <ErrorState message={error} /> : null}
      {isLoading ? <LoadingState label="Buscando contexto" /> : null}

      {!isLoading && !error && !response ? (
        <EmptyState
          title="Nenhuma busca executada"
          description="Aguardando consulta."
          icon={<Search className="h-5 w-5" aria-hidden="true" />}
        />
      ) : null}

      {!isLoading && response ? (
        response.results.length ? (
          <div className="grid gap-4">
            {response.results.map((result) => (
              <SearchResultCard key={result.chunk_id} result={result} />
            ))}
          </div>
        ) : (
          <EmptyState title="Nenhum trecho encontrado" />
        )
      ) : null}
    </div>
  );
}
