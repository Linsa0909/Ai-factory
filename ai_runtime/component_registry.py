"""Component Registry — loads and lists profile components.

When a FULLSTACK project is detected, the registry copies profile components
into the project workspace so the Agent reuses them instead of reinventing.
"""

import json
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProfileManifest:
    name: str
    version: str
    theme: str
    colors: dict[str, str]
    components: list[str]
    forbidden: list[str]
    required: list[str]


class ComponentRegistry:
    """Load design profiles and deploy their components to projects."""

    def __init__(self, profiles_dir: str | Path):
        self.profiles_dir = Path(profiles_dir)

    def list_profiles(self) -> list[str]:
        """Return available profile names."""
        if not self.profiles_dir.exists():
            return []
        return [
            d.name for d in self.profiles_dir.iterdir()
            if d.is_dir() and (d / "profile.json").exists()
        ]

    def load_manifest(self, profile_name: str) -> ProfileManifest | None:
        """Load a profile's manifest from profile.json."""
        pf = self.profiles_dir / profile_name / "profile.json"
        if not pf.exists():
            return None
        try:
            data = json.loads(pf.read_text())
        except (json.JSONDecodeError, KeyError):
            return None

        comp_dir = self.profiles_dir / profile_name / "components"
        components = (
            sorted([f.stem for f in comp_dir.iterdir() if f.suffix == ".tsx"])
            if comp_dir.exists() else []
        )

        rules = data.get("rules", {})
        return ProfileManifest(
            name=data.get("name", profile_name),
            version=data.get("version", "1.0.0"),
            theme=data.get("theme", "dark"),
            colors=data.get("colors", {}),
            components=components,
            forbidden=[k for k, v in rules.items() if v is False],
            required=[k for k, v in rules.items() if v is True],
        )

    def deploy_to_project(self, profile_name: str, workspace: str) -> Path:
        """Copy profile components and assets to the project workspace.

        Target structure:
            frontend/src/ui/    ← components
            frontend/src/lib/   ← utils.ts
            frontend/src/       ← globals.css
        """
        profile_path = self.profiles_dir / profile_name
        target_ui = Path(workspace) / "frontend" / "src" / "ui"
        target_lib = Path(workspace) / "frontend" / "src" / "lib"

        # Create target directories
        target_ui.mkdir(parents=True, exist_ok=True)
        target_lib.mkdir(parents=True, exist_ok=True)

        # Copy components
        comp_src = profile_path / "components"
        if comp_src.exists():
            for f in comp_src.iterdir():
                if f.suffix == ".tsx":
                    shutil.copy2(f, target_ui / f.name)

        # Copy lib
        lib_src = profile_path / "lib"
        if lib_src.exists():
            for f in lib_src.iterdir():
                shutil.copy2(f, target_lib / f.name)

        # Copy globals.css
        css_src = profile_path / "globals.css"
        if css_src.exists():
            shutil.copy2(css_src, Path(workspace) / "frontend" / "src" / "globals.css")

        # Copy tailwind-preset
        tw_src = profile_path / "tailwind-preset.ts"
        if tw_src.exists():
            shutil.copy2(tw_src, Path(workspace) / "frontend" / "tailwind-preset.ts")

        return target_ui

    def deploy_screenshots(self, profile_name: str, workspace: str) -> list[str]:
        """Copy reference screenshots to .ai-factory/artifacts/screenshots/.
        Returns list of copied file paths.
        """
        src = self.profiles_dir / profile_name / "screenshots"
        if not src.exists():
            return []
        dst = Path(workspace) / ".ai-factory" / "artifacts" / "screenshots"
        dst.mkdir(parents=True, exist_ok=True)
        copied: list[str] = []
        for f in src.iterdir():
            if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                shutil.copy2(f, dst / f.name)
                copied.append(str(dst / f.name))
        return copied
