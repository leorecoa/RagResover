import type { ReactNode } from "react";

import type { AuthUser } from "../../lib/types";
import { cn } from "../../lib/utils";
import { Sidebar, type PageKey } from "./Sidebar";
import { Topbar } from "./Topbar";

interface AppShellProps {
  children: ReactNode;
  currentPage: PageKey;
  pageTitle: string;
  pageSubtitle: string;
  tenantId: string;
  apiToken: string;
  authUser: AuthUser;
  apiStatus: string;
  readyStatus: string;
  isRefreshing: boolean;
  onNavigate: (page: PageKey) => void;
  onTenantChange: (value: string) => void;
  onLogout: () => void;
  onRefresh: () => void;
}

export function AppShell({
  children,
  currentPage,
  pageTitle,
  pageSubtitle,
  tenantId,
  apiToken,
  authUser,
  apiStatus,
  readyStatus,
  isRefreshing,
  onNavigate,
  onTenantChange,
  onLogout,
  onRefresh,
}: AppShellProps) {
  const mobilePages: Array<{ key: PageKey; label: string }> = [
    { key: "dashboard", label: "Dashboard" },
    { key: "documents", label: "Documents" },
    { key: "upload", label: "Upload" },
    { key: "search", label: "Search" },
    { key: "chat", label: "Chat" },
  ];

  return (
    <div className="min-h-screen">
      <Sidebar currentPage={currentPage} onNavigate={onNavigate} />
      <div className="min-h-screen lg:pl-72">
        <Topbar
          pageTitle={pageTitle}
          pageSubtitle={pageSubtitle}
          tenantId={tenantId}
          apiToken={apiToken}
          authUser={authUser}
          apiStatus={apiStatus}
          readyStatus={readyStatus}
          isRefreshing={isRefreshing}
          onTenantChange={onTenantChange}
          onLogout={onLogout}
          onRefresh={onRefresh}
        />

        <nav
          className="flex gap-2 overflow-x-auto border-b border-white/10 px-4 py-3 lg:hidden"
          aria-label="Principal"
        >
          {mobilePages.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => onNavigate(item.key)}
              className={cn(
                "min-h-10 shrink-0 rounded-md border px-3 text-sm font-bold transition",
                currentPage === item.key
                  ? "border-cyan-300/25 bg-cyan-300/10 text-white"
                  : "border-white/10 bg-white/[0.04] text-slate-400",
              )}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <main className="px-4 py-5 lg:px-8 lg:py-7">{children}</main>
      </div>
    </div>
  );
}
