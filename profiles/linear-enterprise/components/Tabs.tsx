"use client";

import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface Tab {
  key: string;
  label: string;
  icon?: ReactNode;
  count?: number;
}

interface Props {
  tabs: Tab[];
  active: string;
  onChange: (key: string) => void;
  className?: string;
}

export function Tabs({ tabs, active, onChange, className }: Props) {
  return (
    <nav
      className={cn(
        "flex items-center gap-0 border-b border-zinc-800",
        className,
      )}
    >
      {tabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onChange(tab.key)}
          className={cn(
            "relative flex items-center gap-2 px-4 py-3 text-sm font-medium transition-all",
            active === tab.key
              ? "text-zinc-100"
              : "text-zinc-500 hover:text-zinc-300",
          )}
        >
          {tab.icon}
          {tab.label}
          {tab.count !== undefined && (
            <span
              className={cn(
                "rounded-full px-1.5 py-0.5 text-xs",
                active === tab.key
                  ? "bg-zinc-800 text-zinc-300"
                  : "bg-zinc-900 text-zinc-600",
              )}
            >
              {tab.count}
            </span>
          )}
          {/* Active indicator — Linear style underline */}
          {active === tab.key && (
            <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-zinc-100 rounded-full" />
          )}
        </button>
      ))}
    </nav>
  );
}
