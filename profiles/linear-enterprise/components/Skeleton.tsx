"use client";

import { cn } from "@/lib/utils";

interface Props {
  className?: string;
  /** Preset layouts for common loading patterns */
  variant?: "text" | "card" | "table-row" | "metric" | "page";
}

function SkeletonBlock({ className }: { className?: string }) {
  return (
    <div className={cn("animate-pulse rounded-lg bg-zinc-800", className)} />
  );
}

export function Skeleton({ className, variant = "text" }: Props) {
  if (variant === "page") {
    return (
      <div className="space-y-8">
        {/* Section header */}
        <div className="space-y-2">
          <SkeletonBlock className="h-7 w-48" />
          <SkeletonBlock className="h-4 w-96" />
        </div>
        {/* Metric cards */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <Skeleton variant="metric" />
          <Skeleton variant="metric" />
          <Skeleton variant="metric" />
        </div>
        {/* Table */}
        <Skeleton variant="card" />
      </div>
    );
  }

  if (variant === "metric") {
    return (
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 space-y-3">
        <SkeletonBlock className="h-3 w-20" />
        <SkeletonBlock className="h-8 w-16" />
        <SkeletonBlock className="h-3 w-24" />
      </div>
    );
  }

  if (variant === "card") {
    return (
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 space-y-3">
        <SkeletonBlock className="h-4 w-1/3" />
        {[1, 2, 3, 4].map((i) => (
          <SkeletonBlock key={i} className="h-3 w-full" />
        ))}
      </div>
    );
  }

  if (variant === "table-row") {
    return (
      <div className="flex items-center gap-4 py-3">
        <SkeletonBlock className="h-4 w-1/4" />
        <SkeletonBlock className="h-4 w-1/4" />
        <SkeletonBlock className="h-4 w-1/4" />
        <SkeletonBlock className="h-4 w-1/4" />
      </div>
    );
  }

  // text: single line
  return <SkeletonBlock className={cn("h-4 w-full", className)} />;
}
