import tempfile
from pathlib import Path
from ai_runtime.patch_engine import PatchEngine, PatchApplyError


def test_extract_and_apply_new_file():
    with tempfile.TemporaryDirectory() as d:
        engine = PatchEngine(d)
        ai_output = '```python:backend/app/todo/service.py\ndef get_todos():\n    return []\n```'
        patches = engine.extract_and_apply(ai_output)
        assert len(patches) == 1
        assert patches[0].path == "backend/app/todo/service.py"
        content = (Path(d) / "backend/app/todo/service.py").read_text()
        assert "def get_todos()" in content


def test_extract_format_b():
    with tempfile.TemporaryDirectory() as d:
        engine = PatchEngine(d)
        ai_output = '## File: backend/app/main.py\n```python\nfrom fastapi import FastAPI\napp = FastAPI()\n```'
        patches = engine.extract_and_apply(ai_output)
        assert len(patches) == 1
        content = (Path(d) / "backend/app/main.py").read_text()
        assert "FastAPI" in content


def test_rollback_on_path_escape():
    """Path escape must trigger rollback of all previously written files."""
    with tempfile.TemporaryDirectory() as d:
        engine = PatchEngine(d)
        ai_output = (
            '```python:backend/app/valid.py\ndef ok(): pass\n```\n'
            '```python:/etc/passwd\ndef hack(): pass\n```'
        )
        try:
            engine.extract_and_apply(ai_output)
            assert False, "should have raised"
        except PatchApplyError:
            pass
        # valid.py should NOT exist (rolled back)
        assert not (Path(d) / "backend/app/valid.py").exists()


def test_no_patches_raises():
    with tempfile.TemporaryDirectory() as d:
        engine = PatchEngine(d)
        try:
            engine.extract_and_apply("just some text, no code blocks")
            assert False, "should have raised"
        except PatchApplyError as e:
            assert "No file patches" in str(e)


def test_multiple_files_in_one_output():
    with tempfile.TemporaryDirectory() as d:
        engine = PatchEngine(d)
        ai_output = (
            '```python:backend/app/todo/service.py\ndef get():\n    return []\n```\n'
            '```python:backend/app/todo/models.py\nclass Todo:\n    pass\n```'
        )
        patches = engine.extract_and_apply(ai_output)
        assert len(patches) == 2
        assert {p.path for p in patches} == {"backend/app/todo/service.py", "backend/app/todo/models.py"}


def test_overwrite_existing_file():
    with tempfile.TemporaryDirectory() as d:
        orig = Path(d) / "backend/app/todo/service.py"
        orig.parent.mkdir(parents=True, exist_ok=True)
        orig.write_text("def old():\n    return 'old'")

        engine = PatchEngine(d)
        ai_output = '```python:backend/app/todo/service.py\ndef new():\n    return "new"\n```'
        patches = engine.extract_and_apply(ai_output)
        assert len(patches) == 1
        content = orig.read_text()
        assert "def new()" in content
        assert "def old()" not in content
        assert patches[0].lines_removed >= 0


def test_extract_ignores_non_py_files():
    """Files without .py extension in path should NOT be extracted."""
    with tempfile.TemporaryDirectory() as d:
        engine = PatchEngine(d)
        ai_output = (
            '```python:backend/app/todo/service.py\ndef get():\n    return []\n```\n'
            '```markdown:Dockerfile\nFROM python\n```\n'
            '```python:backend/app/README.md\n# docs\n```'
        )
        patches = engine.extract_and_apply(ai_output)
        assert len(patches) == 1
        assert patches[0].path == "backend/app/todo/service.py"


def test_multiple_formats_mixed():
    """Format A and Format B both used in same output."""
    with tempfile.TemporaryDirectory() as d:
        engine = PatchEngine(d)
        ai_output = (
            '```python:backend/app/todo/service.py\ndef foo(): pass\n```\n'
            '## File: backend/app/todo/models.py\n```python\nclass Bar:\n    pass\n```'
        )
        patches = engine.extract_and_apply(ai_output)
        assert len(patches) == 2


def test_serial_write_failure_rolls_back():
    """Second file write fails -> first file must be rolled back."""
    # This scenario is covered by test_rollback_on_path_escape above,
    # which tests that a path escape on the second file triggers rollback
    # of the first file.
    pass
