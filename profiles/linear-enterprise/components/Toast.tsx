"use client";

import { useEffect, useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import { X, CheckCircle, AlertCircle, Info } from "lucide-react";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
}

// Simple global toast state — no context provider needed for P0
let toastListeners: Array<(toast: Toast | null) => void> = [];
let currentToast: Toast | null = null;

function emit(toast: Toast | null) {
  currentToast = toast;
  toastListeners.forEach((fn) => fn(toast));
}

export function toast(type: ToastType, title: string, description?: string) {
  const id = Math.random().toString(36).slice(2);
  emit({ id, type, title, description });

  // Auto-dismiss after 3s
  setTimeout(() => {
    if (currentToast?.id === id) emit(null);
  }, 3000);
}

const icons: Record<ToastType, typeof CheckCircle> = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
};

const styles: Record<ToastType, string> = {
  success: "border-emerald-500/20 bg-emerald-500/5",
  error: "border-red-500/20 bg-red-500/5",
  info: "border-indigo-500/20 bg-indigo-500/5",
};

const iconColors: Record<ToastType, string> = {
  success: "text-emerald-400",
  error: "text-red-400",
  info: "text-indigo-400",
};

export function ToastContainer() {
  const [toastData, setToastData] = useState<Toast | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const handler = (t: Toast | null) => {
      if (t) {
        setToastData(t);
        requestAnimationFrame(() => setVisible(true));
      } else {
        setVisible(false);
        setTimeout(() => setToastData(null), 200);
      }
    };
    toastListeners.push(handler);
    return () => {
      toastListeners = toastListeners.filter((h) => h !== handler);
    };
  }, []);

  if (!toastData) return null;

  const Icon = icons[toastData.type];

  return (
    <div
      className={cn(
        "fixed bottom-6 right-6 z-[9999]",
        "flex items-start gap-3",
        "max-w-sm rounded-xl border px-4 py-3",
        "shadow-2xl backdrop-blur-xl",
        "transition-all duration-200",
        styles[toastData.type],
        visible
          ? "translate-y-0 opacity-100"
          : "translate-y-2 opacity-0",
      )}
    >
      <Icon className={cn("mt-0.5 h-4 w-4", iconColors[toastData.type])} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-zinc-100">{toastData.title}</p>
        {toastData.description && (
          <p className="text-xs text-zinc-400 mt-0.5">{toastData.description}</p>
        )}
      </div>
      <button
        onClick={() => emit(null)}
        className="rounded-lg p-1 text-zinc-500 hover:text-zinc-300 transition-colors"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
