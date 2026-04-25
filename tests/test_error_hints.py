import pytest
from sandbox.errors import UserError, die


def test_die_writes_to_stderr_and_exits(capsys):
    with pytest.raises(SystemExit) as exc:
        die("base image not built", fix="docker build -t sandbox-template:latest base-image/sandbox-template/")
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "base image not built" in captured.err
    assert "docker build" in captured.err


def test_die_without_fix(capsys):
    with pytest.raises(SystemExit):
        die("plain error")
    captured = capsys.readouterr()
    assert "plain error" in captured.err


def test_user_error_carries_fix():
    e = UserError("port in use", fix="stop the other agent")
    assert e.fix == "stop the other agent"
    assert str(e) == "port in use"
