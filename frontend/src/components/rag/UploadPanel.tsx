import { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  CheckCircle2,
  Clock3,
  FileUp,
  LoaderCircle,
  UploadCloud,
  XCircle,
} from "lucide-react";

import { getUploadJob, uploadDocument } from "../../lib/api";
import type { ApiRequestOptions, UploadJobResponse, UploadJobStatus } from "../../lib/types";
import { cn } from "../../lib/utils";
import { Button } from "../ui/Button";
import { ErrorState } from "../ui/ErrorState";
import { GlassCard } from "../ui/GlassCard";
import { Input } from "../ui/Input";
import { StatusBadge } from "../ui/StatusBadge";

const supportedTypes = ["TXT", "Markdown", "JSON", "PDF", "DOCX"];

interface UploadPanelProps extends ApiRequestOptions {
  onCompleted: (response: UploadJobResponse) => void;
  onOpenDocuments: () => void;
}

const statusTone: Record<UploadJobStatus, "success" | "warning" | "danger" | "info" | "neutral"> = {
  pending: "warning",
  processing: "info",
  completed: "success",
  failed: "danger",
  canceled: "neutral",
};

const statusIcon: Record<UploadJobStatus, JSX.Element> = {
  pending: <Clock3 className="h-5 w-5" aria-hidden="true" />,
  processing: <LoaderCircle className="h-5 w-5 animate-spin" aria-hidden="true" />,
  completed: <CheckCircle2 className="h-5 w-5" aria-hidden="true" />,
  failed: <XCircle className="h-5 w-5" aria-hidden="true" />,
  canceled: <XCircle className="h-5 w-5" aria-hidden="true" />,
};

const terminalStatuses: UploadJobStatus[] = ["completed", "failed", "canceled"];

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

