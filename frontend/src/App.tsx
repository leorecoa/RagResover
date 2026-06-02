import { useCallback, useEffect, useMemo, useState } from "react";

import { ApiError, getHealth, getReady } from "./lib/api";
import type {
  ActivityItem,
  ChatResponse,
  HealthResponse,
  ReadyResponse,
  RetrievalDiagnostics,
  SearchResponse,
  UploadResponse,
} from "./lib/types";
import { createActivityId, getProviderLabel } from "./lib/utils";
import { AppShell } from "./components/layout/AppShell";
import type { PageKey } from "./components/layout/Sidebar";
import { Chat } from "./pages/Chat";
import { Dashboard } from "./pages/Dashboard";
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
  search: {
    title: "Search",
    subtitle: "Busca semantica com threshold, top K e filtros.",
  },
  chat: {
    title: "Chat",
    subtitle: "Respostas RAG com fontes recuperadas.",
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

export default function App() {
  const [currentPage, setCurrentPage] = useState<PageKey>("dashboard");
  const [tenantId, setTenantId] = useState(readStoredTenant);
  const [apiToken, setApiToken] = useState("");
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

  const handleUploaded = useCallback(
    (response: UploadResponse) => {
      setDocumentsCount((current) => current + 1);
      addActivity({
        label: `Upload: ${response.filename}`,
        detail: `${response.chunks_count} chunks indexados`,
        tone: "emerald",
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
        return <Upload {...requestOptions} onUploaded={handleUploaded} />;
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
    handleSearched,
    handleUploaded,
    health,
    isRefreshing,
    ready,
    refreshStatus,
    statusError,
    tenantId,
  ]);

  return (
    <AppShell
      currentPage={currentPage}
      pageTitle={page.title}
      pageSubtitle={page.subtitle}
      tenantId={tenantId}
      apiToken={apiToken}
      apiStatus={apiStatus}
      readyStatus={readyStatus}
      isRefreshing={isRefreshing}
      onNavigate={setCurrentPage}
      onTenantChange={setTenantId}
      onApiTokenChange={setApiToken}
      onRefresh={refreshStatus}
    >
      {content}
    </AppShell>
  );
}
