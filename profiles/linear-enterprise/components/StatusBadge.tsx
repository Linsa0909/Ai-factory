"use client";

import { cn } from "@/lib/utils";

type Status = "online" | "offline" | "warning" | "passed" | "failed" | "running";

const styles: Record<Status, string> = {
  online: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  offline: "bg-zinc-800 text-zinc-500 border-zinc-700",
  warning: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  passed: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  failed: "bg-red-500/10 text-red-400 border-red-500/20",
  running: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
};

const labels: Record<Status, string> = {
  online: "Online",
  offline: "Offline",
  warning: "Warning",
  passed: "Passed",
  failed: "Failed",
  running: "Running",
};

interface Props {
  status: Status;
  label?: string;
  className?: string;
}

export function StatusBadge({ status, label, className }: Props) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5",
        "rounded-full border px-2.5 py-0.5",
        "text-xs font-medium",
        styles[status],
        className,
      )}
    >
      <span className={cn(
        "h-1.5 w-1.5 rounded-full",
        status === "online" || status === "passed"
          ? "bg-emerald-400"
          : status === "offline"
            ? "bg-zinc-500"
            : status === "running"
              ? "bg-indigo-400"
              : "bg-current",
      )} />
      {label || labels[status]}
    </span>
  );
}
