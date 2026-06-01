"use client";

import { InputHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ error, label, className, id, ...props }, ref) => {
    return (
      <div className="space-y-1.5">
        {label && (
          <label
            htmlFor={id}
            className="text-xs font-medium text-zinc-400"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          className={cn(
            "h-10 w-full rounded-xl border bg-black px-4 text-sm text-zinc-100",
            "placeholder:text-zinc-500",
            "transition-all duration-200",
            error
              ? "border-red-500/50 focus:border-red-500"
              : "border-zinc-800 focus:border-indigo-500",
            "focus:outline-none focus:ring-2 focus:ring-indigo-500/20",
            className,
          )}
          {...props}
        />
        {error && (
          <p className="text-xs text-red-400">{error}</p>
        )}
      </div>
    );
  },
);

Input.displayName = "Input";
