import type {
  ApiRequestOptions,
  ChatResponse,
  RetrievalDiagnostics,
} from "../lib/types";
import { ChatPanel } from "../components/rag/ChatPanel";

interface ChatProps extends ApiRequestOptions {
  onAnswered: (response: ChatResponse) => void;
  onDiagnostics: (diagnostics?: RetrievalDiagnostics | null) => void;
}

export function Chat({
  tenantId,
  apiToken,
  onAnswered,
  onDiagnostics,
}: ChatProps) {
  return (
    <ChatPanel
      tenantId={tenantId}
      apiToken={apiToken}
      onAnswered={onAnswered}
      onDiagnostics={onDiagnostics}
    />
  );
}
