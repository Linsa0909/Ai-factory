"""Minimal context builder. P0: only truncation, no RAG, no embeddings."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Build minimal context for AI agent tasks. P0: truncation only."""

    def __init__(self, workspace: str | Path) -> None:
        self.workspace = Path(workspace)

    def build(self, task_type: str, module: str = "", failures: list[str] | None = None) -> str:
        """Build context string for a task from workspace docs and recent failures.

        Args:
            task_type: Reserved for future use - may vary context format.
            module: Reserved for future use - may filter docs by module.
            failures: Recent failure messages to include in context.
        """
        parts: list[str] = []
        for doc_name in ["requirement.md", "design.md"]:
            doc_path = self.workspace / "docs" / doc_name
            if doc_path.exists():
                try:
                    content = doc_path.read_text()
                except (OSError, UnicodeDecodeError) as exc:
                    logger.warning("Failed to read %s: %s", doc_path, exc)
                    continue
                words = content.split()
                if len(words) > 500:
                    content = " ".join(words[:500]) + "\n\n[...truncated]"
                parts.append(f"## {doc_name.replace('.md', '').title()}\n\n{content}")
        if failures:
            parts.append("## Recent Failures\n")
            for f in failures[-3:]:
                parts.append(f"- {f}")
        return "\n\n".join(parts)
