"""Patch scope validation — prevent AI from touching forbidden files."""

from fnmatch import fnmatch
from pathlib import Path


def validate_patch_scope(
    changed_files: list[str],
    allowed_patterns: list[str],
    forbidden_patterns: list[str] | None = None,
    workspace: str = "",
) -> tuple[bool, list[str]]:
    """
    Check whether changed files are within allowed scope.
    Returns (is_valid, [violations]).

    Forbidden patterns take priority over allowed patterns.
    """
    violations: list[str] = []
    w = Path(workspace)

    for f in changed_files:
        rel = str(Path(f).relative_to(w)) if w and Path(f).is_relative_to(w) else f

        # Check forbidden first (takes priority)
        if forbidden_patterns:
            for fb in forbidden_patterns:
                if fnmatch(rel, fb):
                    violations.append(f"{rel} (matches forbidden: {fb})")
                    break

        # Check allowed (only if not already flagged as forbidden)
        if not violations or violations[-1] != f"{rel} (matches forbidden: {fb})":
            matched = any(fnmatch(rel, pat) for pat in allowed_patterns)
            if not matched:
                violations.append(f"{rel} (not in allowed scope)")

    return len(violations) == 0, violations
