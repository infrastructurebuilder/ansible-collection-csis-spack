"""spack_command against the stand-in Spack: any command, with a stated way to tell a change."""

from __future__ import annotations

from typing import Any

from conftest import Spack


def command(spack: Spack, args: list[str], changes: str, *, check: bool = False, **options: Any) -> dict:
    return spack.module("spack_command", args=args, changes=changes, check=check, **options)


ADD = ["config", "--scope", "site", "add", "config:build_jobs:4"]


def test_changes_config_reports_a_change_only_when_the_scope_differs(spack: Spack) -> None:
    first = command(spack, ADD, "config")
    assert (first["changed"], first["ran"]) == (True, True)
    assert spack.scope("site", "config") == {"build_jobs": 4}
    second = command(spack, ADD, "config")
    assert (second["changed"], second["ran"]) == (False, True)


def test_changes_config_looks_only_at_the_sections_and_scope_named(spack: Spack) -> None:
    assert command(spack, ADD, "config", sections=["packages"])["changed"] is False
    other = ["config", "--scope", "site", "add", "config:build_jobs:8"]
    assert command(spack, other, "config", scope="user")["changed"] is False


def test_changes_always_and_never(spack: Spack) -> None:
    always = command(spack, ["buildcache", "update-index", "site-cache"], "always")
    assert (always["changed"], always["ran"]) == (True, True)
    assert "ran: buildcache update-index site-cache" in always["stdout"]
    never = command(spack, ["gpg", "list"], "never")
    assert (never["changed"], never["ran"]) == (False, True)


def test_changes_creates_runs_only_while_the_path_is_missing(spack: Spack) -> None:
    made = spack.env.parent / "made"
    first = command(spack, ["gpg", "init"], "creates", creates=str(made))
    assert (first["changed"], first["ran"]) == (True, True)
    made.mkdir()
    second = command(spack, ["gpg", "init"], "creates", creates=str(made))
    assert (second["changed"], second["ran"]) == (False, False)
    assert len(spack.calls("gpg", "init")) == 1


def test_creates_is_required_with_changes_creates(spack: Spack) -> None:
    assert "creates" in command(spack, ["gpg", "init"], "creates")["msg"]


def test_a_command_can_run_in_an_environment(spack: Spack) -> None:
    command(spack, ["concretize", "--force"], "always", env=str(spack.env))
    assert ["-e", str(spack.env), "concretize", "--force"] in spack.state["calls"]


def test_a_failing_command_fails_with_its_output(spack: Spack) -> None:
    spack.update(fail={"gpg": True})
    result = command(spack, ["gpg", "init"], "always")
    assert result["failed"] is True
    assert "gpg init failed on purpose" in result["msg"]


def test_check_mode_does_not_run_and_reports_a_possible_change(spack: Spack) -> None:
    result = command(spack, ADD, "config", check=True)
    assert (result["changed"], result["ran"]) == (True, False)
    assert spack.scope("site", "config") == {}
    assert command(spack, ["gpg", "list"], "never", check=True)["changed"] is False
    made = spack.env.parent / "made"
    made.mkdir()
    assert command(spack, ["gpg", "init"], "creates", creates=str(made), check=True)["changed"] is False
    assert spack.calls("gpg") == []


def helps(spack: Spack) -> list[list[str]]:
    """The help calls the stand-in saw, as the command words each was for."""
    return [call[:-1] for call in spack.calls() if call[-1:] == ["--help"]]


def test_yes_to_all_answers_a_command_whose_help_lists_it(spack: Spack) -> None:
    result = spack.module("spack_command", args=["gc"], changes="always", yes_to_all=True)
    assert result["failed"] is False, result.get("msg")
    assert [call for call in spack.calls("gc") if call[-1] != "--help"] == [["gc", "--yes-to-all"]]
    assert helps(spack) == [["gc"]]


def test_without_yes_to_all_the_command_runs_as_written_and_no_help_is_read(spack: Spack) -> None:
    spack.module("spack_command", args=["gc"], changes="always")
    assert spack.calls("gc") == [["gc"]]
    assert helps(spack) == []


def test_a_command_that_answers_already_is_run_as_written(spack: Spack) -> None:
    spack.module("spack_command", args=["gc", "-y"], changes="always", yes_to_all=True)
    assert spack.calls("gc") == [["gc", "-y"]]
    assert helps(spack) == []


def test_a_command_whose_help_does_not_list_it_is_run_as_written(spack: Spack) -> None:
    spack.module("spack_command", args=["mirror", "list"], changes="never", yes_to_all=True)
    assert [call for call in spack.calls("mirror") if call[-1] != "--help"] == [["mirror", "list"]]
    assert helps(spack) == [["mirror"], ["mirror", "list"]]


def test_in_check_mode_nothing_runs_and_no_help_is_read(spack: Spack) -> None:
    spack.module("spack_command", args=["gc"], changes="always", yes_to_all=True, check=True)
    assert spack.calls("gc") == []
    assert helps(spack) == []
