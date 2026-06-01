"use client";

import { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  icon?: ReactNode;
}

export function Button({
  variant = "primary",
  size = "md",
  loading,
  icon,
  className,
  children,
  disabled,
  ...props
}: ButtonProps) {
  const sizes = {
    sm: "h-7 px-3 text-xs",
    md: "h-9 px-4 text-sm",
    lg: "h-11 px-6 text-base",
  };

  const variants = {
    primary: [
      "bg-white text-black",
      "hover:shadow-[inset_0_1px_0_rgba(255,255,255,.2)]",
      "hover:scale-[1.01]",
      "active:scale-[0.99]",
    ],
    ghost: [
      "bg-transparent",
      "text-zinc-300",
      "hover:bg-zinc-900",
      "hover:text-zinc-100",
    ],
    danger: [
      "bg-red-500/10 text-red-400",
      "border border-red-500/20",
      "hover:bg-red-500/20",
    ],
  };

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2",
        "rounded-xl font-medium",
        "transition-all duration-200",
        "disabled:opacity-40 disabled:pointer-events-none",
        sizes[size],
        variants[variant],
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : icon ? (
        icon
      ) : null}
      {children}
    </button>
  );
}
