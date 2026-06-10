"""Tests for priority.py"""
import sys
sys.path.insert(0, "/mnt/c/Users/Linsa/ai-factory-runtime")
from ai_runtime.task import TaskStatus

from agent_devos.priority import compute_priority
from agent_devos.dag_builder import TaskMeta


def test_compute_priority_higher_for_shallower_tasks():
    shallow = TaskMeta(agent_id="a", agent_type="analyst", dependency_depth=0, artifact_wait_time=0)
    deep = TaskMeta(agent_id="b", agent_type="backend", dependency_depth=3, artifact_wait_time=0)
    p_shallow = compute_priority(shallow, TaskStatus.READY)
    p_deep = compute_priority(deep, TaskStatus.READY)
    assert p_shallow > p_deep


def test_compute_priority_higher_for_longer_wait():
    fast = TaskMeta(agent_id="a", agent_type="analyst", artifact_wait_time=0)
    slow = TaskMeta(agent_id="b", agent_type="analyst", artifact_wait_time=100)
    p_fast = compute_priority(fast, TaskStatus.READY)
    p_slow = compute_priority(slow, TaskStatus.READY)
    assert p_slow > p_fast


def test_human_required_gets_top_priority():
    normal = TaskMeta(agent_id="a", agent_type="analyst")
    human = TaskMeta(agent_id="b", agent_type="backend")
    p_normal = compute_priority(normal, TaskStatus.READY)
    p_human = compute_priority(human, TaskStatus.HUMAN_REQUIRED)
    assert p_human > p_normal


def test_retry_penalty_lowers_priority():
    fresh = TaskMeta(agent_id="a", agent_type="dev", artifact_wait_time=0)
    failed = TaskMeta(agent_id="b", agent_type="dev", artifact_wait_time=0)
    p_fresh = compute_priority(fresh, TaskStatus.READY, retry_count=0)
    p_failed = compute_priority(failed, TaskStatus.READY, retry_count=3)
    assert p_fresh > p_failed


def test_priority_is_integer():
    meta = TaskMeta(agent_id="test", agent_type="analyst")
    p = compute_priority(meta, TaskStatus.READY)
    assert isinstance(p, int)
