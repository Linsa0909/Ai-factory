"""Tool Registry — tools belong to Runtime, not Agents.

Agents declare tool needs in their agent.md CAPABILITY section.
Runtime executes tools and owns API keys.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    output: str
    tool_name: str


class Tool(Protocol):
    """Protocol for tool implementations."""
    name: str

    def execute(self, params: dict[str, Any], workspace: str) -> ToolResult:
        ...


class ReadFileTool:
    """Read a file from the workspace."""
    name = "read_file"

    def execute(self, params: dict[str, Any], workspace: str) -> ToolResult:
        path = params.get("path", "")
        if not path:
            return ToolResult(success=False, output="Missing 'path' parameter", tool_name=self.name)
        full_path = Path(workspace) / path
        if not full_path.exists():
            return ToolResult(success=False, output=f"File not found: {path}", tool_name=self.name)
        try:
            content = full_path.read_text(encoding="utf-8")
            return ToolResult(success=True, output=content, tool_name=self.name)
        except Exception as e:
            return ToolResult(success=False, output=str(e), tool_name=self.name)


class WriteFileTool:
    """Write a file to the workspace (atomic via .tmp + rename)."""
    name = "write_file"

    def execute(self, params: dict[str, Any], workspace: str) -> ToolResult:
        path = params.get("path", "")
        content = params.get("content", "")
        if not path:
            return ToolResult(success=False, output="Missing 'path' parameter", tool_name=self.name)

        full_path = Path(workspace) / path
        try:
            full_path.resolve().relative_to(Path(workspace).resolve())
        except ValueError:
            return ToolResult(success=False, output=f"Path traversal detected: {path}", tool_name=self.name)

        full_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = full_path.with_suffix(full_path.suffix + ".tmp")
        try:
            tmp_path.write_text(content, encoding="utf-8")
            tmp_path.replace(full_path)
            return ToolResult(success=True, output=f"Written: {path}", tool_name=self.name)
        except Exception as e:
            return ToolResult(success=False, output=str(e), tool_name=self.name)


class RunTestTool:
    """Run pytest in the workspace."""
    name = "run_test"

    def execute(self, params: dict[str, Any], workspace: str) -> ToolResult:
        import subprocess
        try:
            r = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
                cwd=workspace, capture_output=True, text=True, timeout=120,
            )
            return ToolResult(
                success=r.returncode == 0,
                output=r.stdout + "\n" + r.stderr,
                tool_name=self.name,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output="pytest timeout (120s)", tool_name=self.name)
        except FileNotFoundError:
            return ToolResult(success=False, output="pytest not found", tool_name=self.name)


class GitCommitTool:
    """Create a git commit in the workspace."""
    name = "git_commit"

    def execute(self, params: dict[str, Any], workspace: str) -> ToolResult:
        import subprocess
        message = params.get("message", "AgentDevOS commit")
        try:
            subprocess.run(["git", "add", "-u"], cwd=workspace, capture_output=True, text=True)
            r = subprocess.run(
                ["git", "commit", "-m", message, "--allow-empty"],
                cwd=workspace, capture_output=True, text=True,
            )
            return ToolResult(
                success=r.returncode == 0,
                output=r.stdout + "\n" + r.stderr,
                tool_name=self.name,
            )
        except FileNotFoundError:
            return ToolResult(success=False, output="git not found", tool_name=self.name)


class SearchCodeTool:
    """Search codebase for a pattern."""
    name = "search_code"

    def execute(self, params: dict[str, Any], workspace: str) -> ToolResult:
        import subprocess
        pattern = params.get("pattern", "")
        if not pattern:
            return ToolResult(success=False, output="Missing 'pattern' parameter", tool_name=self.name)
        try:
            r = subprocess.run(
                ["grep", "-rn", "--include=*.py", pattern, str(Path(workspace))],
                cwd=workspace, capture_output=True, text=True, timeout=30,
            )
            return ToolResult(
                success=True,
                output=r.stdout if r.stdout else "(no matches)",
                tool_name=self.name,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output="search timeout (30s)", tool_name=self.name)
        except FileNotFoundError:
            return ToolResult(success=False, output="grep not found", tool_name=self.name)


class LintCheckTool:
    """Run ruff lint check."""
    name = "lint_check"

    def execute(self, params: dict[str, Any], workspace: str) -> ToolResult:
        import subprocess
        try:
            r = subprocess.run(
                ["ruff", "check", "."],
                cwd=workspace, capture_output=True, text=True, timeout=60,
            )
            return ToolResult(
                success=r.returncode == 0,
                output=r.stdout + "\n" + r.stderr,
                tool_name=self.name,
            )
        except FileNotFoundError:
            return ToolResult(success=False, output="ruff not found", tool_name=self.name)


class ToolRegistry:
    """Registry of all available tools. Tools belong to Runtime, not Agents."""

    TOOLS: dict[str, type[Tool]] = {
        "read_file": ReadFileTool,
        "write_file": WriteFileTool,
        "run_test": RunTestTool,
        "git_commit": GitCommitTool,
        "search_code": SearchCodeTool,
        "lint_check": LintCheckTool,
    }

    @classmethod
    def get_tools_for_agent(cls, tool_names: list[str]) -> list[Tool]:
        """Return tool instances the agent is permitted to use."""
        tools: list[Tool] = []
        for name in tool_names:
            if name in cls.TOOLS:
                tools.append(cls.TOOLS[name]())
        return tools

    @classmethod
    def execute(cls, tool_name: str, params: dict[str, Any], workspace: str) -> ToolResult:
        """Execute a tool by name. Runtime owns API keys, not agents."""
        if tool_name not in cls.TOOLS:
            return ToolResult(success=False, output=f"Unknown tool: {tool_name}", tool_name=tool_name)
        tool = cls.TOOLS[tool_name]()
        return tool.execute(params, workspace)

    @classmethod
    def list_tools(cls) -> list[str]:
        """Return all available tool names."""
        return list(cls.TOOLS.keys())
