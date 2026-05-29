import asyncio
from ai_runtime.agent_adapter import AgentAdapter, AgentResult


async def test_route_returns_claude_for_design():
    adapter = AgentAdapter()
    assert adapter.route("design") == "claude"
    assert adapter.route("review") == "claude"
    assert adapter.route("requirement") == "claude"


async def test_route_returns_deepseek_for_codegen():
    adapter = AgentAdapter()
    assert adapter.route("dev") == "deepseek"
    assert adapter.route("testgen") == "deepseek"
    assert adapter.route("docs") == "deepseek"


async def test_route_returns_deepseek_for_unknown():
    adapter = AgentAdapter()
    assert adapter.route("nonexistent") == "deepseek"


async def test_deepseek_returns_error_without_api_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    adapter = AgentAdapter(deepseek_api_key="")
    result = await adapter._run_deepseek("prompt", "context")
    assert result.success is False
    assert result.model == "deepseek"
    assert "not configured" in result.output


async def test_agent_result_defaults():
    r = AgentResult(success=True, output="hello", files_changed=[], tokens_used=42, model="claude")
    assert r.success is True
    assert r.output == "hello"
    assert r.tokens_used == 42
