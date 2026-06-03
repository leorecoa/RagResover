import { useState } from "react";

import type { ApiRequestOptions, UploadJobResponse } from "../lib/types";
import { UploadPanel } from "../components/rag/UploadPanel";
import { UploadHistoryPanel } from "../components/rag/UploadHistoryPanel";

interface UploadProps extends ApiRequestOptions {
  onCompleted: (response: UploadJobResponse) => void;
  onOpenDocuments: () => void;
}

export function Upload({
  tenantId,
  apiToken,
  onCompleted,
  onOpenDocuments,
}: UploadProps) {
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);

  const handleCompleted = (response: UploadJobResponse) => {
    onCompleted(response);
    setHistoryRefreshKey((current) => current + 1);
  };

  return (
    <div className="grid gap-5">
      <UploadPanel
        tenantId={tenantId}
        apiToken={apiToken}
        onCompleted={handleCompleted}
        onOpenDocuments={onOpenDocuments}
      />
      <UploadHistoryPanel
        tenantId={tenantId}
        apiToken={apiToken}
        refreshKey={historyRefreshKey}
      />
    </div>
  );
}
