import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

import type { Metadata, MetadataValue, RetrievalDiagnostics } from "./types";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatScore(score: number): string {
  return Number.isFinite(score) ? score.toFixed(3) : "0.000";
}

export function formatMetadataValue(value: MetadataValue | undefined): string {
  if (value === undefined || value === null) {
    return "-";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

export function getMetadataLabel(metadata: Metadata, key: string): string {
  return formatMetadataValue(metadata[key]);
}

export function getProviderLabel(
  diagnostics?: RetrievalDiagnostics | null,
  fallback = "Configured by API",
): string {
  if (diagnostics?.embedding_provider) {
    const reranker =
      diagnostics.reranker_provider && diagnostics.reranker_provider !== "none"
        ? ` + ${diagnostics.reranker_provider}`
        : "";
    return `${diagnostics.embedding_provider}${reranker}`;
  }
  return fallback;
}

export function compactId(value: string): string {
  if (value.length <= 12) {
    return value;
  }
  return `${value.slice(0, 6)}...${value.slice(-6)}`;
}

export function createActivityId(): string {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function clampTopK(value: number): number {
  if (!Number.isFinite(value)) {
    return 5;
  }
  return Math.min(20, Math.max(1, Math.round(value)));
}

export function parseOptionalThreshold(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  const parsed = Number(trimmed);
  if (!Number.isFinite(parsed)) {
    return null;
  }
  return Math.min(1, Math.max(-1, parsed));
}

export function buildSourceFilter(value: string): Record<string, string> {
  const source = value.trim();
  return source ? { source } : {};
}
