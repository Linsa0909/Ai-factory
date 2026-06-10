# AgentDevOS — Deterministic Multi-Agent OS Kernel

A deterministic multi-agent execution kernel for full-stack software development. 8 specialized agents collaborate through artifact contracts, orchestrated by a priority-aware scheduler with FSM-driven state management.

## Architecture

```
                         ┌──────────────────────────┐
                         │       Human Gate           │
                         │   Review / Approve / Reject │
                         └──────────┬───────────────┘
                                    │ escalate
                         ┌──────────▼───────────────┐
                         │     Recovery Layer         │
                         │  FixLoop + RetryPolicy     │
                         │  + HallucinationDetect     │
                         └──────────┬───────────────┘
                                    │ fix / retry
                         ┌──────────▼───────────────┐
                         │    Validation Layer        │
                         │  Lint + Test + Build       │
                         │  + Coverage (85%)          │
                         └──────────┬───────────────┘
                                    │ validate
                         ┌──────────▼───────────────┐
                         │     Artifact Layer         │
                         │  Registry + GlobalPolicy   │
                         │  + Schema + OverwriteProt  │
                         └──────────┬───────────────┘
                                    │ contract check
                         ┌──────────▼───────────────┐
                         │     Workflow Layer         │
                         │  DAG Builder + Scheduler   │
                         │  + Priority Function       │
                         └──────┬──────────┬─────────┘
                                │          │
              ┌─────────────────▼──┐  ┌───▼─────────────────┐
              │    Agent Layer      │  │   Runtime Bridge     │
              │                     │  │                      │
              │  analyst.md         │  │  ai-factory-runtime  │
              │  architect.md       │  │  ├─ FSM (25 states)  │
              │  backend.md         │  │  ├─ EventBus         │
              │  frontend.md        │  │  ├─ PatchEngine      │
              │  tester.md          │  │  ├─ SnapshotManager  │
              │  verifier.md        │  │  ├─ Executor         │
              │  recorder.md        │  │  └─ AgentAdapter     │
              │  knowledge.md       │  │                      │
              └─────────────────────┘  └──────────────────────┘
```

## Agent Pipeline

```
User Requirement
      │
      ▼
  ┌─────────┐
  │ analyst │  →  analysis.md + decomposition.md
  └────┬────┘
       │
       ▼
  ┌──────────┐
  │ architect │  →  design/backend-design.md + frontend-design.md
  └────┬─────┘
       │
  ┌────┴────┐
  ▼         ▼
┌──────┐ ┌────────┐
│backend│ │frontend│  →  implementation code + tests
└───┬──┘ └───┬────┘
    └───┬────┘
        ▼
   ┌────────┐
   │ tester  │  →  test-report.md
   └───┬────┘
        │
        ▼
   ┌──────────┐
   │ verifier │  →  verify-report.md
   └───┬──────┘
        │
        ▼
   ┌──────────┐
   │ recorder │  →  flow-log.md + timeline.json + metrics.md
   └───┬──────┘
        │
        ▼
   ┌───────────┐
   │ knowledge │  →  knowledge-summary.md
   └───────────┘
```

## Core Concepts

| Concept | Definition |
|---------|------------|
| **Agent** | A capability contract (agent.md) — defines what, not how |
| **Task** | A workflow unit — one agent invocation in the DAG |
| **Artifact** | A collaboration contract — agents read/write files, never chat |
| **FSM** | 25-state finite state machine per task (ai-runtime) |
| **DAG** | Directed Acyclic Graph — auto-derived from INPUT/OUTPUT contracts |
| **Scheduler** | Priority-aware dispatcher — picks highest-priority READY task |

## Quick Start

### 1. Install

```bash
pip install -e /mnt/c/Users/Linsa/AgentDevOS
pip install -e /mnt/c/Users/Linsa/ai-factory-runtime
```

### 2. Set API Key

```bash
export DEEPSEEK_API_KEY="sk-..."
```

### 3. Create a Workspace

```bash
mkdir my-project && cd my-project && git init
```

### 4. Run the Pipeline

```python
import asyncio
from agent_devos.orchestrator import Orchestrator

async def main():
    orch = Orchestrator(
        workspace="./my-project",
        agents_dir="/mnt/c/Users/Linsa/AgentDevOS/agents",
        deepseek_api_key="sk-...",
    )
    orch.load_agents()
    print(orch.status())

    # Step-by-step execution
    while True:
        result = await orch.run_once()
        print(orch.status())
        if result in ("done", "blocked"):
            break

asyncio.run(main())
```

### 5. Control Gates

