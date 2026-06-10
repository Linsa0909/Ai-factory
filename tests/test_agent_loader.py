"""Tests for agent_loader.py"""
import tempfile
from pathlib import Path
from agent_devos.agent_loader import AgentLoader, AgentSpec, Phase, AgentLoadError

def test_parse_minimal_agent_md():
    content = """---
schema_version: "1.0"
agent_type: architect
name: 架构师
id: architect
description: 技术设计、架构评估、模块拆解
---

# CAPABILITY
负责后端和前端的技术方案设计。禁止直接编写实现代码。

# INPUT
- {issue_id}/analysis.md

# OUTPUT
- {issue_id}/design/backend-design.md
- {issue_id}/design/frontend-design.md

# EXECUTION
## Phase 0: Pre-check
验证 analysis.md 存在。

## Phase 1: 架构设计
输出设计文档。

# CONSTRAINTS
- 输出必须是 Markdown
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        path = f.name

    try:
        spec = AgentLoader.load(path)
        assert spec.schema_version == "1.0"
        assert spec.agent_type == "architect"
        assert spec.id == "architect"
        assert spec.name == "架构师"
        assert spec.description == "技术设计、架构评估、模块拆解"
        assert len(spec.inputs) == 1
        assert "{issue_id}/analysis.md" in spec.inputs
        assert len(spec.outputs) == 2
        assert "{issue_id}/design/backend-design.md" in spec.outputs
        assert "{issue_id}/design/frontend-design.md" in spec.outputs
        assert len(spec.phases) == 2
        assert spec.phases[0].name == "Phase 0: Pre-check"
        assert spec.phases[1].name == "Phase 1: 架构设计"
        assert len(spec.constraints) >= 1
        assert "输出必须是 Markdown" in spec.constraints[0]
        assert spec.raw_md == content
    finally:
        Path(path).unlink()


def test_missing_frontmatter_raises_error():
    import pytest
    content = "# CAPABILITY\nNo frontmatter here."
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        path = f.name
    try:
        with pytest.raises(AgentLoadError, match="No YAML frontmatter"):
            AgentLoader.load(path)
    finally:
        Path(path).unlink()


def test_missing_required_field_raises_error():
    import pytest
    content = """---
schema_version: "1.0"
agent_type: architect
name: Test
---
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        path = f.name
    try:
        with pytest.raises(AgentLoadError, match="Missing required frontmatter field"):
            AgentLoader.load(path)
    finally:
        Path(path).unlink()


def test_unsupported_schema_version_raises_error():
    import pytest
    content = """---
schema_version: "2.0"
agent_type: architect
id: test
name: Test
description: desc
---
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        path = f.name
    try:
        with pytest.raises(AgentLoadError, match="Unsupported schema_version"):
            AgentLoader.load(path)
    finally:
        Path(path).unlink()


def test_load_all_from_directory():
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as td:
        agent1 = Path(td) / "analyst.md"
        agent1.write_text("""---
schema_version: "1.0"
agent_type: analyst
id: analyst
name: 分析师
description: 需求分析
---

# CAPABILITY
分析需求
""")
        agent2 = Path(td) / "architect.md"
        agent2.write_text("""---
schema_version: "1.0"
agent_type: architect
id: architect
name: 架构师
description: 架构设计
---

# CAPABILITY
设计架构
""")
        specs = AgentLoader.load_all(td)
        assert len(specs) == 2
        assert {s.id for s in specs} == {"analyst", "architect"}
