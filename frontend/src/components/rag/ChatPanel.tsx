import { useState } from "react";
import { MessageSquareText, Send, SlidersHorizontal } from "lucide-react";

import { chatWithDocuments } from "../../lib/api";
import type {
  ApiRequestOptions,
  ChatMessageItem,
  ChatResponse,
  RetrievalDiagnostics,
  Source,
} from "../../lib/types";
import {
  buildSourceFilter,
  clampTopK,
  createActivityId,
  getProviderLabel,
  parseOptionalThreshold,
} from "../../lib/utils";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { GlassCard } from "../ui/GlassCard";
import { Input } from "../ui/Input";
import { LoadingState } from "../ui/LoadingState";
import { StatusBadge } from "../ui/StatusBadge";
import { Textarea } from "../ui/Textarea";
import { ChatMessage } from "./ChatMessage";
import { SourcesPanel } from "./SourcesPanel";

interface ChatPanelProps extends ApiRequestOptions {
  onAnswered: (response: ChatResponse) => void;
  onDiagnostics: (diagnostics?: RetrievalDiagnostics | null) => void;
}

export function ChatPanel({
  tenantId,
  apiToken,
  onAnswered,
  onDiagnostics,
}: ChatPanelProps) {
  const [question, setQuestion] = useState("");
  const [topK, setTopK] = useState(5);
  const [threshold, setThreshold] = useState("");
  const [source, setSource] = useState("");
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [diagnostics, setDiagnostics] = useState<RetrievalDiagnostics | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      return;
    }

    const userMessage: ChatMessageItem = {
      id: createActivityId(),
      role: "user",
      content: trimmedQuestion,
    };

    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await chatWithDocuments(
        {
          question: trimmedQuestion,
          top_k: clampTopK(topK),
          score_threshold: parseOptionalThreshold(threshold),
          metadata_filters: buildSourceFilter(source),
        },
        { tenantId, apiToken },
      );

      setMessages((current) => [
        ...current,
        {
          id: createActivityId(),
          role: "assistant",
          content: response.answer,
          sources: response.sources,
        },
      ]);
      setSources(response.sources);
      setDiagnostics(response.diagnostics ?? null);
      onAnswered(response);
      onDiagnostics(response.diagnostics);
    } catch (caught) {
      const message =
        caught instanceof Error ? caught.message : "Falha ao consultar o chat.";
      setError(message);
      setMessages((current) => [
        ...current,
        {
          id: createActivityId(),
          role: "assistant",
          content: message,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="grid min-h-[calc(100vh-170px)] gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
      <GlassCard className="grid min-h-[680px] grid-rows-[auto_1fr_auto] overflow-hidden" elevated>
        <div className="border-b border-white/10 p-5">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-end">
            <label className="field-label xl:w-28">
              Top K
              <Input
                type="number"
                min={1}
                max={20}
                value={topK}
                onChange={(event) => setTopK(Number(event.target.value))}
                aria-label="Quantidade de fontes"
              />
            </label>
            <label className="field-label xl:w-40">
              Threshold
              <Input
                value={threshold}
                onChange={(event) => setThreshold(event.target.value)}
                placeholder="-1 a 1"
                aria-label="Score threshold do chat"
              />
            </label>
            <label className="field-label xl:flex-1">
              Source
              <Input
                value={source}
                onChange={(event) => setSource(event.target.value)}
                placeholder="manual.pdf"
                aria-label="Filtro de source do chat"
              />
            </label>
          </div>

          {diagnostics ? (
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <SlidersHorizontal className="h-4 w-4 text-cyan-200" aria-hidden="true" />
              <StatusBadge label={`provider ${getProviderLabel(diagnostics)}`} tone="info" />
              <StatusBadge label={`returned ${diagnostics.returned_count ?? 0}`} />
              <StatusBadge label={`tenant ${diagnostics.tenant_id ?? tenantId ?? "-"}`} />
            </div>
          ) : null}
        </div>

        <div className="min-h-0 overflow-auto p-5">
          {messages.length ? (
            <div className="grid gap-4">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              {isLoading ? <LoadingState label="Gerando resposta" /> : null}
            </div>
          ) : (
            <EmptyState
              title="Chat pronto"
              description="Aguardando pergunta."
              icon={<MessageSquareText className="h-5 w-5" aria-hidden="true" />}
              className="min-h-full"
            />
          )}
        </div>

        <div className="sticky bottom-0 border-t border-white/10 bg-slate-950/72 p-5 backdrop-blur-xl">
          {error ? <ErrorState message={error} className="mb-4" /> : null}
          <div className="grid gap-3">
            <Textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={3}
              placeholder="Pergunte sobre os documentos indexados"
              aria-label="Pergunta para o chat"
              onKeyDown={(event) => {
                if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                  event.preventDefault();
                  void handleSubmit();
                }
              }}
            />
            <div className="flex justify-end">
              <Button
                onClick={handleSubmit}
                disabled={isLoading || !question.trim()}
                icon={<Send className="h-4 w-4" aria-hidden="true" />}
              >
                Enviar
              </Button>
            </div>
          </div>
        </div>
      </GlassCard>

      <SourcesPanel sources={sources} />
    </div>
  );
}
