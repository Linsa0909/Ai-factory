"""Tests for tool_registry.py"""
import tempfile
from pathlib import Path
from agent_devos.tool_registry import ToolRegistry, ReadFileTool, WriteFileTool


def test_read_file_tool():
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "test.txt").write_text("hello world")
        tool = ReadFileTool()
        result = tool.execute({"path": "test.txt"}, td)
        assert result.success
        assert "hello world" in result.output


def test_read_file_not_found():
    tool = ReadFileTool()
    result = tool.execute({"path": "nonexistent.txt"}, "/tmp")
    assert not result.success


def test_write_file_tool_atomic():
    with tempfile.TemporaryDirectory() as td:
        tool = WriteFileTool()
        result = tool.execute({"path": "output.md", "content": "# Test"}, td)
        assert result.success
        content = (Path(td) / "output.md").read_text()
        assert content == "# Test"


def test_write_file_prevents_path_traversal():
    with tempfile.TemporaryDirectory() as td:
        tool = WriteFileTool()
        result = tool.execute({"path": "../../../etc/passwd", "content": "bad"}, td)
        assert not result.success


def test_tool_registry_list():
    tools = ToolRegistry.list_tools()
    assert "read_file" in tools
    assert "write_file" in tools
    assert "run_test" in tools


def test_tool_registry_execute_unknown_tool():
    result = ToolRegistry.execute("nonexistent_tool", {}, "/tmp")
    assert not result.success
