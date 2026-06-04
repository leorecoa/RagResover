import { useCallback, useEffect, useMemo, useState } from "react";

import { ApiError, getHealth, getMe, getReady } from "./lib/api";
import type {
  ActivityItem,
  AuthTokenResponse,
  AuthUser,
  ChatResponse,
  HealthResponse,
  ReadyResponse,
  RetrievalDiagnostics,
  SearchResponse,
  UploadJobResponse,
} from "./lib/types";
import { createActivityId, getProviderLabel } from "./lib/utils";
import { AppShell } from "./components/layout/AppShell";
import type { PageKey } from "./components/layout/Sidebar";
import { Chat } from "./pages/Chat";
import { Dashboard } from "./pages/Dashboard";
import { Documents } from "./pages/Documents";
import { LoginPage } from "./pages/Login";
import { OrganizationPage } from "./pages/Organization";
import { SearchPage } from "./pages/Search";
import { Upload } from "./pages/Upload";

const pageCopy: Record<PageKey, { title: string; subtitle: string }> = {
  dashboard: {
    title: "Dashboard",
    subtitle: "Operacao local-first para documentos privados.",
  },
  upload: {
    title: "Upload",
    subtitle: "Ingestao de TXT, Markdown, JSON, PDF e DOCX.",
  },
  documents: {
    title: "Documents",
    subtitle: "Gestao de documentos, metadados e chunks por tenant.",
  },
  search: {
    title: "Search",
    subtitle: "Busca semantica com threshold, top K e filtros.",
  },
  chat: {
    title: "Chat",
    subtitle: "Respostas RAG com fontes recuperadas.",
  },
  organization: {
    title: "Organization",
    subtitle: "Settings, membros, convites e RBAC por organizacao.",
  },
};

function isReadyResponse(value: unknown): value is ReadyResponse {
  if (!value || typeof value !== "object") {
    return false;
  }
  const candidate = value as Partial<ReadyResponse>;
  return (
    typeof candidate.status === "string" &&
    typeof candidate.database === "string" &&
    typeof candidate.storage === "string" &&
    typeof candidate.env === "string" &&
    typeof candidate.version === "string"
  );
}

function extractReadyFromError(error: unknown): ReadyResponse | null {
  if (!(error instanceof ApiError)) {
    return null;
  }

  const payload = error.payload;
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail?: unknown }).detail;
    if (isReadyResponse(detail)) {
      return detail;
    }
  }

  return null;
}

function readStoredTenant(): string {
  return window.localStorage.getItem("ragresover.tenant") ?? "tenant-demo";
}

function readStoredToken(): string {
  return window.localStorage.getItem("ragresover.token") ?? "";
}

function readStoredUser(): AuthUser | null {
  const raw = window.localStorage.getItem("ragresover.user");
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    window.localStorage.removeItem("ragresover.user");
    return null;
  }
}

function selectTenant(user: AuthUser, preferredTenantId: string): string {
  const memberships = user.organizations;
  if (memberships.some((membership) => membership.organization_id === preferredTenantId)) {
    return preferredTenantId;
  }
  return memberships[0]?.organization_id ?? preferredTenantId;
}

