import { useEffect, useState } from "react";
import {
  Ban,
  Filter,
  LoaderCircle,
  RefreshCw,
  RotateCcw,
} from "lucide-react";

import { cancelUploadJob, listUploadJobs, retryUploadJob } from "../../lib/api";
import type {
  ApiRequestOptions,
  UploadJobFilters,
  UploadJobResponse,
  UploadJobStatus,
} from "../../lib/types";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { GlassCard } from "../ui/GlassCard";
import { Input } from "../ui/Input";
import { LoadingState } from "../ui/LoadingState";
import { StatusBadge } from "../ui/StatusBadge";

interface UploadHistoryPanelProps extends ApiRequestOptions {
  refreshKey?: number;
}

const statusTone: Record<
  UploadJobStatus,
  "success" | "warning" | "danger" | "info" | "neutral"
> = {
  pending: "warning",
  processing: "info",
  completed: "success",
  failed: "danger",
  canceled: "neutral",
};

function formatDate(value?: string | null): string {
  if (!value) {
    return "n/a";
  }
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

function jobError(job: UploadJobResponse): string | null {
  return job.error_message || job.last_error || null;
}

export function UploadHistoryPanel({
  tenantId,
  apiToken,
  refreshKey = 0,
}: UploadHistoryPanelProps) {
  const [jobs, setJobs] = useState<UploadJobResponse[]>([]);
  const [statusFilter, setStatusFilter] = useState<UploadJobStatus | "">("");
  const [filenameFilter, setFilenameFilter] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [actionJobId, setActionJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const requestOptions = {
    tenantId,
    apiToken,
  };

  const loadJobs = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const filters: UploadJobFilters = {
        limit: 10,
        offset: 0,
        status: statusFilter,
        filename: filenameFilter,
      };
      const response = await listUploadJobs(filters, requestOptions);
      setJobs(response.uploads);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Falha ao carregar uploads.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadJobs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantId, apiToken, refreshKey]);

  const handleRetry = async (job: UploadJobResponse) => {
    setActionJobId(job.job_id);
    setError(null);
    setFeedback(null);
    try {
      await retryUploadJob(job.job_id, requestOptions);
      setFeedback(`Job reenfileirado: ${job.filename}`);
      await loadJobs();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Falha ao reenfileirar job.");
    } finally {
      setActionJobId(null);
    }
  };

  const handleCancel = async (job: UploadJobResponse) => {
    setActionJobId(job.job_id);
    setError(null);
    setFeedback(null);
    try {
      await cancelUploadJob(job.job_id, requestOptions);
      setFeedback(`Job cancelado: ${job.filename}`);
      await loadJobs();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Falha ao cancelar job.");
    } finally {
      setActionJobId(null);
    }
  };

  return (
    <GlassCard className="p-5 lg:p-6" elevated>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-black text-white">Upload jobs</h2>
          <p className="mt-1 text-sm text-slate-400">Historico operacional por tenant</p>
        </div>
        <Button
          variant="secondary"
          onClick={() => void loadJobs()}
          disabled={isLoading}
          icon={
            isLoading ? (
              <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
            )
          }
        >
          Refresh
        </Button>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-[180px_1fr_auto]">
        <label className="field-label">
          Status
          <select
            className="input-surface"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value as UploadJobStatus | "")}
            aria-label="Filtro por status de upload"
          >
            <option value="">Todos</option>
            <option value="pending">pending</option>
            <option value="processing">processing</option>
            <option value="completed">completed</option>
            <option value="failed">failed</option>
            <option value="canceled">canceled</option>
          </select>
        </label>
        <label className="field-label">
          Filename
          <Input
            value={filenameFilter}
            onChange={(event) => setFilenameFilter(event.target.value)}
            placeholder="manual.pdf"
            aria-label="Filtro por filename de upload"
          />
        </label>
        <Button
          className="self-end"
          variant="secondary"
          onClick={() => void loadJobs()}
          icon={<Filter className="h-4 w-4" aria-hidden="true" />}
        >
          Filtrar uploads
        </Button>
      </div>

      {feedback ? (
        <p className="mt-4 rounded-lg border border-emerald-300/20 bg-emerald-400/10 p-3 text-sm font-bold text-emerald-100">
          {feedback}
        </p>
      ) : null}
      {error ? <div className="mt-4"><ErrorState message={error} /></div> : null}

      <div className="mt-5">
        {isLoading ? (
          <LoadingState label="Carregando upload jobs" />
        ) : jobs.length === 0 ? (
          <EmptyState
            title="Sem upload jobs"
            description="Os jobs enviados para este tenant aparecem aqui."
          />
        ) : (
          <div className="grid gap-3">
            {jobs.map((job) => (
              <div
                key={job.job_id}
                className="rounded-lg border border-white/10 bg-white/[0.04] p-4"
              >
                <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="truncate text-sm font-black text-white">
                        {job.filename}
                      </h3>
                      <StatusBadge label={job.status} tone={statusTone[job.status]} />
                      <StatusBadge
                        label={`${job.attempts}/${job.max_attempts}`}
                        tone="neutral"
                      />
                    </div>
                    <p className="mt-1 truncate font-mono text-xs text-slate-500">
                      {job.job_id}
                    </p>
                    {jobError(job) ? (
                      <p className="mt-3 rounded-lg border border-rose-300/20 bg-rose-400/10 p-3 text-xs font-semibold text-rose-100">
                        {jobError(job)}
                      </p>
                    ) : null}
                  </div>

                  <div className="flex shrink-0 flex-wrap gap-2">
                    {job.status === "failed" ? (
                      <Button
                        size="sm"
                        variant="secondary"
                        disabled={actionJobId === job.job_id}
                        onClick={() => void handleRetry(job)}
                        icon={<RotateCcw className="h-4 w-4" aria-hidden="true" />}
                        aria-label={`Retry ${job.filename}`}
                      >
                        Retry
                      </Button>
                    ) : null}
                    {job.status === "pending" ? (
                      <Button
                        size="sm"
                        variant="danger"
                        disabled={actionJobId === job.job_id}
                        onClick={() => void handleCancel(job)}
                        icon={<Ban className="h-4 w-4" aria-hidden="true" />}
                        aria-label={`Cancel ${job.filename}`}
                      >
                        Cancel
                      </Button>
                    ) : null}
                  </div>
                </div>

                <dl className="mt-4 grid gap-2 text-xs sm:grid-cols-2 xl:grid-cols-4">
                  <div>
                    <dt className="text-slate-500">Content type</dt>
                    <dd className="mt-1 truncate font-semibold text-slate-200">
                      {job.content_type}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Created</dt>
                    <dd className="mt-1 font-semibold text-slate-200">
                      {formatDate(job.created_at)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Updated</dt>
                    <dd className="mt-1 font-semibold text-slate-200">
                      {formatDate(job.updated_at)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Finished</dt>
                    <dd className="mt-1 font-semibold text-slate-200">
                      {formatDate(job.finished_at)}
                    </dd>
                  </div>
                </dl>
              </div>
            ))}
          </div>
        )}
      </div>
    </GlassCard>
  );
}
