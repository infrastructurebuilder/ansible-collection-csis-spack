"""shell_environment: the environment some shell lines produce."""

from __future__ import annotations

from typing import Any

from conftest import Spack


def capture(spack: Spack, shell: str, *, check: bool = False, **options: Any) -> dict:
    return spack.module("shell_environment", shell=shell, check=check, **options)


def test_what_the_lines_set_is_returned_and_nothing_else(spack: Spack) -> None:
    result = capture(spack, "export MYCOMPILER_LOADED=1\nexport MYCOMPILER_ROOT=/opt/my\nnot_exported=2")
    assert result["environment"] == {"MYCOMPILER_LOADED": "1", "MYCOMPILER_ROOT": "/opt/my"}
    assert result["changed"] is False


def test_a_changed_variable_is_returned_with_its_new_value(spack: Spack) -> None:
    result = capture(spack, 'export PATH="/opt/my/bin:$PATH"')
    assert list(result["environment"]) == ["PATH"]
    assert result["environment"]["PATH"].startswith("/opt/my/bin:")


def test_a_removed_variable_is_named(spack: Spack) -> None:
    result = spack.module("shell_environment", shell="unset DOOMED", task_env={"DOOMED": "1"})
    assert result["unset"] == ["DOOMED"]
    assert result["environment"] == {}


def test_what_the_lines_print_does_not_get_in_the_way(spack: Spack) -> None:
    result = capture(spack, 'echo \'{"not": "the environment"}\'\nexport A_B=1')
    assert result["environment"] == {"A_B": "1"}


def test_shell_functions_and_the_shells_own_variables_are_left_out(spack: Spack) -> None:
    result = capture(spack, "module() { :; }\nexport -f module\ncd /\nexport KEPT=1")
    assert result["environment"] == {"KEPT": "1"}


def test_it_runs_in_check_mode_too(spack: Spack) -> None:
    assert capture(spack, "export KEPT=1", check=True)["environment"] == {"KEPT": "1"}


def test_a_shell_that_fails_fails_the_task(spack: Spack) -> None:
    result = capture(spack, "export KEPT=1\nexit 3")
    assert result["failed"] is True
    assert "exit 3" in result["msg"]


def test_a_failing_line_does_not_stop_the_rest_unless_the_lines_say_so(spack: Spack) -> None:
    assert capture(spack, "false\nexport KEPT=1")["environment"] == {"KEPT": "1"}
    assert capture(spack, "set -e\nfalse\nexport KEPT=1")["failed"] is True


def test_another_shell_can_be_named(spack: Spack) -> None:
    result = capture(spack, "export KEPT=1", executable="/bin/sh")
    assert result["environment"] == {"KEPT": "1"}
