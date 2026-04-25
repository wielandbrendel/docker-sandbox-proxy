from pathlib import Path
import pytest
from sandbox.commands.check import (
    CheckResult,
    check_env_file,
    check_required_env_vars,
    check_base_image,
    run_checks,
)


def test_check_env_file_missing(tmp_path):
    result = check_env_file(tmp_path / "agent")
    assert result.ok is False
    assert ".env" in result.message
    assert result.fix_hint is not None


def test_check_env_file_present(tmp_path):
    agent = tmp_path / "agent"
    agent.mkdir()
    (agent / ".env").write_text("FOO=bar\n")
    result = check_env_file(agent)
    assert result.ok is True


def test_check_required_env_vars_missing_var():
    env = {"FOO": "x"}
    result = check_required_env_vars(env, required=["FOO", "BAR"])
    assert result.ok is False
    assert "BAR" in result.message


def test_check_required_env_vars_all_present():
    env = {"FOO": "x", "BAR": "y"}
    result = check_required_env_vars(env, required=["FOO", "BAR"])
    assert result.ok is True


def test_run_checks_returns_summary(tmp_path):
    agent = tmp_path / "agent"
    agent.mkdir()
    (agent / ".env").write_text("FOO=bar\n")
    checks = [
        lambda: CheckResult("env file", True, "ok", None),
        lambda: CheckResult("missing thing", False, "not found", "do X"),
    ]
    summary = run_checks(checks)
    assert summary.passed == 1
    assert summary.failed == 1
    assert summary.ok is False
