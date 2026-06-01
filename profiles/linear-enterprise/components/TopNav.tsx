"use client";

import { Search, Bell } from "lucide-react";

interface Props {
  title?: string;
}

export function TopNav({ title }: Props) {
  return (
    <header
      className="
        flex h-12 items-center justify-between
        border-b border-zinc-800/50
        bg-black/80 backdrop-blur-xl
        px-6
      "
    >
      <div className="flex items-center gap-3">
        <span className="text-sm font-semibold tracking-tight text-zinc-100">
          NEXUS
        </span>
        {title && (
          <>
            <span className="text-zinc-700">/</span>
            <span className="text-sm text-zinc-400">{title}</span>
          </>
        )}
      </div>

      <div className="flex items-center gap-2">
        <button
          className="
            inline-flex h-8 w-8 items-center justify-center
            rounded-lg text-zinc-400
            hover:bg-zinc-900 hover:text-zinc-200
            transition-colors
          "
        >
          <Search className="h-4 w-4" />
        </button>
        <button
          className="
            inline-flex h-8 w-8 items-center justify-center
            rounded-lg text-zinc-400
            hover:bg-zinc-900 hover:text-zinc-200
            transition-colors
          "
        >
          <Bell className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
}
