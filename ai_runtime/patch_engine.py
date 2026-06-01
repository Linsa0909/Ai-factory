"""Patch Engine: parse AI output, extract code blocks, apply to filesystem atomically."""

import os
import re
from pathlib import Path
from typing import NamedTuple


class AppliedPatch(NamedTuple):
    path: str
    lines_added: int
    lines_removed: int


class PatchApplyError(Exception):
    def __init__(self, msg: str, partial: list[AppliedPatch] | None = None) -> None:
        super().__init__(msg)
        self.partial = partial or []


class PatchEngine:
    """Extract code from AI output and apply to workspace files atomically."""

    def __init__(self, workspace: str | Path) -> None:
        self.workspace = Path(workspace).resolve()

    def extract_and_apply(self, ai_output: str, snapshot_id: str = "") -> list[AppliedPatch]:
        """
        Parse AI output for code blocks with file paths, apply them.

        Format A (code block with file path):
            ```python:backend/app/todo/file.py
            ...code...
            ```

        Format B (heading + code block):
            ## File: backend/app/todo/file.py
            ```python
            ...code...
            ```

        Atomic: if any file write fails, rollback all previously applied patches.
        """
        patches = self._extract_patches(ai_output)
        if not patches:
            raise PatchApplyError("No file patches found in AI output")

        applied: list[AppliedPatch] = []
        snapshots: dict[str, str] = {}  # path -> original content

        try:
            for file_path, content in patches:
                # Security: reject absolute paths (path escape attempt)
                if file_path.startswith("/"):
                    raise PatchApplyError(f"Path escape denied: {file_path}")

                rel_path = file_path.lstrip("/")
                full_path = (self.workspace / rel_path).resolve()

                # Security: ensure path is within workspace
                if not str(full_path).startswith(str(self.workspace)):
                    raise PatchApplyError(f"Path escape denied: {file_path}")

                # Snapshot original content
                if full_path.exists():
                    snapshots[rel_path] = full_path.read_text(encoding="utf-8")
                else:
                    snapshots[rel_path] = ""

                # Atomic write: write to tmp, then rename
                full_path.parent.mkdir(parents=True, exist_ok=True)
                tmp = full_path.with_suffix(full_path.suffix + ".ai_tmp")
                tmp.write_text(content, encoding="utf-8")
                os.replace(str(tmp), str(full_path))

                # Count changes
                original_lines = set(snapshots[rel_path].splitlines())
                new_lines = set(content.splitlines())
                added = len(new_lines - original_lines)
                removed = len(original_lines - new_lines)
                applied.append(
                    AppliedPatch(
                        path=rel_path,
                        lines_added=max(added, 0),
                        lines_removed=max(removed, 0),
                    )
                )

            return applied

        except Exception as e:
            # Rollback all applied patches before re-raising
            for ap in applied:
                full_path = self.workspace / ap.path
                if ap.path in snapshots and snapshots[ap.path]:
                    full_path.write_text(snapshots[ap.path], encoding="utf-8")
                elif full_path.exists():
                    full_path.unlink()
            if not isinstance(e, PatchApplyError):
                raise PatchApplyError(str(e), partial=applied) from e
            raise

    def _extract_patches(self, ai_output: str) -> list[tuple[str, str]]:
        """Extract (file_path, content) pairs from AI output."""
        patches: list[tuple[str, str]] = []

        # Format A: ```python:path/to/file.py\n...code...\n```
        pattern_a = re.compile(
            r"```(?:python|python3)?:([^\s\n]+)\s*\n(.*?)```",
            re.DOTALL,
        )
        for m in pattern_a.finditer(ai_output):
            file_path = m.group(1).strip()
            content = m.group(2).strip()
            # Include .py files or absolute paths (absolute paths need security check)
            if content and (file_path.startswith("/") or file_path.endswith(".py")):
                patches.append((file_path, content))

        # Format B: ## File: path/to/file.py\n```python\n...code...\n```
        pattern_b = re.compile(
            r"##\s*File:\s*([^\s\n]+)\s*\n```(?:python|python3)?\s*\n(.*?)```",
            re.DOTALL,
        )
        for m in pattern_b.finditer(ai_output):
            file_path = m.group(1).strip()
            content = m.group(2).strip()
            # Include .py files or absolute paths (absolute paths need security check)
            if content and (file_path.startswith("/") or file_path.endswith(".py")):
                patches.append((file_path, content))

        return patches
