"""Fix loop convergence — prevent infinite repair cycles."""



class ConvergenceError(Exception):
    """Raised when auto-fix loop should stop and escalate to human."""
    pass


def check_convergence(
    retry_count: int,
    current_error: str,
    previous_error: str,
    previous_output_size: int,
    current_output_size: int,
    scope_violation: bool = False,
) -> None:
    """
    Check if auto-fix should stop. Raises ConvergenceError if so.
    Returns normally if fix loop should continue.

    Stop conditions (checked in order, first match wins):
    1. Scope violation → immediate stop
    2. Max retries exceeded
    3. Same error repeated (fix not making progress)
    4. Diff entropy rising (AI may be drifting)
    5. No diff generated (fix produced empty output)
    """
    if scope_violation:
        raise ConvergenceError("Scope violation: AI modified forbidden files")

    MAX_RETRY: int = 3  # from policy.STOP_CONDITIONS["retry_exceeded"]
    if retry_count >= MAX_RETRY:
        raise ConvergenceError(f"Max retries ({MAX_RETRY}) exceeded")

    if previous_error and current_error == previous_error:
        raise ConvergenceError(
            "Same error repeated: fix not making progress"
        )

    ENTROPY_THRESHOLD: float = 2.0  # from policy.STOP_CONDITIONS["diff_entropy_rising"]
    if previous_output_size > 0 and current_output_size > previous_output_size * ENTROPY_THRESHOLD:
        raise ConvergenceError(
            f"Diff entropy rising: output size {previous_output_size} → {current_output_size}"
        )

    if current_output_size == 0:
        raise ConvergenceError("No diff generated: fix produced empty output")


def error_signature(stdout: str) -> str:
    """Extract a stable error signature from pytest output (last 20 error lines)."""
    lines = stdout.splitlines()
    error_lines = [line for line in lines if line.startswith(("FAILED", "ERROR", "E ", "> "))]
    return "\n".join(error_lines[-20:])
