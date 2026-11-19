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
