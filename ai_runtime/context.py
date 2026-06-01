"""Context builder — 4-layer context for AI agent tasks.

Layer 1: Requirement (docs/requirement.md)
Layer 2: Design (docs/design.md)
Layer 3: Profile (design-system.md, component-rules.md, screenshots)
Layer 4: Existing Code (workspace source files, available components)

For frontend tasks, Profile + Available Components are injected at the TOP
of the prompt to enforce design consistency and component reuse.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Build layered context for AI agent tasks."""

    def __init__(self, workspace: str | Path, profiles_dir: str | Path = ""):
        self.workspace = Path(workspace)
        self.profiles_dir = Path(profiles_dir) if profiles_dir else Path(__file__).parent.parent / "profiles"

    def build(
        self,
        task_type: str,
        module: str = "",
        failures: list[str] | None = None,
        profile: str = "",
    ) -> str:
        """Build context string for a task.

        For frontend tasks, injects Profile + Available Components as the
        highest-priority context (placed before requirements).
        """
        parts: list[str] = []

        # --- Layer 3: Profile Context (frontend tasks only) ---
        is_frontend = task_type in ("ui-design", "component-test", "page-dev", "e2e-test")
        if is_frontend and profile:
            profile_context = self._build_profile_context(profile)
            if profile_context:
                parts.append(profile_context)

        # --- Layer 4: Available Components (frontend tasks only) ---
        if is_frontend and profile:
            components_context = self._build_components_context(profile)
            if components_context:
                parts.append(components_context)

        # --- Layer 1: Requirement ---
        req = self._read_doc("requirement.md", max_words=500)
        if req:
            parts.append(f"## Requirement\n\n{req}")

        # --- Layer 2: Design ---
        design = self._read_doc("design.md", max_words=500)
        if design:
            parts.append(f"## Design\n\n{design}")

        # --- Recent failures ---
        if failures:
            parts.append("## Recent Failures\n")
            for f in failures[-3:]:
                parts.append(f"- {f}")

        return "\n\n".join(parts)

    # ── Layer 3: Profile ──────────────────────────────────────────

    def _build_profile_context(self, profile_name: str) -> str:
        """Build the PROFILE SUMMARY block injected at prompt top."""
        profile_path = self.profiles_dir / profile_name
        if not profile_path.exists():
            logger.warning("Profile not found: %s", profile_path)
            return ""

        lines: list[str] = []
        lines.append("## ⚠️ DESIGN PROFILE: " + profile_name)
        lines.append("")
        lines.append("You MUST follow this design profile. Do NOT deviate.")

        # profile.json → structured summary
        pf = profile_path / "profile.json"
        if pf.exists():
            try:
                data = json.loads(pf.read_text())
                lines.append("")
                lines.append("### Profile Summary")
                lines.append(f"- **Theme:** {data.get('theme', 'dark')}")
                lines.append(f"- **Font:** {data.get('font', 'Geist')}")
                lines.append(f"- **Primary:** {data.get('colors', {}).get('foreground', '#fafafa')}")
                lines.append(f"- **Accent:** {data.get('colors', {}).get('accent', '#6366f1')}")
                forbidden = [k for k, v in data.get("rules", {}).items() if v is False]
                if forbidden:
                    lines.append(f"- **Forbidden:** {', '.join(forbidden)}")
                required = [k for k, v in data.get("rules", {}).items() if v is True]
                if required:
                    lines.append(f"- **Required:** {', '.join(required)}")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("Failed to parse profile.json: %s", e)

        # design-system.md → summarized
        ds = profile_path / "design-system.md"
        if ds.exists():
            text = ds.read_text()
            # Extract only ## headings and first sentence of each
            summary_lines = []
            for line in text.splitlines():
                if line.startswith("## "):
                    summary_lines.append(line)
                elif summary_lines and line.startswith("- "):
                    summary_lines.append(line)
            if summary_lines:
                lines.append("")
                lines.append("### Design Rules")
                lines.extend(summary_lines[:30])

        # component-rules.md → MUST/FORBIDDEN extracted
        cr = profile_path / "component-rules.md"
        if cr.exists():
            text = cr.read_text()
            must_section = False
            forbid_section = False
            must_lines: list[str] = []
            forbid_lines: list[str] = []
            for line in text.splitlines():
                ll = line.strip()
                if "Mandatory" in ll or ll.startswith("## Mandatory"):
                    must_section = True
                    forbid_section = False
                    continue
                if "Forbidden" in ll or ll.startswith("## Forbidden"):
                    forbid_section = True
                    must_section = False
                    continue
                if ll.startswith("##") or ll.startswith("#"):
                    must_section = False
                    forbid_section = False
                if must_section and ll.startswith(("-", "1.", "2.")):
                    must_lines.append(ll)
                if forbid_section and ll.startswith("-"):
                    forbid_lines.append(ll)
            if must_lines:
                lines.append("")
                lines.append("### MANDATORY")
                lines.extend(must_lines[:15])
            if forbid_lines:
                lines.append("")
                lines.append("### FORBIDDEN")
                lines.extend(forbid_lines[:10])

        lines.append("")
        return "\n".join(lines)

    # ── Layer 4: Available Components ──────────────────────────────

    def _build_components_context(self, profile_name: str) -> str:
        """Generate AVAILABLE COMPONENTS list and reuse mandate."""
        comp_dir = self.profiles_dir / profile_name / "components"
        if not comp_dir.exists():
            return ""

        components = sorted([
            f.stem for f in comp_dir.iterdir()
            if f.suffix == ".tsx" and not f.name.startswith("_")
        ])

        if not components:
            return ""

        lines: list[str] = []
        lines.append("## ⚠️ AVAILABLE COMPONENTS (MUST reuse — do NOT recreate)")
        lines.append("")
        lines.append("These components ALREADY EXIST in the project.")
        lines.append("Use them directly: `import { X } from \"@/components/ui/X\"`")
        lines.append("")
        lines.append("### Component List")
        for c in components:
            lines.append(f"- **{c}**")
        lines.append("")
        lines.append("### USAGE RULES")
        lines.append("1. **Use existing components first** — do NOT write a new Button, Card, Input, etc.")
        lines.append("2. If a component exists here, import it — never redefine it")
        lines.append("3. You MAY create new components only for business-specific UI not covered above")
        lines.append("4. Every page MUST be wrapped in `<PageShell>`")
        lines.append("5. Every content block MUST use `<Card>`")
        lines.append("6. Every empty list MUST use `<EmptyState>`")
        lines.append("7. Every table MUST use `<DataTable>`")
        lines.append("")
        return "\n".join(lines)

    # ── Helpers ────────────────────────────────────────────────────

    def _read_doc(self, doc_name: str, max_words: int = 500) -> str:
        doc_path = self.workspace / "docs" / doc_name
        if not doc_path.exists():
            return ""
        try:
            content = doc_path.read_text()
        except (OSError, UnicodeDecodeError) as exc:
            logger.warning("Failed to read %s: %s", doc_path, exc)
            return ""
        words = content.split()
        if len(words) > max_words:
            content = " ".join(words[:max_words]) + "\n\n[...truncated]"
        return content
