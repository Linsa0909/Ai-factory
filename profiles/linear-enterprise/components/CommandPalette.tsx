"use client";

import { useEffect, useState, useCallback, ReactNode } from "react";
import { Search } from "lucide-react";

interface CommandItem {
  id: string;
  label: string;
  icon?: ReactNode;
  shortcut?: string;
  onSelect: () => void;
  category?: string;
}

interface Props {
  items: CommandItem[];
  placeholder?: string;
}

/**
 * Linear-style Command Palette (⌘K).
 * Keyboard-first: ⌘K to open, ↑↓ to navigate, ↵ to select, Esc to close.
 */
export function CommandPalette({ items, placeholder = "Search commands..." }: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(0);

  const filtered = items.filter((item) =>
    item.label.toLowerCase().includes(query.toLowerCase()),
  );

  // Reset selection when query changes
  useEffect(() => {
    setSelected(0);
  }, [query]);

  // Keyboard shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelected((s) => Math.min(s + 1, filtered.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelected((s) => Math.max(s - 1, 0));
      } else if (e.key === "Enter" && filtered[selected]) {
        filtered[selected].onSelect();
        setOpen(false);
      }
    },
    [filtered, selected],
  );

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
        onClick={() => setOpen(false)}
      />

      {/* Palette */}
      <div
        className="
          fixed left-1/2 top-[20%] z-50
          w-full max-w-md -translate-x-1/2
          overflow-hidden rounded-2xl
          border border-zinc-800
          bg-zinc-900 shadow-2xl
          animate-scale-in
        "
      >
        {/* Search input */}
        <div className="flex items-center gap-2 border-b border-zinc-800/50 px-4">
          <Search className="h-4 w-4 text-zinc-500" />
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="
              h-12 flex-1 bg-transparent text-sm text-zinc-100
              placeholder:text-zinc-500
              focus:outline-none
            "
          />
          <kbd className="rounded-md border border-zinc-700 bg-zinc-800 px-1.5 py-0.5 text-xs text-zinc-500">
            Esc
          </kbd>
        </div>

        {/* Results */}
        <div className="max-h-64 overflow-auto p-2">
          {filtered.length === 0 ? (
            <p className="px-3 py-4 text-center text-sm text-zinc-500">
              No results found
            </p>
          ) : (
            filtered.map((item, i) => (
              <button
                key={item.id}
                onClick={() => {
                  item.onSelect();
                  setOpen(false);
                }}
                className={`
                  flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm
                  transition-colors
                  ${i === selected ? "bg-zinc-800 text-zinc-100" : "text-zinc-400"}
                `}
              >
                {item.icon && <span className="h-4 w-4">{item.icon}</span>}
                <span className="flex-1 text-left">{item.label}</span>
                {item.shortcut && (
                  <kbd className="rounded-md border border-zinc-700 bg-zinc-800 px-1.5 py-0.5 text-xs text-zinc-500">
                    {item.shortcut}
                  </kbd>
                )}
              </button>
            ))
          )}
        </div>
      </div>
    </>
  );
}
