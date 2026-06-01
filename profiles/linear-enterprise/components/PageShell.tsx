"use client";

import { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { TopNav } from "./TopNav";

interface Props {
  children: ReactNode;
  /** Sidebar navigation items */
  navItems?: { label: string; icon: string; href: string; active?: boolean }[];
  /** Top-level page title */
  title?: string;
}

/**
 * Every page MUST be wrapped in PageShell.
 * This ensures consistent layout: TopNav + Sidebar + content area.
 */
export function PageShell({ children, navItems = [], title }: Props) {
  return (
    <div className="flex h-screen flex-col bg-black text-zinc-100">
      <TopNav title={title} />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar items={navItems} />

        <main className="flex-1 overflow-auto">
          <div className="mx-auto max-w-7xl p-8">
            {/* Page content animates in */}
            <div className="animate-fade-in">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
