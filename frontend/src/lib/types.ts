export type MetadataFilterValue = string | number | boolean;
export type MetadataValue = string | number | boolean | null | MetadataValue[] | {
  [key: string]: MetadataValue;
};

export type Metadata = Record<string, MetadataValue>;

export interface HealthResponse {
  status: string;
  env: string;
  version: string;
}

export interface ReadyResponse {
  status: string;
  database: string;
  storage: string;
  env: string;
  version: string;
}

export interface UploadResponse {
  document_id: string;
  filename: string;
  status: string;
  chunks_count: number;
  message: string;
}

export interface SearchRequest {
  query: string;
  top_k?: number;
  score_threshold?: number | null;
  metadata_filters?: Record<string, MetadataFilterValue>;
}

export interface RetrievalDiagnostics {
  requested_top_k?: number;
  fetch_limit?: number;
  returned_count?: number;
  tenant_id?: string;
  score_threshold?: number | null;
  metadata_filters?: Record<string, MetadataFilterValue>;
  embedding_provider?: string;
  reranker_provider?: string;
  reranker_applied?: boolean;
  [key: string]: MetadataValue | undefined;
}

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  file_name: string;
  content: string;
  score: number;
  metadata: Metadata;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  diagnostics?: RetrievalDiagnostics | null;
}

export interface ChatRequest {
  question: string;
  top_k?: number;
  score_threshold?: number | null;
  metadata_filters?: Record<string, MetadataFilterValue>;
}

export interface Source {
  index: number;
  chunk_id: string;
  document_id: string;
  file_name: string;
  score: number;
  excerpt: string;
  metadata: Metadata;
}

export interface ChatResponse {
  question: string;
  answer: string;
  sources: Source[];
  diagnostics?: RetrievalDiagnostics | null;
}

export interface ApiRequestOptions {
  tenantId?: string;
  apiToken?: string;
}

export interface ChatMessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

export interface ActivityItem {
  id: string;
  label: string;
  detail: string;
  tone: "cyan" | "emerald" | "violet";
}
