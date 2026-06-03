import { useCallback, useEffect, useState } from "react";
import { FileStack, RefreshCw, Search, Trash2 } from "lucide-react";

import {
  deleteDocument,
  getDocument,
  getDocumentChunks,
  listDocuments,
} from "../lib/api";
import type {
  ApiRequestOptions,
  DocumentChunk,
  DocumentDetailResponse,
  DocumentItem,
} from "../lib/types";
import {
  compactId,
  formatBytes,
  formatDate,
  formatMetadataValue,
  getMetadataLabel,
} from "../lib/utils";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { GlassCard } from "../components/ui/GlassCard";
import { Input } from "../components/ui/Input";
import { LoadingState } from "../components/ui/LoadingState";
import { StatusBadge } from "../components/ui/StatusBadge";

interface DocumentsProps extends ApiRequestOptions {
  onDeleted: (document: DocumentItem) => void;
}

function MetadataList({ metadata }: { metadata: DocumentItem["metadata"] }) {
  const entries = Object.entries(metadata);
  if (!entries.length) {
    return <p className="text-sm text-slate-500">Sem metadados.</p>;
  }

  return (
    <dl className="grid gap-2">
      {entries.map(([key, value]) => (
        <div
          key={key}
          className="grid gap-1 rounded-md border border-white/10 bg-white/[0.04] px-3 py-2"
        >
          <dt className="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">
            {key}
          </dt>
          <dd className="break-words text-sm text-slate-200">
            {formatMetadataValue(value)}
          </dd>
        </div>
      ))}
    </dl>
  );
}

