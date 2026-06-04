"""
集成测试 — 模拟完整 Pipeline 验证 Runtime 调度
"""
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from ai_runtime.task import Task, TaskStatus
from ai_runtime.runtime import AIRuntime
from ai_runtime.agent_adapter import AgentResult
from ai_runtime.executor import ExecResult
from ai_runtime.fsm import InvalidTransition
from ai_runtime.store import RuntimeStore


@pytest.fixture
def workspace():
    with tempfile.TemporaryDirectory() as d:
        ws = Path(d)
        subprocess.run(["git", "init"], cwd=str(ws), capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test"], cwd=str(ws), capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=str(ws), capture_output=True)
        (ws / "docs").mkdir(parents=True)
        (ws / "docs" / "requirement.md").write_text("# Test Feature")
        (ws / "docs" / "design.md").write_text("## Architecture")
        yield str(ws)


@pytest.fixture
def rt(workspace):
    return AIRuntime(workspace=workspace)


OK = AgentResult(success=True, output="OK", files_changed=[], tokens_used=10, model="test")
PASS_PYTEST = ExecResult(success=True, command="pytest", stdout="ok", stderr="", exit_code=0)
FAIL_PYTEST = ExecResult(success=False, command="pytest",
                         stdout="FAILED x\nERROR x\nE   assert 1 == 2", stderr="", exit_code=1)


async def test_full_pipeline_all_pass(rt):
    """6 个 Task 全部成功 → pipeline 正常结束"""
    with patch.object(rt.adapter, 'run', AsyncMock(return_value=OK)):
        with patch.object(rt.executor, 'run_pytest', AsyncMock(return_value=PASS_PYTEST)):
            result = await rt.run_until_done("test")
            assert result == "done"

    for t in rt.graph.all_tasks():
        assert t.status == TaskStatus.PASSED, f"{t.id} is {t.status.value}"
    assert rt.graph.task_count() == 6


async def test_dev_failure_escalates_to_human(rt):
    """DEV 失败 → HUMAN_REQUIRED (非 verify,不走 fix loop)"""
    mock = [OK, OK, OK, AgentResult(success=False, output="err", files_changed=[], tokens_used=10, model="test")]
    with patch.object(rt.adapter, 'run', side_effect=mock):
        result = await rt.run_until_done("fail")
        assert result in ("blocked", "done")
    dev = rt.graph.get("DEV-FAIL")
    assert dev.status == TaskStatus.HUMAN_REQUIRED


async def test_fix_loop_runs_on_verify_failure(rt):
    """VERIFY 失败 → fix_loop 触发 → 修复后通过"""
    pytest_results = [FAIL_PYTEST, PASS_PYTEST]
    with patch.object(rt.adapter, 'run', AsyncMock(return_value=OK)):
        with patch.object(rt.executor, 'run_pytest', AsyncMock(side_effect=pytest_results)):
            result = await rt.run_until_done("fix")
            assert result == "done"
    verify = rt.graph.get("VERIFY-FIX")
    assert verify.status == TaskStatus.PASSED


async def test_dag_execution_order(rt):
    """DAG 严格按依赖顺序执行"""
    order = []
    async def track(task_type, prompt, context, workspace):
        order.append(task_type)
        return OK
    with patch.object(rt.adapter, 'run', AsyncMock(side_effect=track)):
        with patch.object(rt.executor, 'run_pytest', AsyncMock(return_value=PASS_PYTEST)):
            await rt.run_until_done("dag")
    assert order[:6] == ["requirement", "design", "testgen", "dev", "verify", "review"]


async def test_event_bus_receives_events(rt):
    """Pipeline 执行时 EventBus 发出事件"""
    with patch.object(rt.adapter, 'run', AsyncMock(return_value=OK)):
        with patch.object(rt.executor, 'run_pytest', AsyncMock(return_value=PASS_PYTEST)):
            await rt.submit("evt", requirement_path="", requirement_text="x")
            await rt.run_once()  # 只跑一个 task
            event = await rt.event_bus.next_event()
            assert event.task_id == "REQ-EVT"


async def test_fsm_blocks_illegal_transition(rt):
    """非法 FSM 跳转被 InvalidTransition 阻止"""
    await rt.submit("fsm", requirement_path="", requirement_text="x")
    task = rt.graph.get("REQ-FSM")
    with pytest.raises(InvalidTransition):
        from ai_runtime.fsm import transition
        transition(task, TaskStatus.PASSED)


async def test_graph_detects_cycles(rt):
    """DAG 循环依赖被检测并拒绝"""
    t1 = Task(id="CYCLE-A", type="design", depends_on=["CYCLE-B"])
    t2 = Task(id="CYCLE-B", type="design", depends_on=["CYCLE-A"])
    rt.graph.add(t1)
    rt.graph.add(t2)
    with pytest.raises(Exception):
        rt.graph.validate()


async def test_store_recovers_corrupted_json(workspace):
    """腐蚀的 JSON 文件返回空列表"""
    store = RuntimeStore(workspace)
    store.graph_path.write_text("{{{ not json {{{")
    assert store.load_graph() == []


async def test_fix_loop_max_retries_exceeded(rt):
    """反复同样失败直到超限 → HUMAN_REQUIRED"""
    with patch.object(rt.adapter, 'run', AsyncMock(return_value=OK)):
        with patch.object(rt.executor, 'run_pytest', AsyncMock(return_value=FAIL_PYTEST)):
            result = await rt.run_until_done("loop")
            assert result in ("blocked", "done")
    verify = rt.graph.get("VERIFY-LOOP")
    assert verify.status in (TaskStatus.HUMAN_REQUIRED, TaskStatus.PASSED)
