import {
  BarChart3,
  FileStack,
  FileUp,
  MessageSquareText,
  Settings,
  Search,
  Sparkles,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { cn } from "../../lib/utils";

export type PageKey = "dashboard" | "documents" | "upload" | "search" | "chat" | "organization";

interface NavItem {
  key: PageKey;
  label: string;
  description: string;
  icon: LucideIcon;
}

const navItems: NavItem[] = [
  {
    key: "dashboard",
    label: "Dashboard",
    description: "Status",
    icon: BarChart3,
  },
  {
    key: "upload",
    label: "Upload",
    description: "Ingestao",
    icon: FileUp,
  },
  {
    key: "documents",
    label: "Documents",
    description: "Library",
    icon: FileStack,
  },
  {
    key: "search",
    label: "Search",
    description: "Retrieval",
    icon: Search,
  },
  {
    key: "chat",
    label: "Chat",
    description: "RAG",
    icon: MessageSquareText,
  },
  {
    key: "organization",
    label: "Organization",
    description: "B2B admin",
    icon: Settings,
  },
];

interface SidebarProps {
  currentPage: PageKey;
  onNavigate: (page: PageKey) => void;
}

export function Sidebar({ currentPage, onNavigate }: SidebarProps) {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r border-white/10 bg-slate-950/72 px-4 py-5 backdrop-blur-2xl lg:block">
      <div className="flex h-full flex-col">
        <div className="flex items-center gap-3 px-2">
          <div className="grid h-11 w-11 place-items-center rounded-md border border-cyan-300/20 bg-cyan-400/10 text-cyan-200">
            <Sparkles className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <p className="text-sm font-black uppercase tracking-[0.18em] text-cyan-100">
              RagResover
            </p>
            <p className="mt-0.5 text-xs text-slate-500">Document intelligence</p>
          </div>
        </div>

        <nav className="mt-8 grid gap-2" aria-label="Principal">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.key;

            return (
              <button
                key={item.key}
                type="button"
                onClick={() => onNavigate(item.key)}
                className={cn(
                  "group flex min-h-14 items-center gap-3 rounded-md border px-3 text-left transition",
                  isActive
                    ? "border-cyan-300/25 bg-cyan-300/10 text-white shadow-glow"
                    : "border-transparent text-slate-400 hover:border-white/10 hover:bg-white/[0.07] hover:text-slate-100",
                )}
              >
                <span
                  className={cn(
                    "grid h-9 w-9 place-items-center rounded-md border transition",
                    isActive
                      ? "border-cyan-300/25 bg-cyan-300/12 text-cyan-100"
                      : "border-white/10 bg-white/[0.04] text-slate-400 group-hover:text-cyan-100",
                  )}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-bold">{item.label}</span>
                  <span className="block text-xs text-slate-500">{item.description}</span>
                </span>
              </button>
            );
          })}
        </nav>

        <div className="mt-auto rounded-lg border border-white/10 bg-white/[0.04] p-4">
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">
            Local-first
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            Private RAG workflow with tenant-aware retrieval.
          </p>
        </div>
      </div>
    </aside>
  );
}
