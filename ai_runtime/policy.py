"""P0: immutable policy constants. P1+ moves to YAML."""

MAX_RETRY = 3

STOP_CONDITIONS = {
    "same_error_repeated": 2,
    "diff_entropy_rising": 2.0,
    "regression_rate": 0.3,
    "no_diff_generated": True,
    "scope_violation": "immediate",
    "retry_exceeded": MAX_RETRY,
}

ROUTING: dict[str, str] = {
    "requirement": "claude",
    "design": "claude",
    "review": "claude",
    "testgen": "deepseek",
    "dev": "deepseek",
    "docs": "deepseek",
}

SCOPE_ALLOWED: dict[str, list[str]] = {
    "dev": ["backend/app/{module}/*.py"],
    "testgen": ["backend/tests/*.py"],
    "fix": ["backend/app/{module}/*.py", "backend/tests/test_{module}.py"],
}

SCOPE_FORBIDDEN = ["backend/app/core/*", "backend/app/shared/*"]