function DocumentRow({
  document,
  selected,
  onSelect,
}: {
  document: DocumentItem;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`grid gap-3 rounded-lg border p-4 text-left transition ${
        selected
          ? "border-cyan-300/35 bg-cyan-300/10"
          : "border-white/10 bg-white/[0.04] hover:border-cyan-300/20 hover:bg-white/[0.07]"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate text-sm font-black text-white">{document.file_name}</h3>
          <p className="mt-1 text-xs text-slate-500">{compactId(document.id)}</p>
        </div>
        <StatusBadge label={`${document.chunks_count} chunks`} tone="info" />
      </div>
      <div className="flex flex-wrap gap-2">
        <StatusBadge label={document.content_type} />
        <StatusBadge label={formatBytes(document.file_size)} />
      </div>
    </button>
  );
}

function ChunkCard({ chunk }: { chunk: DocumentChunk }) {
  return (
    <GlassCard className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h4 className="text-sm font-black text-white">Chunk #{chunk.chunk_index}</h4>
          <p className="mt-1 text-xs text-slate-500">{compactId(chunk.id)}</p>
        </div>
        <StatusBadge label={getMetadataLabel(chunk.metadata, "source")} />
      </div>
      <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-300">
        {chunk.content}
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        {Object.entries(chunk.metadata).map(([key, value]) => (
          <StatusBadge key={key} label={`${key}: ${formatMetadataValue(value)}`} />
        ))}
      </div>
    </GlassCard>
  );
}

export function Documents({ tenantId, apiToken, onDeleted }: DocumentsProps) {
  const [sourceFilter, setSourceFilter] = useState("");
  const [contentTypeFilter, setContentTypeFilter] = useState("");
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<DocumentDetailResponse | null>(null);
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const requestOptions = { tenantId, apiToken };

  const loadDocuments = useCallback(async () => {
    setIsLoadingList(true);
    setError(null);
    try {
      const response = await listDocuments(
        {
          source: sourceFilter,
          contentType: contentTypeFilter,
        },
        requestOptions,
      );
      setDocuments(response.documents);
      setSelectedId((current) => {
        if (current && response.documents.some((document) => document.id === current)) {
          return current;
        }
        return response.documents[0]?.id ?? null;
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Falha ao listar documentos.");
    } finally {
      setIsLoadingList(false);
    }
  }, [apiToken, contentTypeFilter, sourceFilter, tenantId]);

  const loadDetail = useCallback(
    async (documentId: string) => {
      setIsLoadingDetail(true);
      setError(null);
      try {
        const [nextDetail, chunkPage] = await Promise.all([
          getDocument(documentId, requestOptions),
          getDocumentChunks(documentId, { page: 1, pageSize: 20 }, requestOptions),
        ]);
        setDetail(nextDetail);
        setChunks(chunkPage.chunks);
        setTotalChunks(chunkPage.total);
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Falha ao abrir documento.");
        setDetail(null);
        setChunks([]);
        setTotalChunks(0);
      } finally {
        setIsLoadingDetail(false);
      }
    },
    [apiToken, tenantId],
  );

  useEffect(() => {
    void loadDocuments();
  }, [loadDocuments]);

  useEffect(() => {
    if (selectedId) {
      void loadDetail(selectedId);
    } else {
      setDetail(null);
      setChunks([]);
      setTotalChunks(0);
    }
  }, [loadDetail, selectedId]);

  const handleDelete = async () => {
    if (!detail || isDeleting) {
      return;
    }

    const confirmed = window.confirm(`Remover ${detail.file_name}?`);
    if (!confirmed) {
      return;
    }

    setIsDeleting(true);
    setError(null);
    setSuccess(null);
    try {
      await deleteDocument(detail.id, requestOptions);
      setSuccess(`${detail.file_name} removido.`);
      onDeleted(detail);
      setDocuments((current) => current.filter((document) => document.id !== detail.id));
      setSelectedId(null);
      setDetail(null);
      setChunks([]);
      setTotalChunks(0);
      await loadDocuments();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Falha ao deletar documento.");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="grid gap-5 xl:grid-cols-[420px_minmax(0,1fr)]">
      <GlassCard className="grid content-start gap-4 p-5 lg:p-6" elevated>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-black text-white">Documents</h2>
            <p className="mt-1 text-sm text-slate-500">{documents.length} documentos</p>
          </div>
          <Button
            variant="secondary"
            size="icon"
            onClick={loadDocuments}
            disabled={isLoadingList}
            aria-label="Atualizar documentos"
            icon={<RefreshCw className={isLoadingList ? "h-4 w-4 animate-spin" : "h-4 w-4"} />}
          />
        </div>

        <div className="grid gap-3">
          <label className="field-label">
            Source
            <Input
              value={sourceFilter}
              onChange={(event) => setSourceFilter(event.target.value)}
              placeholder="manual.pdf"
              aria-label="Filtrar por source"
            />
          </label>
          <label className="field-label">
            Content type
            <Input
              value={contentTypeFilter}
              onChange={(event) => setContentTypeFilter(event.target.value)}
              placeholder="application/pdf"
              aria-label="Filtrar por content type"
            />
          </label>
          <Button
            onClick={loadDocuments}
            icon={<Search className="h-4 w-4" aria-hidden="true" />}
          >
            Filtrar documentos
          </Button>
        </div>

        {error ? <ErrorState message={error} /> : null}
        {success ? (
          <div className="rounded-lg border border-emerald-300/20 bg-emerald-400/10 p-4 text-sm font-bold text-emerald-100">
            {success}
          </div>
        ) : null}

        {isLoadingList ? <LoadingState label="Carregando documentos" /> : null}

        {!isLoadingList && !documents.length ? (
          <EmptyState
            title="Sem documentos"
            description="Aguardando upload no tenant atual."
            icon={<FileStack className="h-5 w-5" aria-hidden="true" />}
          />
        ) : null}

        <div className="grid gap-3">
          {documents.map((document) => (
            <DocumentRow
              key={document.id}
              document={document}
              selected={document.id === selectedId}
              onSelect={() => setSelectedId(document.id)}
            />
          ))}
        </div>
      </GlassCard>

      <div className="grid gap-5">
        <GlassCard className="p-5 lg:p-6" elevated>
          {!detail && !isLoadingDetail ? (
            <EmptyState
              title="Selecione um documento"
              description="Detalhes e chunks aparecem aqui."
              icon={<FileStack className="h-5 w-5" aria-hidden="true" />}
              className="min-h-96"
            />
          ) : null}

          {isLoadingDetail ? <LoadingState label="Abrindo documento" /> : null}

          {detail && !isLoadingDetail ? (
            <div className="grid gap-5">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0">
                  <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">
                    Documento
                  </p>
                  <h2 className="mt-2 truncate text-2xl font-black text-white">
                    {detail.file_name}
                  </h2>
                  <p className="mt-1 text-sm text-slate-500">{compactId(detail.id)}</p>
                </div>
                <Button
                  variant="danger"
                  onClick={handleDelete}
                  disabled={isDeleting}
                  icon={<Trash2 className="h-4 w-4" aria-hidden="true" />}
                >
                  {isDeleting ? "Removendo" : "Delete"}
                </Button>
              </div>

              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <StatusBadge label={detail.content_type} tone="info" />
                <StatusBadge label={formatBytes(detail.file_size)} />
                <StatusBadge label={`${detail.chunks_count} chunks`} tone="success" />
                <StatusBadge label={`tenant ${detail.tenant_id}`} />
              </div>

              <div className="grid gap-4 lg:grid-cols-[1fr_1fr]">
                <div>
                  <h3 className="mb-3 text-sm font-black text-white">Metadados</h3>
                  <MetadataList metadata={detail.metadata} />
                </div>
                <div className="rounded-lg border border-white/10 bg-white/[0.04] p-4">
                  <h3 className="text-sm font-black text-white">Resumo</h3>
                  <dl className="mt-4 grid gap-3 text-sm">
                    <div className="flex justify-between gap-3">
                      <dt className="text-slate-500">Criado em</dt>
                      <dd className="text-right text-slate-200">{formatDate(detail.created_at)}</dd>
                    </div>
                    <div className="flex justify-between gap-3">
                      <dt className="text-slate-500">Source</dt>
                      <dd className="truncate text-right text-slate-200">
                        {getMetadataLabel(detail.metadata, "source")}
                      </dd>
                    </div>
                    <div className="flex justify-between gap-3">
                      <dt className="text-slate-500">Chunks carregados</dt>
                      <dd className="text-right text-slate-200">
                        {chunks.length} / {totalChunks}
                      </dd>
                    </div>
                  </dl>
                </div>
              </div>
            </div>
          ) : null}
        </GlassCard>

        {detail ? (
          <div className="grid gap-3">
            <div className="flex items-center justify-between gap-4">
              <h3 className="text-base font-black text-white">Chunks</h3>
              <StatusBadge label={`${totalChunks} total`} tone="info" />
            </div>
            {chunks.map((chunk) => (
              <ChunkCard key={chunk.id} chunk={chunk} />
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
