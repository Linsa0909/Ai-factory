"""Priority scoring function for the Scheduler.

Higher score = higher priority.
Components:
  - artifact_wait_time: tasks waiting longer get priority (x10)
  - dependency_depth: shallower tasks first — unblocks more downstream (x50 penalty)
  - retry_penalty: failed tasks get deprioritized (x100 penalty per retry)
  - human_boost: human-gated tasks get highest priority (+2000)
"""

from __future__ import annotations

from agent_devos.dag_builder import TaskMeta

# Import TaskStatus from ai-runtime
import sys
sys.path.insert(0, "/mnt/c/Users/Linsa/ai-factory-runtime")
from ai_runtime.task import TaskStatus


def compute_priority(
    meta: TaskMeta,
    status: TaskStatus,
    retry_count: int = 0,
) -> int:
    """Compute priority score. Higher = more urgent."""
    depth_penalty = meta.dependency_depth * 50       # deeper = lower
    wait_boost = int(meta.artifact_wait_time) * 10   # waited longer = higher
    retry_penalty = retry_count * 100                 # failed more = lower
    human_boost = 2000 if status == TaskStatus.HUMAN_REQUIRED else 0

    return wait_boost + human_boost - depth_penalty - retry_penalty
