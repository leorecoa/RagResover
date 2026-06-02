import type { ApiRequestOptions, UploadResponse } from "../lib/types";
import { UploadPanel } from "../components/rag/UploadPanel";

interface UploadProps extends ApiRequestOptions {
  onUploaded: (response: UploadResponse) => void;
}

export function Upload({ tenantId, apiToken, onUploaded }: UploadProps) {
  return (
    <UploadPanel
      tenantId={tenantId}
      apiToken={apiToken}
      onUploaded={onUploaded}
    />
  );
}
