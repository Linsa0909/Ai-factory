from ai_runtime.scope import validate_patch_scope


def test_valid_patch_passes():
    ok, violations = validate_patch_scope(
        changed_files=["backend/app/todo/service.py"],
        allowed_patterns=["backend/app/todo/*.py"],
        forbidden_patterns=["backend/app/core/*"],
    )
    assert ok is True
    assert violations == []


def test_forbidden_file_violated():
    ok, violations = validate_patch_scope(
        changed_files=["backend/app/core/db.py"],
        allowed_patterns=["backend/app/todo/*.py"],
        forbidden_patterns=["backend/app/core/*"],
    )
    assert ok is False
    assert any("forbidden" in v for v in violations)


def test_out_of_scope_file_violated():
    ok, violations = validate_patch_scope(
        changed_files=["backend/app/auth/service.py"],
        allowed_patterns=["backend/app/todo/*.py"],
    )
    assert ok is False
    assert any("not in allowed scope" in v for v in violations)


def test_multiple_files_mixed():
    ok, violations = validate_patch_scope(
        changed_files=["backend/app/todo/service.py", "backend/app/core/db.py"],
        allowed_patterns=["backend/app/todo/*.py"],
        forbidden_patterns=["backend/app/core/*"],
    )
    assert ok is False
    assert len(violations) >= 1


def test_empty_changed_files():
    ok, violations = validate_patch_scope(
        changed_files=[],
        allowed_patterns=["backend/app/todo/*.py"],
    )
    assert ok is True
    assert violations == []


def test_no_forbidden_patterns():
    ok, violations = validate_patch_scope(
        changed_files=["backend/app/todo/service.py"],
        allowed_patterns=["backend/app/todo/*.py"],
    )
    assert ok is True