```python
# Approve a gate
orch.human_gate.approve("gate1", reviewer="me")

# Reject with reason
orch.human_gate.reject("gate2", "Design does not cover edge cases")
```

## Usage Example: Build a REST API

```bash
# 1. Create workspace
mkdir todo-api && cd todo-api && git init

# 2. Write requirement
cat > requirement.md << 'EOF'
# Todo API
实现一个简单的 Todo REST API：
- POST /todos — 创建待办事项
- GET /todos — 获取待办列表
- PUT /todos/{id} — 更新待办状态
- DELETE /todos/{id} — 删除待办

技术栈：FastAPI + SQLite
要求：单元测试覆盖率 > 85%
EOF

# 3. Run AgentDevOS
python -c "
import asyncio
from agent_devos.orchestrator import Orchestrator

async def main():
    orch = Orchestrator(
        workspace='./todo-api',
        agents_dir='/mnt/c/Users/Linsa/AgentDevOS/agents',
    )
    orch.load_agents()
    for i in range(30):
        result = await orch.run_once()
        s = orch.status()
        print(f'Step {i+1}: {result} | {s[\"by_status\"]}')
        if result in ('done', 'blocked'):
            break

asyncio.run(main())
"
```

**Expected output flow:**

```
Step 1: running | {'pending': 7, 'passed': 1}    # analyst done
Step 2: running | {'pending': 6, 'passed': 2}    # architect done
Step 3: running | {'pending': 5, 'passed': 3}    # backend done
Step 4: running | {'pending': 4, 'passed': 4}    # frontend done
Step 5: running | {'pending': 3, 'passed': 5}    # tester done
Step 6: running | {'pending': 2, 'passed': 6}    # verifier done
Step 7: running | {'pending': 1, 'passed': 7}    # recorder done
Step 8: running | {'pending': 0, 'passed': 8}    # knowledge done
Step 9: done    | {'passed': 8}                  # pipeline complete
```

## File Structure

```
AgentDevOS/
├── agents/                     # 8 agent definition files
│   ├── analyst.md              #   Requirement analysis
│   ├── architect.md            #   Architecture design
│   ├── backend.md              #   Backend implementation
│   ├── frontend.md             #   Frontend implementation
│   ├── tester.md               #   Test execution
│   ├── verifier.md             #   Output verification
│   ├── recorder.md             #   Flow logging
│   └── knowledge.md            #   Knowledge extraction
├── agent_devos/                # Python package
│   ├── agent_loader.py         #   agent.md -> AgentSpec parser
│   ├── artifact_registry.py    #   Global artifact registry
│   ├── global_policy.py        #   Consistency validation engine
│   ├── dag_builder.py          #   DAG from AgentSpec + Registry
│   ├── execution_snapshot.py   #   Deterministic replay layer
│   ├── context_assembler.py    #   4-layer context assembly
│   ├── priority.py             #   Priority scoring function
│   ├── scheduler.py            #   Priority-aware scheduler
│   ├── tool_registry.py        #   Tool registration + execution
│   ├── recovery_engine.py      #   FixLoop + Retry + Hallucination
│   ├── orchestrator.py         #   Top-level facade
│   └── human_gate.py           #   Review/Approve/Reject
├── tests/                      # 47 tests, 100% passing
└── pyproject.toml
```

## Agent Contract Format

Each agent.md is an **executable constraint contract** with 6 required sections:

```markdown
---
schema_version: "1.0"
agent_type: architect
name: 架构师
id: architect
description: 技术设计、架构评估、模块拆解
---

# CAPABILITY         <- What this agent does (and DOES NOT do)
# INPUT              <- Upstream artifact paths (Artifact Contract)
# OUTPUT             <- Downstream deliverable paths
# EXECUTION          <- Phased execution steps (Phase 0: Pre-check -> ...)
# CONSTRAINTS        <- Output format and quality requirements
# TOOLS              <- (optional) Tools the agent is permitted to use
```

**Key principle:** Agents never chat — they read/write files. The INPUT/OUTPUT declarations automatically form the DAG edges.

## FSM States

```
PENDING -> READY -> DISPATCHED -> RUNNING -> PASSED
                                        -> FAILED -> WAITING_RETRY -> FIXING -> VERIFYING -> PASSED
                                                 -> HUMAN_REQUIRED -> READY
                                                 -> BLOCKED -> STALE -> PENDING
                                        -> TIMED_OUT -> WAITING_RETRY
```

## Requirements

- Python 3.12+
- pyyaml >= 6.0
- ai-factory-runtime (local)
- DeepSeek API key (for code generation tasks)
- Claude CLI (for planning/review tasks)

## Repository

https://github.com/Linsa0909/Ai-factory
