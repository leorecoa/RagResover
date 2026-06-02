import { useEffect, useRef, useState } from "react";
import { CheckCircle2, FileUp, LoaderCircle, UploadCloud } from "lucide-react";

import { uploadDocument } from "../../lib/api";
import type { ApiRequestOptions, UploadResponse } from "../../lib/types";
import { cn } from "../../lib/utils";
import { Button } from "../ui/Button";
import { ErrorState } from "../ui/ErrorState";
import { GlassCard } from "../ui/GlassCard";
import { Input } from "../ui/Input";
import { StatusBadge } from "../ui/StatusBadge";

const supportedTypes = ["TXT", "Markdown", "JSON", "PDF", "DOCX"];

interface UploadPanelProps extends ApiRequestOptions {
  onUploaded: (response: UploadResponse) => void;
}

export function UploadPanel({
  tenantId,
  apiToken,
  onUploaded,
}: UploadPanelProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [localTenant, setLocalTenant] = useState(tenantId ?? "");
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLocalTenant(tenantId ?? "");
  }, [tenantId]);

  const handleFile = (nextFile?: File | null) => {
    if (!nextFile) {
      return;
    }
    setFile(nextFile);
    setUploadResult(null);
    setError(null);
  };

  const handleSubmit = async () => {
    if (!file) {
      setError("Selecione um arquivo.");
      return;
    }

    setIsUploading(true);
    setError(null);
    try {
      const response = await uploadDocument(file, {
        tenantId: localTenant || tenantId,
        apiToken,
      });
      setUploadResult(response);
      onUploaded(response);
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
            disabled={isUploading}
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
            <div className="rounded-lg border border-emerald-300/20 bg-emerald-400/10 p-4">
              <div className="flex items-center gap-2 text-emerald-100">
                <CheckCircle2 className="h-5 w-5" aria-hidden="true" />
                <p className="text-sm font-black">Documento indexado</p>
              </div>
              <dl className="mt-4 grid gap-2 text-sm">
                <div className="flex justify-between gap-3">
                  <dt className="text-slate-500">Arquivo</dt>
                  <dd className="truncate text-slate-200">{uploadResult.filename}</dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt className="text-slate-500">Chunks</dt>
                  <dd className="font-bold text-slate-100">{uploadResult.chunks_count}</dd>
                </div>
              </dl>
            </div>
          ) : null}
        </div>
      </div>
    </GlassCard>
  );
}
