"""Tests for scheduler.py"""
import sys
sys.path.insert(0, "/mnt/c/Users/Linsa/ai-factory-runtime")
from ai_runtime.task import Task, TaskStatus
from ai_runtime.graph import TaskGraph
from ai_runtime.fsm import transition
from agent_devos.dag_builder import TaskMeta
from agent_devos.scheduler import Scheduler


def test_scheduler_picks_highest_priority_ready_task():
    graph = TaskGraph()
    t1 = Task(id="analyst", type="analyst", module="analyst")
    t2 = Task(id="architect", type="architect", module="architect", depends_on=["analyst"])
    graph.add(t1)
    graph.add(t2)
    transition(t1, TaskStatus.READY)

    metas = {
        "analyst": TaskMeta(agent_id="analyst", agent_type="analyst", dependency_depth=0),
        "architect": TaskMeta(agent_id="architect", agent_type="architect", dependency_depth=1),
    }

    scheduler = Scheduler(graph, metas)
    next_task, next_meta = scheduler.next_ready()
    assert next_task is not None
    assert next_task.id == "analyst"


def test_scheduler_returns_none_when_no_ready_tasks():
    graph = TaskGraph()
    t1 = Task(id="analyst", type="analyst", module="analyst")
    t2 = Task(id="architect", type="architect", module="architect", depends_on=["analyst"])
    graph.add(t1)
    graph.add(t2)

    scheduler = Scheduler(graph, {"analyst": TaskMeta(agent_id="analyst", agent_type="analyst")})
    next_task, next_meta = scheduler.next_ready()
    assert next_task is None


def test_scheduler_picks_between_multiple_ready():
    graph = TaskGraph()
    t1 = Task(id="analyst", type="analyst", module="analyst")
    t2 = Task(id="recorder", type="recorder", module="recorder")
    graph.add(t1)
    graph.add(t2)
    transition(t1, TaskStatus.READY)
    transition(t2, TaskStatus.READY)

    metas = {
        "analyst": TaskMeta(agent_id="analyst", agent_type="analyst", dependency_depth=0, artifact_wait_time=0),
        "recorder": TaskMeta(agent_id="recorder", agent_type="recorder", dependency_depth=0, artifact_wait_time=100),
    }

    scheduler = Scheduler(graph, metas)
    next_task, next_meta = scheduler.next_ready()
    assert next_task.id == "recorder"
