"use client";

import { ReactNode } from "react";
import { Card } from "./Card";
import { EmptyState } from "./EmptyState";

interface ActivityItem {
  id: string;
  icon?: ReactNode;
  content: ReactNode;
  timestamp: string;
}

interface Props {
  items: ActivityItem[];
  title?: string;
}

export function ActivityFeed({ items, title = "Recent Activity" }: Props) {
  return (
    <Card padding="none">
      <div className="border-b border-zinc-800/50 px-6 py-4">
        <h3 className="text-sm font-medium text-zinc-100">{title}</h3>
      </div>

      {items.length === 0 ? (
        <div className="p-6">
          <EmptyState title="No activity yet" />
        </div>
      ) : (
        <div className="divide-y divide-zinc-800/50">
          {items.map((item) => (
            <div
              key={item.id}
              className="flex items-start gap-3 px-6 py-3 transition-colors hover:bg-zinc-900/50"
            >
              {item.icon && (
                <div className="mt-0.5 flex-shrink-0">{item.icon}</div>
              )}
              <div className="min-w-0 flex-1">
                <div className="text-sm text-zinc-200">{item.content}</div>
                <time className="text-xs text-zinc-500">{item.timestamp}</time>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
