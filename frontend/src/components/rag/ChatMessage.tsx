import { Bot, UserRound } from "lucide-react";

import type { ChatMessageItem } from "../../lib/types";
import { cn } from "../../lib/utils";

interface ChatMessageProps {
  message: ChatMessageItem;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isAssistant = message.role === "assistant";
  const Icon = isAssistant ? Bot : UserRound;

  return (
    <article
      className={cn(
        "flex gap-3",
        isAssistant ? "justify-start" : "justify-end",
      )}
    >
      {isAssistant ? (
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-md border border-cyan-300/20 bg-cyan-400/10 text-cyan-100">
          <Icon className="h-4 w-4" aria-hidden="true" />
        </div>
      ) : null}

      <div
        className={cn(
          "max-w-[760px] rounded-lg border px-4 py-3 text-sm leading-6 shadow-glass",
          isAssistant
            ? "border-white/10 bg-white/[0.07] text-slate-200"
            : "border-violet-300/20 bg-violet-400/15 text-violet-50",
        )}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
      </div>

      {!isAssistant ? (
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-md border border-violet-300/20 bg-violet-400/10 text-violet-100">
          <Icon className="h-4 w-4" aria-hidden="true" />
        </div>
      ) : null}
    </article>
  );
}
