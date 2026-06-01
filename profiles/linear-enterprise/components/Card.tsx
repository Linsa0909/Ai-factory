"use client";

import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface Props {
  children: ReactNode;
  className?: string;
  hoverable?: boolean;
  padding?: "none" | "sm" | "md" | "lg";
}

const paddings = {
  none: "",
  sm: "p-4",
  md: "p-6",
  lg: "p-8",
};

export function Card({
  children,
  className,
  hoverable = true,
  padding = "md",
}: Props) {
  return (
    <div
      className={cn(
        "rounded-2xl",
        "border border-zinc-800",
        "bg-zinc-900/50 backdrop-blur-xl",
        "transition-all duration-200",
        paddings[padding],
        hoverable && [
          "hover:border-zinc-700",
          "hover:scale-[1.01]",
        ],
        className,
      )}
    >
      {children}
    </div>
  );
}
