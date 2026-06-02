import type {
  ApiRequestOptions,
  RetrievalDiagnostics,
  SearchResponse,
} from "../lib/types";
import { SearchPanel } from "../components/rag/SearchPanel";

interface SearchProps extends ApiRequestOptions {
  onSearched: (response: SearchResponse) => void;
  onDiagnostics: (diagnostics?: RetrievalDiagnostics | null) => void;
}

export function SearchPage({
  tenantId,
  apiToken,
  onSearched,
  onDiagnostics,
}: SearchProps) {
  return (
    <SearchPanel
      tenantId={tenantId}
      apiToken={apiToken}
      onSearched={onSearched}
      onDiagnostics={onDiagnostics}
    />
  );
}
