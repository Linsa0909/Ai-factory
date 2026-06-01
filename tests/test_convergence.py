import pytest
from ai_runtime.convergence import check_convergence, ConvergenceError, error_signature


def test_no_convergence_issue_on_first_retry():
    # First run — should not trigger convergence
    check_convergence(
        retry_count=1, current_error="new error",
        previous_error="", previous_output_size=0, current_output_size=100,
    )


def test_same_error_repeated_raises():
    with pytest.raises(ConvergenceError, match="Same error"):
        check_convergence(
            retry_count=2, current_error="err A",
            previous_error="err A", previous_output_size=100, current_output_size=100,
        )


def test_max_retries_exceeded():
    with pytest.raises(ConvergenceError, match="Max retries"):
        check_convergence(
            retry_count=3, current_error="err", previous_error="",
            previous_output_size=0, current_output_size=50,
        )


def test_diff_entropy_rising():
    with pytest.raises(ConvergenceError, match="entropy"):
        check_convergence(
            retry_count=1, current_error="err B", previous_error="err A",
            previous_output_size=100, current_output_size=300,  # 3x > 2.0 threshold
        )


def test_scope_violation_immediate():
    with pytest.raises(ConvergenceError, match="Scope violation"):
        check_convergence(
            retry_count=1, current_error="err", previous_error="",
            previous_output_size=0, current_output_size=50,
            scope_violation=True,
        )


def test_no_diff_generated_raises():
    with pytest.raises(ConvergenceError, match="No diff"):
        check_convergence(
            retry_count=1, current_error="err", previous_error="",
            previous_output_size=0, current_output_size=0,
        )


def test_error_signature_extracts_last_20():
    sig = error_signature("FAILED test_a\n" * 30)
    assert sig.count("\n") == 19  # 20 lines = 19 newlines


def test_error_signature_filters_non_error_lines():
    sig = error_signature("collected 5 items\nPASSED test_a\nFAILED test_b\nERROR test_c\nE   assert 1 == 2\n>   in test_c")
    assert "PASSED" not in sig
    assert "FAILED" in sig
    assert "ERROR" in sig
