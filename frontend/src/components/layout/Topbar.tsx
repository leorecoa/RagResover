import { RefreshCw } from "lucide-react";

import { API_BASE_URL } from "../../lib/api";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { StatusBadge } from "../ui/StatusBadge";

interface TopbarProps {
  pageTitle: string;
  pageSubtitle: string;
  tenantId: string;
  apiToken: string;
  apiStatus: string;
  readyStatus: string;
  isRefreshing: boolean;
  onTenantChange: (value: string) => void;
  onApiTokenChange: (value: string) => void;
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
  apiStatus,
  readyStatus,
  isRefreshing,
  onTenantChange,
  onApiTokenChange,
  onRefresh,
}: TopbarProps) {
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

        <div className="grid gap-3 sm:grid-cols-[minmax(160px,220px)_minmax(160px,220px)_auto] sm:items-end">
          <label className="field-label">
            Tenant
            <Input
              value={tenantId}
              onChange={(event) => onTenantChange(event.target.value)}
              placeholder="tenant-demo"
              aria-label="Tenant ID"
            />
          </label>
          <label className="field-label">
            API token
            <Input
              type="password"
              value={apiToken}
              onChange={(event) => onApiTokenChange(event.target.value)}
              placeholder="opcional"
              aria-label="API token"
            />
          </label>
          <Button
            variant="secondary"
            onClick={onRefresh}
            disabled={isRefreshing}
            icon={<RefreshCw className={isRefreshing ? "h-4 w-4 animate-spin" : "h-4 w-4"} />}
          >
            Atualizar
          </Button>
        </div>
      </div>
      <p className="mt-3 truncate text-xs text-slate-600">{API_BASE_URL}</p>
    </header>
  );
}
