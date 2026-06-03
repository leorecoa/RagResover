import type { ApiRequestOptions, UploadJobResponse } from "../lib/types";
import { UploadPanel } from "../components/rag/UploadPanel";

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
  return (
    <UploadPanel
      tenantId={tenantId}
      apiToken={apiToken}
      onCompleted={onCompleted}
      onOpenDocuments={onOpenDocuments}
    />
  );
}
