import type {
  ApiRequestOptions,
  ChatRequest,
  ChatResponse,
  DeleteDocumentResponse,
  DocumentChunksResponse,
  DocumentDetailResponse,
  DocumentListResponse,
  HealthResponse,
  AuthTokenResponse,
  AuthUser,
  LoginRequest,
  Organization,
  OrganizationApiKeyCreated,
  OrganizationApiKeysResponse,
  OrganizationInvitation,
  OrganizationInvitationsResponse,
  OrganizationMembersResponse,
  ReadyResponse,
  RegisterRequest,
  SearchRequest,
  SearchResponse,
  UploadJobFilters,
  UploadJobListResponse,
  UploadJobResponse,
  UploadResponse,
} from "./types";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

function getErrorMessage(payload: unknown): string {
  if (typeof payload === "string") {
    return payload;
  }

  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail?: unknown }).detail;
    if (typeof detail === "string") {
      return detail;
    }
    return JSON.stringify(detail ?? payload);
  }

  return JSON.stringify(payload);
}

function buildHeaders(
  options?: ApiRequestOptions,
  extraHeaders?: HeadersInit,
): Headers {
  const headers = new Headers(extraHeaders);

  const tenantId = options?.tenantId?.trim();
  if (tenantId) {
    headers.set("X-Tenant-ID", tenantId);
  }

  const apiToken = options?.apiToken?.trim();
  if (apiToken) {
    headers.set("Authorization", `Bearer ${apiToken}`);
  }

  return headers;
}

async function requestJson<T>(
  path: string,
  init: RequestInit = {},
  options?: ApiRequestOptions,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: buildHeaders(options, init.headers),
  });
  const text = await response.text();
  const payload = text ? JSON.parse(text) : {};

  if (!response.ok) {
    throw new ApiError(getErrorMessage(payload), response.status, payload);
  }

  return payload as T;
}

export function getHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/health");
}

export function getReady(): Promise<ReadyResponse> {
  return requestJson<ReadyResponse>("/ready");
}

export function login(payload: LoginRequest): Promise<AuthTokenResponse> {
  return requestJson<AuthTokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json",
    },
  });
}

export function register(payload: RegisterRequest): Promise<AuthTokenResponse> {
  return requestJson<AuthTokenResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json",
    },
  });
}

export function getMe(options?: ApiRequestOptions): Promise<AuthUser> {
  return requestJson<AuthUser>("/auth/me", undefined, options);
}

export function getCurrentOrganization(options?: ApiRequestOptions): Promise<Organization> {
  return requestJson<Organization>("/organizations/current", undefined, options);
}

export function updateCurrentOrganization(
  payload: { name: string },
  options?: ApiRequestOptions,
): Promise<Organization> {
  return requestJson<Organization>(
    "/organizations/current",
    {
      method: "PATCH",
      body: JSON.stringify(payload),
      headers: {
        "Content-Type": "application/json",
      },
    },
    options,
  );
}

export function listOrganizationMembers(
  options?: ApiRequestOptions,
): Promise<OrganizationMembersResponse> {
  return requestJson<OrganizationMembersResponse>(
    "/organizations/current/members",
    undefined,
    options,
  );
}

