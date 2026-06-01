"use client";

import { ReactNode, useState, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { ChevronDown } from "lucide-react";

interface Option {
  value: string;
  label: string;
  disabled?: boolean;
}

interface Props {
  options: Option[];
  value?: string;
  onChange: (value: string) => void;
  placeholder?: string;
  error?: string;
  className?: string;
}

export function Select({
  options,
  value,
  onChange,
  placeholder = "Select...",
  error,
  className,
}: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const selected = options.find((o) => o.value === value);

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={ref} className={cn("relative", className)}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className={cn(
          "flex h-10 w-full items-center justify-between rounded-xl border bg-black px-4 text-sm",
          "transition-all duration-200",
          error
            ? "border-red-500/50"
            : "border-zinc-800 hover:border-zinc-700",
          open && "border-indigo-500 ring-2 ring-indigo-500/20",
        )}
      >
        <span className={selected ? "text-zinc-100" : "text-zinc-500"}>
          {selected?.label || placeholder}
        </span>
        <ChevronDown
          className={cn(
            "h-4 w-4 text-zinc-500 transition-transform duration-200",
            open && "rotate-180",
          )}
        />
      </button>

      {open && (
        <div
          className="
            absolute left-0 right-0 z-50 mt-1
            overflow-hidden rounded-xl
            border border-zinc-800 bg-zinc-900
            shadow-2xl animate-scale-in
          "
        >
          {options.map((option) => (
            <button
              key={option.value}
              disabled={option.disabled}
              onClick={() => {
                onChange(option.value);
                setOpen(false);
              }}
              className={cn(
                "flex w-full items-center px-4 py-2.5 text-sm transition-colors",
                option.value === value
                  ? "bg-indigo-500/10 text-indigo-400"
                  : "text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100",
                option.disabled && "opacity-40 cursor-not-allowed",
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}

      {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
    </div>
  );
}
