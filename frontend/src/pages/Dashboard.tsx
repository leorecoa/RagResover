import {
  Cpu,
  Database,
  FileStack,
  HardDrive,
  MessageSquareText,
  RefreshCw,
  Server,
  UploadCloud,
  Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type { ActivityItem, HealthResponse, ReadyResponse } from "../lib/types";
import { cn } from "../lib/utils";
import type { PageKey } from "../components/layout/Sidebar";
import { Button } from "../components/ui/Button";
import { ErrorState } from "../components/ui/ErrorState";
import { GlassCard } from "../components/ui/GlassCard";
import { StatusBadge } from "../components/ui/StatusBadge";

interface DashboardProps {
  health: HealthResponse | null;
  ready: ReadyResponse | null;
  statusError: string | null;
  documentsCount: number;
  activeProvider: string;
  tenantId: string;
  activities: ActivityItem[];
  isRefreshing: boolean;
  onRefresh: () => void;
  onNavigate: (page: PageKey) => void;
}

interface MetricCardProps {
  label: string;
  value: string;
  detail: string;
  icon: LucideIcon;
  tone: "cyan" | "emerald" | "violet" | "slate";
}

const toneClasses: Record<MetricCardProps["tone"], string> = {
  cyan: "border-cyan-300/20 bg-cyan-400/10 text-cyan-100",
  emerald: "border-emerald-300/20 bg-emerald-400/10 text-emerald-100",
  violet: "border-violet-300/20 bg-violet-400/10 text-violet-100",
  slate: "border-white/10 bg-white/[0.06] text-slate-200",
};

function MetricCard({ label, value, detail, icon: Icon, tone }: MetricCardProps) {
  return (
    <GlassCard className="p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">
            {label}
          </p>
          <p className="mt-3 truncate text-2xl font-black text-white">{value}</p>
          <p className="mt-1 text-sm text-slate-400">{detail}</p>
        </div>
        <div className={cn("grid h-11 w-11 place-items-center rounded-md border", toneClasses[tone])}>
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
      </div>
    </GlassCard>
  );
}

export function Dashboard({
  health,
  ready,
  statusError,
  documentsCount,
  activeProvider,
  tenantId,
  activities,
  isRefreshing,
  onRefresh,
  onNavigate,
}: DashboardProps) {
  const apiValue = health?.status ?? "offline";
  const readyValue = ready?.status ?? "unknown";
  const storageValue = ready?.storage ?? "unknown";

  const visibleActivities = activities.slice(0, 5);

  return (
    <div className="grid gap-6">
      {statusError ? <ErrorState title="Status da API" message={statusError} /> : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <MetricCard
          label="API"
          value={apiValue}
          detail={health ? `${health.env} / v${health.version}` : "FastAPI"}
          icon={Server}
          tone={apiValue === "healthy" ? "emerald" : "slate"}
        />
        <MetricCard
          label="Readiness"
          value={readyValue}
          detail={ready ? `database ${ready.database}` : "Dependencias"}
          icon={Database}
          tone={readyValue === "ready" ? "emerald" : "violet"}
        />
        <MetricCard
          label="Documentos"
          value={String(documentsCount)}
          detail="sessao atual"
          icon={FileStack}
          tone="cyan"
        />
        <MetricCard
          label="Provider"
          value={activeProvider}
          detail="retrieval ativo"
          icon={Cpu}
          tone="violet"
        />
        <MetricCard
          label="Storage"
          value={storageValue}
          detail="MinIO/S3"
          icon={HardDrive}
          tone={storageValue === "available" ? "emerald" : "slate"}
        />
        <MetricCard
          label="Tenant"
          value={tenantId || "anonymous"}
          detail="header X-Tenant-ID"
          icon={Users}
          tone="cyan"
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
        <GlassCard className="p-5 lg:p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-lg font-black text-white">Atividade recente</h2>
              <p className="mt-1 text-sm text-slate-500">Upload, search e chat</p>
            </div>
            <Button
              variant="secondary"
              onClick={onRefresh}
              disabled={isRefreshing}
              icon={<RefreshCw className={isRefreshing ? "h-4 w-4 animate-spin" : "h-4 w-4"} />}
            >
              Revalidar
            </Button>
          </div>

          <div className="mt-5 grid gap-3">
            {visibleActivities.length ? (
              visibleActivities.map((activity) => {
                const badgeLabel =
                  activity.tone === "emerald"
                    ? "upload"
                    : activity.tone === "violet"
                      ? "chat"
                      : "search";

                return (
                  <div
                    key={activity.id}
                    className="flex items-center justify-between gap-4 rounded-lg border border-white/10 bg-white/[0.04] px-4 py-3"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-bold text-white">{activity.label}</p>
                      <p className="mt-1 truncate text-xs text-slate-500">{activity.detail}</p>
                    </div>
                    <StatusBadge
                      label={badgeLabel}
                      tone={activity.tone === "emerald" ? "success" : "info"}
                    />
                  </div>
                );
              })
            ) : (
              ["Upload pendente", "Busca pendente", "Chat pendente"].map((item) => (
                <div
                  key={item}
                  className="h-16 rounded-lg border border-white/10 bg-white/[0.035] px-4 py-3"
                >
                  <div className="h-3 w-36 rounded-full bg-white/10" />
                  <div className="mt-3 h-2 w-60 max-w-full rounded-full bg-white/[0.06]" />
                </div>
              ))
            )}
          </div>
        </GlassCard>

        <GlassCard className="grid content-between gap-6 p-5 lg:p-6" elevated>
          <div>
            <h2 className="text-lg font-black text-white">Workspace</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              Tenant ativo, documentos privados e respostas com citacoes.
            </p>
          </div>
          <div className="grid gap-3">
            <Button
              onClick={() => onNavigate("upload")}
              icon={<UploadCloud className="h-4 w-4" aria-hidden="true" />}
            >
              Novo upload
            </Button>
            <Button
              variant="secondary"
              onClick={() => onNavigate("chat")}
              icon={<MessageSquareText className="h-4 w-4" aria-hidden="true" />}
            >
              Abrir chat
            </Button>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
