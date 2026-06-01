"use client";

import { LucideIcon } from "lucide-react";
import { Card } from "./Card";

interface Props {
  title: string;
  value: string | number;
  change?: string;
  trend?: "up" | "down" | "neutral";
  icon?: LucideIcon;
}

export function MetricCard({ title, value, change, trend, icon: Icon }: Props) {
  return (
    <Card hoverable padding="md">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium text-zinc-500">{title}</p>
          <p className="text-2xl font-semibold tracking-tight text-zinc-100">
            {value}
          </p>
          {change && (
            <p
              className={`text-xs ${
                trend === "up"
                  ? "text-emerald-400"
                  : trend === "down"
                    ? "text-red-400"
                    : "text-zinc-500"
              }`}
            >
              {change}
            </p>
          )}
        </div>
        {Icon && (
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-800/50 border border-zinc-700/50">
            <Icon className="h-4 w-4 text-zinc-400" />
          </div>
        )}
      </div>
    </Card>
  );
}
