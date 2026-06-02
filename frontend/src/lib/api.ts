import type {
  ApiRequestOptions,
  ChatRequest,
  ChatResponse,
  HealthResponse,
  ReadyResponse,
  SearchRequest,
  SearchResponse,
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
