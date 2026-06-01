"use client";

import {
  LayoutDashboard,
  TestTube,
  Workflow,
  Server,
  Settings,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

const iconMap: Record<string, LucideIcon> = {
  dashboard: LayoutDashboard,
  test: TestTube,
  workflow: Workflow,
  server: Server,
  settings: Settings,
};

interface NavItem {
  label: string;
  icon: string;
  href: string;
  active?: boolean;
}

interface Props {
  items: NavItem[];
}

export function Sidebar({ items }: Props) {
  return (
    <aside
      className="
        flex w-[200px] flex-shrink-0 flex-col
        border-r border-zinc-800/50
        bg-black
      "
    >
      <nav className="flex-1 space-y-1 p-3">
        {items.map((item) => {
          const Icon = iconMap[item.icon] || LayoutDashboard;
          return (
            <a
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium",
                "transition-all duration-150",
                item.active
                  ? "bg-zinc-900 text-zinc-100"
                  : "text-zinc-400 hover:bg-zinc-900/50 hover:text-zinc-200",
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </a>
          );
        })}
      </nav>

      {/* User avatar area — placeholder for Linear-style profile */}
      <div className="border-t border-zinc-800/50 p-3">
        <div className="flex items-center gap-3 rounded-xl px-3 py-2">
          <div className="h-6 w-6 rounded-full bg-indigo-500" />
          <span className="text-sm text-zinc-400">User</span>
        </div>
      </div>
    </aside>
  );
}