export function updateOrganizationMemberRole(
  userId: string,
  payload: { role: string },
  options?: ApiRequestOptions,
): Promise<OrganizationMembersResponse> {
  return requestJson<OrganizationMembersResponse>(
    `/organizations/current/members/${userId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
      headers: {
        "Content-Type": "application/json",
      },
    },
    options,
  );
}

export function inviteOrganizationMember(
  payload: { email: string; role: string },
  options?: ApiRequestOptions,
): Promise<OrganizationInvitation> {
  return requestJson<OrganizationInvitation>(
    "/organizations/current/invitations",
    {
      method: "POST",
      body: JSON.stringify(payload),
      headers: {
        "Content-Type": "application/json",
      },
    },
    options,
  );
}

export function listOrganizationInvitations(
  options?: ApiRequestOptions,
): Promise<OrganizationInvitationsResponse> {
  return requestJson<OrganizationInvitationsResponse>(
    "/organizations/current/invitations",
    undefined,
    options,
  );
}

export function listOrganizationApiKeys(
  options?: ApiRequestOptions,
): Promise<OrganizationApiKeysResponse> {
  return requestJson<OrganizationApiKeysResponse>(
    "/organizations/current/api-keys",
    undefined,
    options,
  );
}

export function createOrganizationApiKey(
  payload: { name: string; role: string },
  options?: ApiRequestOptions,
): Promise<OrganizationApiKeyCreated> {
  return requestJson<OrganizationApiKeyCreated>(
    "/organizations/current/api-keys",
    {
      method: "POST",
      body: JSON.stringify(payload),
      headers: {
        "Content-Type": "application/json",
      },
    },
    options,
  );
}

export function revokeOrganizationApiKey(
  apiKeyId: string,
  options?: ApiRequestOptions,
): Promise<OrganizationApiKeysResponse> {
  return requestJson<OrganizationApiKeysResponse>(
    `/organizations/current/api-keys/${apiKeyId}`,
    { method: "DELETE" },
    options,
  );
}

export function uploadDocument(
  file: File,
  options?: ApiRequestOptions,
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return requestJson<UploadResponse>(
    "/upload",
    {
      method: "POST",
      body: formData,
    },
    options,
  );
}

export function getUploadJob(
  jobId: string,
  options?: ApiRequestOptions,
): Promise<UploadJobResponse> {
  return requestJson<UploadJobResponse>(`/uploads/${jobId}`, undefined, options);
}

export function listUploadJobs(
  filters: UploadJobFilters = {},
  options?: ApiRequestOptions,
): Promise<UploadJobListResponse> {
  const params = new URLSearchParams({
    limit: String(filters.limit ?? 10),
    offset: String(filters.offset ?? 0),
  });
  if (filters.status) {
    params.set("status", filters.status);
  }
  if (filters.filename?.trim()) {
    params.set("filename", filters.filename.trim());
  }
  if (filters.contentType?.trim()) {
    params.set("content_type", filters.contentType.trim());
  }
  if (filters.createdFrom?.trim()) {
    params.set("created_from", filters.createdFrom.trim());
  }
  if (filters.createdTo?.trim()) {
    params.set("created_to", filters.createdTo.trim());
  }
  if (filters.documentId?.trim()) {
    params.set("document_id", filters.documentId.trim());
  }

  return requestJson<UploadJobListResponse>(
    `/uploads?${params.toString()}`,
    undefined,
    options,
  );
}

export function retryUploadJob(
  jobId: string,
  options?: ApiRequestOptions,
): Promise<UploadJobResponse> {
  return requestJson<UploadJobResponse>(
    `/uploads/${jobId}/retry`,
    { method: "POST" },
    options,
  );
}

export function cancelUploadJob(
  jobId: string,
  options?: ApiRequestOptions,
): Promise<UploadJobResponse> {
  return requestJson<UploadJobResponse>(
    `/uploads/${jobId}/cancel`,
    { method: "POST" },
    options,
  );
}

export function listDocuments(
  filters: { source?: string; contentType?: string } = {},
  options?: ApiRequestOptions,
): Promise<DocumentListResponse> {
  const params = new URLSearchParams();
  if (filters.source?.trim()) {
    params.set("source", filters.source.trim());
  }
  if (filters.contentType?.trim()) {
    params.set("content_type", filters.contentType.trim());
  }
  const query = params.toString();
  return requestJson<DocumentListResponse>(
    `/documents${query ? `?${query}` : ""}`,
    undefined,
    options,
  );
}

export function getDocument(
  documentId: string,
  options?: ApiRequestOptions,
): Promise<DocumentDetailResponse> {
  return requestJson<DocumentDetailResponse>(`/documents/${documentId}`, undefined, options);
}

export function getDocumentChunks(
  documentId: string,
  params: { page?: number; pageSize?: number } = {},
  options?: ApiRequestOptions,
): Promise<DocumentChunksResponse> {
  const query = new URLSearchParams({
    page: String(params.page ?? 1),
    page_size: String(params.pageSize ?? 20),
  });
  return requestJson<DocumentChunksResponse>(
    `/documents/${documentId}/chunks?${query.toString()}`,
    undefined,
    options,
  );
}

export function deleteDocument(
  documentId: string,
  options?: ApiRequestOptions,
): Promise<DeleteDocumentResponse> {
  return requestJson<DeleteDocumentResponse>(
    `/documents/${documentId}`,
    { method: "DELETE" },
    options,
  );
}

export function searchDocuments(
  payload: SearchRequest,
  options?: ApiRequestOptions,
): Promise<SearchResponse> {
  return requestJson<SearchResponse>(
    "/search",
    {
      method: "POST",
      body: JSON.stringify(payload),
      headers: {
        "Content-Type": "application/json",
      },
    },
    options,
  );
}

export function chatWithDocuments(
  payload: ChatRequest,
  options?: ApiRequestOptions,
): Promise<ChatResponse> {
  return requestJson<ChatResponse>(
    "/chat",
    {
      method: "POST",
      body: JSON.stringify(payload),
      headers: {
        "Content-Type": "application/json",
      },
    },
    options,
  );
}
