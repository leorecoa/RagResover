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

export type UploadJobStatus = "pending" | "processing" | "completed" | "failed" | "canceled";

export interface UploadJobResponse {
  job_id: string;
  filename: string;
  content_type: string;
  file_size: number;
  status: UploadJobStatus;
  tenant_id: string;
  error_message?: string | null;
  attempts: number;
  max_attempts: number;
  last_error?: string | null;
  document_id?: string | null;
  created_at: string;
  updated_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  message: string;
}

export type UploadResponse = UploadJobResponse;

export interface UploadJobListResponse {
  uploads: UploadJobResponse[];
  limit: number;
  offset: number;
  count: number;
}

export interface UploadJobFilters {
  status?: UploadJobStatus | "";
  filename?: string;
  contentType?: string;
  createdFrom?: string;
  createdTo?: string;
  documentId?: string;
  limit?: number;
  offset?: number;
}

export interface DocumentItem {
  id: string;
  file_name: string;
  content_type: string;
  file_size: number;
  chunks_count: number;
  tenant_id: string;
  created_at: string;
  metadata: Metadata;
}

export interface DocumentListResponse {
  documents: DocumentItem[];
}

export type DocumentDetailResponse = DocumentItem;

export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  metadata: Metadata;
  created_at: string;
}

export interface DocumentChunksResponse {
  document_id: string;
  page: number;
  page_size: number;
  total: number;
  chunks: DocumentChunk[];
}

export interface DeleteDocumentResponse {
  document_id: string;
  status: string;
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

export interface OrganizationMembership {
  organization_id: string;
  role: string;
}

export interface AuthUser {
  user_id: string;
  email: string;
  full_name?: string | null;
  organizations: OrganizationMembership[];
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: AuthUser;
}

export interface LoginRequest {
  email: string;
  password: string;
  organization_id?: string | null;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string | null;
  organization_name: string;
}

export interface Organization {
  id: string;
  name: string;
  current_user_role: string;
}

export interface OrganizationMember {
  user_id: string;
  email: string;
  full_name?: string | null;
  role: string;
  created_at: string;
}

export interface OrganizationMembersResponse {
  members: OrganizationMember[];
}

export interface OrganizationInvitation {
  id: string;
  organization_id: string;
  email: string;
  role: string;
  invited_by_user_id: string;
  status: string;
  created_at: string;
}

export interface OrganizationInvitationsResponse {
  invitations: OrganizationInvitation[];
}

export interface OrganizationApiKey {
  id: string;
  name: string;
  key_prefix: string;
  role: string;
  created_by_user_id: string;
  created_at: string;
  revoked_at?: string | null;
}

export interface OrganizationApiKeyCreated extends OrganizationApiKey {
  api_key: string;
}

export interface OrganizationApiKeysResponse {
  api_keys: OrganizationApiKey[];
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
