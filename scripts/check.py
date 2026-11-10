"""Exercise 1.5 solution: one command that runs every quality check, like `make check`.

New idea: running other programs with ``subprocess.run`` and using their exit codes.
Run it from the project root with:  uv run python scripts/check.py
"""

from __future__ import annotations

import subprocess  # Start other programs (ruff, pytest) and wait for them
import sys  # sys.executable = the Python of the current virtual environment
from collections.abc import Callable, Sequence  # Types for the runner and the command list

# Each check is (label, command). Using `sys.executable -m tool` guarantees we run the tool
# installed in THIS environment, not some other copy on your PATH.
CHECKS: list[tuple[str, list[str]]] = [
    ("format", [sys.executable, "-m", "ruff", "format", "--check", "."]),  # Is code formatted?
    ("lint", [sys.executable, "-m", "ruff", "check", "."]),  # Any lint findings?
    ("tests", [sys.executable, "-m", "pytest", "-q"]),  # Do the tests pass?
]

# A runner takes a command and returns its exit code. Tests pass a fake runner.
Runner = Callable[[list[str]], int]


def run_command(command: list[str]) -> int:
    """Run one command, streaming its output to the terminal, and return its exit code."""
    completed = subprocess.run(command, check=False)  # check=False: don't raise on failure
    return completed.returncode  # 0 = success, anything else = failure


def run_checks(
    checks: Sequence[tuple[str, list[str]]] = CHECKS, runner: Runner = run_command
) -> int:
    """Run the checks in order, stop at the first failure, and return an exit code."""
    for label, command in checks:  # Fast checks first: formatting fails in milliseconds
        print(f"==> {label}: {' '.join(command[1:])}", flush=True)  # Show what is running
        code = runner(command)  # Run it
        if code != 0:  # Stop early: no point running tests if the code doesn't even lint
            print(f"FAILED: {label} (exit code {code})")
            return code  # Propagate the failing tool's exit code
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_checks())
