"""Global artifact registry — tracks who produces/consumes what.

System invariants (enforced):
  - single_writer: True              — one producer per artifact path
  - immutable_after_publish: True    — no modification after first write (content_hash set)
  - versioned: True                  — every artifact has schema_version
  - consumer_tracked: True           — every consumer is registered
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ArtifactEntry:
    """A single artifact in the global registry."""
    path: str
    produced_by: str
    schema_version: str = "1.0"
    required_sections: list[str] = field(default_factory=list)
    allow_overwrite: bool = False
    consumers: list[str] = field(default_factory=list)
    content_hash: str = ""
    published: bool = False


class AmbiguousProducerError(Exception):
    """Raised when two agents claim to produce the same artifact path."""
    pass


class ArtifactRegistry:
    """Global registry of all artifacts in the pipeline."""

    def __init__(self) -> None:
        self._entries: dict[str, ArtifactEntry] = {}

    def register(self, entry: ArtifactEntry) -> None:
        """Register an artifact entry. Raises AmbiguousProducerError on conflict."""
        if entry.path in self._entries:
            existing = self._entries[entry.path]
            if existing.produced_by != entry.produced_by:
                raise AmbiguousProducerError(
                    f"Artifact '{entry.path}' already produced by '{existing.produced_by}', "
                    f"cannot also be produced by '{entry.produced_by}'"
                )
        self._entries[entry.path] = entry

    def lookup_producer(self, path: str) -> str | None:
        """Return the agent_id that produces this artifact, or None."""
        entry = self._entries.get(path)
        return entry.produced_by if entry else None

    def get(self, path: str) -> ArtifactEntry:
        """Get the full ArtifactEntry for a path. Raises KeyError if not found."""
        return self._entries[path]

    def get_consumers(self, path: str) -> list[str]:
        """Return list of agent_ids that consume this artifact."""
        entry = self._entries.get(path)
        return list(entry.consumers) if entry else []

    def add_consumer(self, path: str, consumer_id: str) -> None:
        """Register a consumer for an artifact."""
        if path not in self._entries:
            raise KeyError(f"Artifact '{path}' not registered — cannot add consumer")
        if consumer_id not in self._entries[path].consumers:
            self._entries[path].consumers.append(consumer_id)

    def validate_no_conflict(self, path: str, producer: str) -> bool:
        """Check if a producer can claim this path. True = no conflict."""
        if path not in self._entries:
            return True
        return self._entries[path].produced_by == producer

    def publish(self, path: str, content_hash: str) -> None:
        """Mark an artifact as published with its content hash.
        After publish, overwrite is forbidden (immutability invariant).
        """
        if path not in self._entries:
            raise KeyError(f"Artifact '{path}' not registered — cannot publish")
        entry = self._entries[path]
        if entry.published and not entry.allow_overwrite:
            raise AmbiguousProducerError(
                f"Artifact '{path}' already published by '{entry.produced_by}' — "
                f"immutability invariant violated (content_hash={entry.content_hash})"
            )
        entry.content_hash = content_hash
        entry.published = True

    def can_publish(self, path: str, producer: str) -> bool:
        """Check if an artifact can be published. False if already published
        and allow_overwrite=False."""
        if path not in self._entries:
            return False
        entry = self._entries[path]
        if entry.produced_by != producer:
            return False
        if entry.published and not entry.allow_overwrite:
            return False
        return True

    def all_entries(self) -> dict[str, ArtifactEntry]:
        """Return all registered entries. Returns a copy."""
        return dict(self._entries)
