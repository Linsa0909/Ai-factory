"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { ReactNode } from "react";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  description?: string;
  children: ReactNode;
  size?: "sm" | "md" | "lg";
}

const widths = { sm: "max-w-sm", md: "max-w-lg", lg: "max-w-2xl" };

export function Dialog({
  open,
  onOpenChange,
  title,
  description,
  children,
  size = "md",
}: Props) {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        {/* Overlay */}
        <DialogPrimitive.Overlay
          className="
            fixed inset-0 z-50
            bg-black/70 backdrop-blur-sm
            animate-fade-in
          "
        />

        {/* Content */}
        <DialogPrimitive.Content
          className={`
            fixed left-1/2 top-1/2 z-50
            w-full ${widths[size]}
            -translate-x-1/2 -translate-y-1/2
            rounded-2xl border border-zinc-800
            bg-zinc-900 shadow-2xl
            animate-scale-in
          `}
        >
          {/* Header */}
          {(title || description) && (
            <div className="flex items-start justify-between border-b border-zinc-800/50 px-6 py-4">
              <div>
                {title && (
                  <DialogPrimitive.Title className="text-sm font-semibold text-zinc-100">
                    {title}
                  </DialogPrimitive.Title>
                )}
                {description && (
                  <DialogPrimitive.Description className="mt-1 text-xs text-zinc-500">
                    {description}
                  </DialogPrimitive.Description>
                )}
              </div>
              <DialogPrimitive.Close
                className="
                  rounded-lg p-1 text-zinc-400
                  hover:bg-zinc-800 hover:text-zinc-200
                  transition-colors
                "
              >
                <X className="h-4 w-4" />
              </DialogPrimitive.Close>
            </div>
          )}

          {/* Body */}
          <div className="px-6 py-4">{children}</div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
