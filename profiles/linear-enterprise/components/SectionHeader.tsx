"use client";

import { ReactNode } from "react";

interface Props {
  title: string;
  description?: string;
  actions?: ReactNode;
}

/**
 * Linear-style section header with tight tracking and muted description.
 * Use at the top of every page section.
 */
export function SectionHeader({ title, description, actions }: Props) {
  return (
    <div className="flex items-center justify-between">
      <div className="space-y-1">
        <h2 className="text-xl font-semibold tracking-tight text-zinc-100">
          {title}
        </h2>
        {description && (
          <p className="text-sm text-zinc-500">{description}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