export function UploadPanel({
  tenantId,
  apiToken,
  onCompleted,
  onOpenDocuments,
}: UploadPanelProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const pollingRunRef = useRef(0);
  const [file, setFile] = useState<File | null>(null);
  const [localTenant, setLocalTenant] = useState(tenantId ?? "");
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadJobResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLocalTenant(tenantId ?? "");
  }, [tenantId]);

  useEffect(() => {
    return () => {
      pollingRunRef.current += 1;
    };
  }, []);

  const handleFile = (nextFile?: File | null) => {
    if (!nextFile) {
      return;
    }
    pollingRunRef.current += 1;
    setFile(nextFile);
    setUploadResult(null);
    setIsPolling(false);
    setError(null);
  };

  const pollUploadStatus = async (
    initialJob: UploadJobResponse,
    options: ApiRequestOptions,
  ) => {
    const runId = pollingRunRef.current + 1;
    pollingRunRef.current = runId;
    setIsPolling(!terminalStatuses.includes(initialJob.status));

    let latestJob = initialJob;
    for (let attempt = 0; attempt < 60; attempt += 1) {
      if (pollingRunRef.current !== runId) {
        return;
      }

      if (latestJob.status === "completed") {
        setIsPolling(false);
        onCompleted(latestJob);
        return;
      }

      if (latestJob.status === "failed") {
        setIsPolling(false);
        setError(latestJob.error_message || "Falha ao processar o documento.");
        return;
      }

      if (latestJob.status === "canceled") {
        setIsPolling(false);
        return;
      }

      await wait(attempt === 0 ? 800 : 1500);

      try {
        latestJob = await getUploadJob(initialJob.job_id, options);
        setUploadResult(latestJob);
      } catch (caught) {
        if (pollingRunRef.current !== runId) {
          return;
        }
        setIsPolling(false);
        setError(caught instanceof Error ? caught.message : "Falha ao consultar status.");
        return;
      }
    }

    if (pollingRunRef.current === runId) {
      setIsPolling(false);
      setError("Tempo limite ao aguardar processamento do upload.");
    }
  };

  const handleSubmit = async () => {
    if (!file) {
      setError("Selecione um arquivo.");
      return;
    }

    setIsUploading(true);
    setUploadResult(null);
    setError(null);
    try {
      const requestOptions = {
        tenantId: localTenant || tenantId,
        apiToken,
      };
      const response = await uploadDocument(file, {
        ...requestOptions,
      });
      setUploadResult(response);
      void pollUploadStatus(response, requestOptions);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Falha ao enviar arquivo.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <GlassCard className="p-5 lg:p-6" elevated>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-black text-white">Upload</h2>
          <p className="mt-1 text-sm text-slate-400">TXT, Markdown, JSON, PDF e DOCX</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {supportedTypes.map((type) => (
            <StatusBadge key={type} label={type} tone="info" />
          ))}
        </div>
      </div>

      <div className="mt-6 grid gap-5 xl:grid-cols-[1.4fr_0.6fr]">
        <div
          onDragOver={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setIsDragging(false);
            handleFile(event.dataTransfer.files.item(0));
          }}
          className={cn(
            "grid min-h-72 place-items-center rounded-lg border border-dashed p-8 text-center transition",
            isDragging
              ? "border-cyan-300/60 bg-cyan-300/10"
              : "border-white/[0.14] bg-white/[0.04] hover:border-cyan-300/35 hover:bg-white/[0.07]",
          )}
        >
          <input
            ref={inputRef}
            type="file"
            className="sr-only"
            accept=".txt,.md,.json,.pdf,.docx,text/plain,text/markdown,application/json,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            onChange={(event) => handleFile(event.target.files?.item(0))}
            aria-label="Selecionar arquivo"
          />
          <div className="grid justify-items-center gap-4">
            <div className="grid h-14 w-14 place-items-center rounded-lg border border-cyan-300/25 bg-cyan-400/10 text-cyan-100">
              <UploadCloud className="h-7 w-7" aria-hidden="true" />
            </div>
            <div>
              <p className="text-base font-black text-white">
                {file ? file.name : "Arraste o documento"}
              </p>
              <p className="mt-1 text-sm text-slate-500">
                {file ? `${Math.ceil(file.size / 1024)} KB` : "Selecione um arquivo local"}
              </p>
            </div>
            <Button
              variant="secondary"
              onClick={() => inputRef.current?.click()}
              icon={<FileUp className="h-4 w-4" aria-hidden="true" />}
            >
              Selecionar arquivo
            </Button>
          </div>
        </div>

        <div className="grid content-start gap-4">
          <label className="field-label">
            Tenant opcional
            <Input
              value={localTenant}
              onChange={(event) => setLocalTenant(event.target.value)}
              placeholder="tenant-demo"
              aria-label="Tenant do upload"
            />
          </label>

          <Button
            onClick={handleSubmit}
            disabled={isUploading || isPolling}
            icon={
              isUploading ? (
                <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <FileUp className="h-4 w-4" aria-hidden="true" />
              )
            }
          >
            {isUploading ? "Enviando" : "Indexar documento"}
          </Button>

          {error ? <ErrorState message={error} /> : null}

          {uploadResult ? (
            <div className="rounded-lg border border-white/10 bg-white/[0.05] p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-slate-100">
                  <span className={cn(
                    "grid h-8 w-8 place-items-center rounded-lg border",
                    uploadResult.status === "completed"
                      ? "border-emerald-300/25 bg-emerald-400/10 text-emerald-100"
                      : uploadResult.status === "failed"
                        ? "border-rose-300/25 bg-rose-400/10 text-rose-100"
                        : "border-cyan-300/25 bg-cyan-400/10 text-cyan-100",
                  )}>
                    {statusIcon[uploadResult.status]}
                  </span>
                  <div>
                    <p className="text-sm font-black">
                      {uploadResult.status === "completed"
                        ? "Upload completed"
                        : uploadResult.status === "failed"
                          ? "Upload failed"
                          : uploadResult.status === "canceled"
                            ? "Upload canceled"
                            : "Upload em processamento"}
                    </p>
                    <p className="text-xs text-slate-500">{uploadResult.message}</p>
                  </div>
                </div>
                <StatusBadge
                  label={uploadResult.status}
                  tone={statusTone[uploadResult.status]}
                />
              </div>
              <dl className="mt-4 grid gap-2 text-sm">
                <div className="flex justify-between gap-3">
                  <dt className="text-slate-500">Arquivo</dt>
                  <dd className="truncate text-slate-200">{uploadResult.filename}</dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt className="text-slate-500">Tamanho</dt>
                  <dd className="font-bold text-slate-100">
                    {Math.ceil(uploadResult.file_size / 1024)} KB
                  </dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt className="text-slate-500">Job</dt>
                  <dd className="max-w-40 truncate font-mono text-xs text-slate-300">
                    {uploadResult.job_id}
                  </dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt className="text-slate-500">Tentativas</dt>
                  <dd className="font-bold text-slate-100">
                    {uploadResult.attempts}/{uploadResult.max_attempts}
                  </dd>
                </div>
                {uploadResult.document_id ? (
                  <div className="flex justify-between gap-3">
                    <dt className="text-slate-500">Documento</dt>
                    <dd className="max-w-40 truncate font-mono text-xs text-emerald-100">
                      {uploadResult.document_id}
                    </dd>
                  </div>
                ) : null}
              </dl>
              {uploadResult.status === "failed" && uploadResult.last_error ? (
                <p className="mt-4 rounded-lg border border-rose-300/20 bg-rose-400/10 p-3 text-xs font-semibold text-rose-100">
                  {uploadResult.last_error}
                </p>
              ) : null}
              {uploadResult.status === "completed" ? (
                <Button
                  className="mt-4 w-full"
                  variant="secondary"
                  onClick={onOpenDocuments}
                  icon={<ArrowRight className="h-4 w-4" aria-hidden="true" />}
                >
                  Abrir Documents
                </Button>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </GlassCard>
  );
}
