"""Unified adapter for calling Claude (CLI) and DeepSeek (API). P0: no streaming, no MCP."""

from __future__ import annotations

import asyncio
import datetime
import json
import os
from dataclasses import dataclass
from pathlib import Path

from ai_runtime.policy import ROUTING


@dataclass
class AgentResult:
    """Result from an agent invocation."""
    success: bool
    output: str
    files_changed: list[str]  # Populated by PatchEngine after code extraction. Always empty here.
    tokens_used: int
    model: str


class AgentAdapter:
    """Unified adapter for calling Claude via CLI and DeepSeek via API."""

    def __init__(self, deepseek_api_key: str = "", deepseek_base_url: str = "") -> None:
        self.deepseek_api_key = deepseek_api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.deepseek_base_url = deepseek_base_url or os.getenv(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
        )

    def route(self, task_type: str) -> str:
        """Return the model name for a given task type."""
        return ROUTING.get(task_type, "deepseek")

    async def run(self, task_type: str, prompt: str, context: str, workspace: str) -> AgentResult:
        """Dispatch to the correct model and return result."""
        model = self.route(task_type)
        if model == "claude":
            return await self._run_claude(prompt, context, workspace)
        return await self._run_deepseek(prompt, context, workspace)

    async def _run_claude(self, prompt: str, context: str, workspace: str) -> AgentResult:
        """Call Claude via CLI subprocess. Writes prompt to temp file, executes claude CLI."""
        full_prompt = f"{prompt}\n\n## Context\n\n{context}"
        prompt_dir = Path(workspace) / ".ai-factory" / "artifacts" / "prompts"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        prompt_file = prompt_dir / f"claude-{ts}.md"
        prompt_file.write_text(full_prompt)

        try:
            proc = await asyncio.create_subprocess_exec(
                "claude", "--print", "--output-format", "text",
                "--permission-mode", "plan", str(prompt_file),
                cwd=workspace,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            return AgentResult(
                success=False, output="Claude CLI not found on PATH",
                files_changed=[], tokens_used=0, model="claude",
            )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=600)
        except asyncio.TimeoutError:
            proc.kill()
            return AgentResult(
                success=False, output="Claude CLI timeout",
                files_changed=[], tokens_used=0, model="claude",
            )
        return AgentResult(
            success=proc.returncode == 0,
            output=stdout.decode() if stdout else "",
            files_changed=[], tokens_used=0, model="claude",
        )

    async def _run_deepseek(self, prompt: str, context: str, workspace: str) -> AgentResult:
        """Call DeepSeek API via HTTP."""
        if not self.deepseek_api_key:
            return AgentResult(
                success=False, output="DeepSeek API key not configured",
                files_changed=[], tokens_used=0, model="deepseek",
            )
        try:
            import httpx
        except ImportError:
            return AgentResult(
                success=False, output="httpx not installed",
                files_changed=[], tokens_used=0, model="deepseek",
            )
        try:
            async with httpx.AsyncClient(timeout=300) as client:
                resp = await client.post(
                    f"{self.deepseek_base_url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.deepseek_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": context},
                        ],
                        "temperature": 0.2, "max_tokens": 32000,
                    },
                )
                if resp.status_code != 200:
                    return AgentResult(
                        success=False, output=resp.text,
                        files_changed=[], tokens_used=0, model="deepseek",
                    )
                data = resp.json()
                usage = data.get("usage", {})
                return AgentResult(
                    success=True,
                    output=data["choices"][0]["message"]["content"],
                    files_changed=[],
                    tokens_used=usage.get("total_tokens", 0),
                    model="deepseek",
                )
        except (
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.ReadError,
            httpx.RemoteProtocolError,
            KeyError,
            IndexError,
            json.JSONDecodeError,
        ) as exc:
            return AgentResult(
                success=False, output=str(exc),
                files_changed=[], tokens_used=0, model="deepseek",
            )
