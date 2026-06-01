"use client";

import { LucideIcon, Inbox } from "lucide-react";
import { Button } from "./Button";
import { ReactNode } from "react";

interface Props {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  children?: ReactNode;
}

export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  action,
  children,
}: Props) {
  return (
    <div
      className="
        relative overflow-hidden
        rounded-2xl border border-dashed border-zinc-800
        py-20
      "
    >
      {/* Micro-dots background */}
      <div
        className="
          absolute inset-0 opacity-20
          [background-image:radial-gradient(#27272a_1px,transparent_1px)]
          [background-size:16px_16px]
        "
      />

      <div className="relative z-10 flex flex-col items-center justify-center text-center">
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-zinc-900 border border-zinc-800">
          <Icon className="h-5 w-5 text-zinc-500" />
        </div>

        <h3 className="text-zinc-100 font-medium">{title}</h3>

        {description && (
          <p className="mt-1.5 max-w-sm text-sm text-zinc-500">
            {description}
          </p>
        )}

        {action && (
          <Button
            variant="primary"
            size="sm"
            className="mt-4"
            onClick={action.onClick}
          >
            {action.label}
          </Button>
        )}

        {children}
      </div>
    </div>
  );
}
