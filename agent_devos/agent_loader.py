"""Parse agent.md files into AgentSpec dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import yaml


@dataclass
class Phase:
    """A single execution phase from agent.md."""
    name: str
    description: str


@dataclass
class AgentSpec:
    """Parsed agent definition. Immutable after construction."""
    schema_version: str
    agent_type: str
    id: str
    name: str
    description: str
    capability: str
    inputs: list[str]
    outputs: list[str]
    phases: list[Phase]
    constraints: list[str]
    raw_md: str


class AgentLoadError(Exception):
    """Raised when an agent.md file cannot be parsed."""
    pass


class AgentLoader:
    """Parse agent.md files into AgentSpec objects."""

    _YAML_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.DOTALL)
    _SECTION_RE = re.compile(r"^#\s+(CAPABILITY|INPUT|OUTPUT|EXECUTION|CONSTRAINTS)$", re.MULTILINE)
    _PHASE_RE = re.compile(r"^##\s+(Phase \d+:.*)$", re.MULTILINE)

    @staticmethod
    def load(filepath: str | Path) -> AgentSpec:
        """Parse a single agent.md file and return AgentSpec."""
        path = Path(filepath)
        if not path.exists():
            raise AgentLoadError(f"Agent file not found: {filepath}")

        raw = path.read_text(encoding="utf-8")

        # 1. Parse YAML frontmatter
        m = AgentLoader._YAML_RE.match(raw)
        if not m:
            raise AgentLoadError(f"No YAML frontmatter found in {filepath}")
        frontmatter = yaml.safe_load(m.group(1))
        body = m.group(2)

        # 2. Validate required frontmatter fields
        for key in ("schema_version", "agent_type", "id", "name", "description"):
            if key not in frontmatter:
                raise AgentLoadError(f"Missing required frontmatter field '{key}' in {filepath}")
        if frontmatter["schema_version"] != "1.0":
            raise AgentLoadError(
                f"Unsupported schema_version '{frontmatter['schema_version']}' in {filepath}. Expected '1.0'"
            )

        # 3. Parse sections
        sections = AgentLoader._parse_sections(body)

        # 4. Parse inputs (bullet list)
        inputs = AgentLoader._parse_bullet_list(sections.get("INPUT", ""))

        # 5. Parse outputs (bullet list)
        outputs = AgentLoader._parse_bullet_list(sections.get("OUTPUT", ""))

        # 6. Parse execution phases
        phases = AgentLoader._parse_phases(sections.get("EXECUTION", ""))

        # 7. Parse constraints (bullet list)
        constraints = AgentLoader._parse_bullet_list(sections.get("CONSTRAINTS", ""))

        return AgentSpec(
            schema_version=str(frontmatter["schema_version"]),
            agent_type=str(frontmatter["agent_type"]),
            id=str(frontmatter["id"]),
            name=str(frontmatter["name"]),
            description=str(frontmatter["description"]),
            capability=sections.get("CAPABILITY", "").strip(),
            inputs=inputs,
            outputs=outputs,
            phases=phases,
            constraints=constraints,
            raw_md=raw,
        )

    @staticmethod
    def _parse_sections(body: str) -> dict[str, str]:
        """Split body into named sections. Returns {SECTION_NAME: content}."""
        sections: dict[str, str] = {}
        matches = list(AgentLoader._SECTION_RE.finditer(body))
        for i, m in enumerate(matches):
            section_name = m.group(1)
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            sections[section_name] = body[start:end].strip()
        return sections

    @staticmethod
    def _parse_bullet_list(text: str) -> list[str]:
        """Extract bullet list items (lines starting with '- ')."""
        items: list[str] = []
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("- "):
                item = stripped[2:].strip()
                if " # " in item:
                    item = item.split(" # ")[0].strip()
                if item:
                    items.append(item)
        return items

    @staticmethod
    def _parse_phases(text: str) -> list[Phase]:
        """Extract Phase headers and following paragraph as description."""
        phases: list[Phase] = []
        lines = text.split("\n")
        current_phase: str | None = None
        current_desc: list[str] = []

        for line in lines:
            phase_m = AgentLoader._PHASE_RE.match(line.strip())
            if phase_m:
                if current_phase:
                    phases.append(Phase(name=current_phase, description="\n".join(current_desc).strip()))
                current_phase = phase_m.group(1)
                current_desc = []
            elif current_phase:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    current_desc.append(stripped)

        if current_phase:
            phases.append(Phase(name=current_phase, description="\n".join(current_desc).strip()))

        return phases

    @staticmethod
    def load_all(agents_dir: str | Path) -> list[AgentSpec]:
        """Load all agent.md files from a directory."""
        dir_path = Path(agents_dir)
        specs: list[AgentSpec] = []
        for md_file in sorted(dir_path.glob("*.md")):
            specs.append(AgentLoader.load(md_file))
        return specs
