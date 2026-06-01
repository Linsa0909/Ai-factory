"use client";

import { ReactNode, useState, useRef } from "react";
import { cn } from "@/lib/utils";

interface Props {
  content: string;
  children: ReactNode;
  side?: "top" | "bottom" | "left" | "right";
  className?: string;
}

export function Tooltip({
  content,
  children,
  side = "top",
  className,
}: Props) {
  const [visible, setVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const positions: Record<string, string> = {
    top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
    bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
    left: "right-full top-1/2 -translate-y-1/2 mr-2",
    right: "left-full top-1/2 -translate-y-1/2 ml-2",
  };

  return (
    <div
      ref={ref}
      className="relative inline-flex"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div
          className={cn(
            "absolute z-50",
            "rounded-lg border border-zinc-700 bg-zinc-800 px-2.5 py-1.5",
            "text-xs text-zinc-200",
            "shadow-lg backdrop-blur-sm",
            "pointer-events-none",
            "animate-fade-in",
            positions[side],
            className,
          )}
        >
          {content}
        </div>
      )}
    </div>
  );
}