export default function App() {
  const [currentPage, setCurrentPage] = useState<PageKey>("dashboard");
  const [tenantId, setTenantId] = useState(readStoredTenant);
  const [apiToken, setApiToken] = useState(readStoredToken);
  const [authUser, setAuthUser] = useState<AuthUser | null>(readStoredUser);
  const [isCheckingAuth, setIsCheckingAuth] = useState(() => Boolean(readStoredToken()));
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [ready, setReady] = useState<ReadyResponse | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [documentsCount, setDocumentsCount] = useState(0);
  const [activeProvider, setActiveProvider] = useState("Configured by API");
  const [activities, setActivities] = useState<ActivityItem[]>([]);

  useEffect(() => {
    window.localStorage.setItem("ragresover.tenant", tenantId);
  }, [tenantId]);

  useEffect(() => {
    if (apiToken) {
      window.localStorage.setItem("ragresover.token", apiToken);
    } else {
      window.localStorage.removeItem("ragresover.token");
    }
  }, [apiToken]);

  useEffect(() => {
    if (authUser) {
      window.localStorage.setItem("ragresover.user", JSON.stringify(authUser));
    } else {
      window.localStorage.removeItem("ragresover.user");
    }
  }, [authUser]);

  const clearSession = useCallback(() => {
    setApiToken("");
    setAuthUser(null);
    setTenantId("tenant-demo");
    setCurrentPage("dashboard");
  }, []);

  const applyAuthResponse = useCallback(
    (response: AuthTokenResponse) => {
      const nextTenant = selectTenant(response.user, tenantId);
      setApiToken(response.access_token);
      setAuthUser(response.user);
      setTenantId(nextTenant);
      setCurrentPage("dashboard");
    },
    [tenantId],
  );

  useEffect(() => {
    if (!apiToken) {
      setIsCheckingAuth(false);
      return;
    }

    let active = true;
    setIsCheckingAuth(true);

    getMe({ tenantId, apiToken })
      .then((user) => {
        if (!active) {
          return;
        }
        setAuthUser(user);
        setTenantId((currentTenant) => selectTenant(user, currentTenant));
      })
      .catch((caught) => {
        if (!active) {
          return;
        }
        console.warn(caught instanceof Error ? caught.message : "Sessao expirada.");
        clearSession();
      })
      .finally(() => {
        if (active) {
          setIsCheckingAuth(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const addActivity = useCallback((item: Omit<ActivityItem, "id">) => {
    setActivities((current) => [
      { ...item, id: createActivityId() },
      ...current,
    ].slice(0, 8));
  }, []);

  const refreshStatus = useCallback(async () => {
    setIsRefreshing(true);
    setStatusError(null);

    try {
      const nextHealth = await getHealth();
      setHealth(nextHealth);

      try {
        const nextReady = await getReady();
        setReady(nextReady);
      } catch (caught) {
        const degradedReady = extractReadyFromError(caught);
        if (degradedReady) {
          setReady(degradedReady);
        } else {
          setReady(null);
        }
        setStatusError(
          caught instanceof Error ? caught.message : "Readiness indisponivel.",
        );
      }
    } catch (caught) {
      setHealth(null);
      setReady(null);
      setStatusError(caught instanceof Error ? caught.message : "API indisponivel.");
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void refreshStatus();
  }, [refreshStatus]);

  const handleDiagnostics = useCallback(
    (diagnostics?: RetrievalDiagnostics | null) => {
      setActiveProvider(getProviderLabel(diagnostics));
    },
    [],
  );

  const handleUploadCompleted = useCallback(
    (response: UploadJobResponse) => {
      setDocumentsCount((current) => current + 1);
      addActivity({
        label: `Upload: ${response.filename}`,
        detail: `Job ${response.status} com documento ${response.document_id ?? "pendente"}`,
        tone: "emerald",
      });
    },
    [addActivity],
  );

  const handleDeleted = useCallback(
    (document: { file_name: string; chunks_count: number }) => {
      setDocumentsCount((current) => Math.max(0, current - 1));
      addActivity({
        label: `Delete: ${document.file_name}`,
        detail: `${document.chunks_count} chunks removidos`,
        tone: "cyan",
      });
    },
    [addActivity],
  );

  const handleSearched = useCallback(
    (response: SearchResponse) => {
      addActivity({
        label: `Search: ${response.query}`,
        detail: `${response.results.length} trechos recuperados`,
        tone: "cyan",
      });
    },
    [addActivity],
  );

  const handleAnswered = useCallback(
    (response: ChatResponse) => {
      addActivity({
        label: `Chat: ${response.question}`,
        detail: `${response.sources.length} fontes citadas`,
        tone: "violet",
      });
    },
    [addActivity],
  );

  const page = pageCopy[currentPage];
  const apiStatus = health?.status ?? (statusError ? "offline" : "checking");
  const readyStatus = ready?.status ?? "unknown";

  const content = useMemo(() => {
    const requestOptions = {
      tenantId,
      apiToken,
    };

    switch (currentPage) {
      case "dashboard":
        return (
          <Dashboard
            health={health}
            ready={ready}
            statusError={statusError}
            documentsCount={documentsCount}
            activeProvider={activeProvider}
            tenantId={tenantId}
            activities={activities}
            isRefreshing={isRefreshing}
            onRefresh={refreshStatus}
            onNavigate={setCurrentPage}
          />
        );
      case "upload":
        return (
          <Upload
            {...requestOptions}
            onCompleted={handleUploadCompleted}
            onOpenDocuments={() => setCurrentPage("documents")}
          />
        );
      case "documents":
        return <Documents {...requestOptions} onDeleted={handleDeleted} />;
      case "search":
        return (
          <SearchPage
            {...requestOptions}
            onSearched={handleSearched}
            onDiagnostics={handleDiagnostics}
          />
        );
      case "chat":
        return (
          <Chat
            {...requestOptions}
            onAnswered={handleAnswered}
            onDiagnostics={handleDiagnostics}
          />
        );
      case "organization":
        return <OrganizationPage {...requestOptions} />;
      default:
        return null;
    }
  }, [
    activities,
    activeProvider,
    apiToken,
    currentPage,
    documentsCount,
    handleAnswered,
    handleDiagnostics,
    handleDeleted,
    handleSearched,
    handleUploadCompleted,
    health,
    isRefreshing,
    ready,
    refreshStatus,
    statusError,
    tenantId,
  ]);

  if (isCheckingAuth) {
    return (
      <main className="grid min-h-screen place-items-center px-4 text-center">
        <div>
          <p className="text-sm font-bold uppercase tracking-[0.18em] text-cyan-100">
            RagResover
          </p>
          <p className="mt-3 text-sm text-slate-400">Validando sessao...</p>
        </div>
      </main>
    );
  }

  if (!authUser || !apiToken) {
    return <LoginPage onAuthenticated={applyAuthResponse} />;
  }

  return (
    <AppShell
      currentPage={currentPage}
      pageTitle={page.title}
      pageSubtitle={page.subtitle}
      tenantId={tenantId}
      apiToken={apiToken}
      authUser={authUser}
      apiStatus={apiStatus}
      readyStatus={readyStatus}
      isRefreshing={isRefreshing}
      onNavigate={setCurrentPage}
      onTenantChange={setTenantId}
      onLogout={clearSession}
      onRefresh={refreshStatus}
    >
      {content}
    </AppShell>
  );
}
