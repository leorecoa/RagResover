import { LogOut, RefreshCw } from "lucide-react";

import { API_BASE_URL } from "../../lib/api";
import type { AuthUser } from "../../lib/types";
import { Button } from "../ui/Button";
import { StatusBadge } from "../ui/StatusBadge";

interface TopbarProps {
  pageTitle: string;
  pageSubtitle: string;
  tenantId: string;
  apiToken: string;
  authUser: AuthUser;
  apiStatus: string;
  readyStatus: string;
  isRefreshing: boolean;
  onTenantChange: (value: string) => void;
  onLogout: () => void;
  onRefresh: () => void;
}

function statusTone(value: string): "success" | "danger" | "neutral" | "warning" {
  if (value === "healthy" || value === "ready") {
    return "success";
  }
  if (value === "offline" || value === "unavailable" || value === "error") {
    return "danger";
  }
  if (value === "not_ready") {
    return "warning";
  }
  return "neutral";
}

export function Topbar({
  pageTitle,
  pageSubtitle,
  tenantId,
  apiToken,
  authUser,
  apiStatus,
  readyStatus,
  isRefreshing,
  onTenantChange,
  onLogout,
  onRefresh,
}: TopbarProps) {
  const currentMembership = authUser.organizations.find(
    (membership) => membership.organization_id === tenantId,
  );
  const userLabel = authUser.full_name?.trim() || authUser.email;

  return (
    <header className="sticky top-0 z-20 border-b border-white/10 bg-slate-950/55 px-4 py-4 backdrop-blur-2xl lg:px-8">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-black text-white sm:text-2xl">{pageTitle}</h1>
            <StatusBadge label={apiStatus} tone={statusTone(apiStatus)} />
            <StatusBadge label={readyStatus} tone={statusTone(readyStatus)} />
          </div>
          <p className="mt-1 text-sm text-slate-400">{pageSubtitle}</p>
        </div>

        <div className="grid gap-3 sm:grid-cols-[minmax(180px,260px)_minmax(160px,240px)_auto_auto] sm:items-end">
          <div className="min-w-0">
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">
              Sessao
            </p>
            <p className="mt-1 truncate text-sm font-bold text-slate-100">{userLabel}</p>
            <p className="mt-0.5 text-xs text-slate-500">
              {currentMembership?.role ?? "member"} - JWT ativo
            </p>
          </div>
          <label className="field-label">
            Organizacao
            <select
              className="input-surface"
              value={tenantId}
              onChange={(event) => onTenantChange(event.target.value)}
              aria-label="Organizacao atual"
            >
              {authUser.organizations.map((membership) => (
                <option key={membership.organization_id} value={membership.organization_id}>
                  {membership.organization_id} - {membership.role}
                </option>
              ))}
            </select>
          </label>
          <Button
            variant="secondary"
            onClick={onRefresh}
            disabled={isRefreshing}
            icon={<RefreshCw className={isRefreshing ? "h-4 w-4 animate-spin" : "h-4 w-4"} />}
          >
            Atualizar
          </Button>
          <Button
            variant="ghost"
            onClick={onLogout}
            icon={<LogOut className="h-4 w-4" />}
          >
            Sair
          </Button>
        </div>
      </div>
      <p className="mt-3 truncate text-xs text-slate-600">
        {API_BASE_URL} - token {apiToken ? "configurado" : "ausente"}
      </p>
    </header>
  );
}
