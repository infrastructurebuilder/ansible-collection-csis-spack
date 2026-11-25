"""spack_detect against the stand-in Spack: discovery of compilers and externals."""

from __future__ import annotations

from typing import Any

from conftest import Spack

# A machine with a system compiler, one that is only seen with its environment
# loaded, one that is only found where it is looked for, and three tools.
MACHINE = {
    "compilers": [
        {"package": "gcc", "spec": "gcc@14.3.1 languages:='c,c++'"},
        {"package": "mycompiler", "spec": "mycompiler@12.2.0", "needs": "MYCOMPILER_LOADED"},
        {"package": "gcc", "spec": "gcc@15.1.0", "path": "/opt/toolset/usr"},
    ],
    "externals": [
        {"package": "git", "spec": "git@2.47"},
        {"package": "perl", "spec": "perl@5.40"},
        {"package": "mybuildtool", "spec": "mybuildtool@3.30", "default": False},
    ],
}
LOADED = {"MYCOMPILER_LOADED": "1"}


def detect(spack: Spack, *, check: bool = False, task_env: dict | None = None, **options: Any) -> dict:
    if "machine" not in spack.state:
        spack.update(machine=MACHINE)
    return spack.module("spack_detect", check=check, task_env=task_env, **options)


def registered(spack: Spack, scope: str = "site") -> list[str]:
    return sorted(
        external["spec"]
        for entry in spack.scope(scope, "packages").values()
        for external in entry.get("externals", [])
    )


def test_compilers_on_the_path_are_recorded_in_the_site_scope(spack: Spack) -> None:
    result = detect(spack, compilers=True)
    assert result["changed"] is True
    assert result["added"] == ["gcc@14.3.1 languages:='c,c++'"]
    assert result["removed"] == []
    assert spack.calls("compiler", "find") == [["compiler", "find", "--scope", "site"]]
    assert spack.calls("external", "find") == []


def test_a_second_run_reports_no_change_though_spack_reorders_the_section(spack: Spack) -> None:
    detect(spack, compilers=True, externals=True)
    again = detect(spack, compilers=True, externals=True)
    assert (again["changed"], again["added"]) == (False, [])
    assert spack.state["detections"] == 4


def test_externals_true_looks_for_spacks_default_set(spack: Spack) -> None:
    result = detect(spack, externals=True)
    assert result["added"] == ["git@2.47", "perl@5.40"]
    assert spack.calls("external", "find") == [["external", "find", "--scope", "site"]]


def test_named_externals_and_not_buildable(spack: Spack) -> None:
    result = detect(spack, externals=["mybuildtool"], not_buildable=True)
    assert result["added"] == ["mybuildtool@3.30"]
    assert spack.scope("site", "packages")["mybuildtool"]["buildable"] is False
    assert spack.calls("external", "find") == [
        ["external", "find", "--scope", "site", "--not-buildable", "mybuildtool"]
    ]


def test_exclude_and_paths_reach_spack(spack: Spack) -> None:
    detect(spack, externals=True, exclude=["perl"])
    assert registered(spack) == ["git@2.47"]
    detect(spack, compilers=True, externals=True, paths=["/opt/toolset/usr"])
    assert "gcc@15.1.0" in registered(spack)
    assert spack.calls("compiler", "find")[-1] == ["compiler", "find", "--scope", "site", "/opt/toolset/usr"]
    assert spack.calls("external", "find")[-1] == [
        "external",
        "find",
        "--scope",
        "site",
        "-p",
        "/opt/toolset/usr",
    ]


def test_what_is_only_seen_in_an_environment_is_found_with_it(spack: Spack) -> None:
    assert detect(spack, compilers=True)["added"] == ["gcc@14.3.1 languages:='c,c++'"]
    result = detect(spack, compilers=True, task_env=LOADED)
    assert result["added"] == ["mycompiler@12.2.0"]


def test_require_fails_when_the_environment_was_not_given(spack: Spack) -> None:
    result = detect(spack, compilers=True, require=["mycompiler@12"])
    assert result["failed"] is True
    assert "not registered after detection: mycompiler@12" in result["msg"]
    assert "give the task that environment" in result["msg"]


def test_require_passes_with_the_environment_and_accepts_a_more_exact_version(spack: Spack) -> None:
    result = detect(spack, compilers=True, require=["mycompiler@12", "gcc@14.3.1", "gcc"], task_env=LOADED)
    assert result.get("failed") is False
    assert "mycompiler@12.2.0" in result["added"]


def test_require_is_not_met_by_another_version(spack: Spack) -> None:
    result = detect(spack, compilers=True, require=["gcc@13", "gcc@14.3"])
    assert "not registered after detection: gcc@13." in result["msg"]


def test_require_looks_in_every_scope(spack: Spack) -> None:
    detect(spack, compilers=True, scope="user", task_env=LOADED)
    result = detect(spack, compilers=True, require=["mycompiler"])
    assert result.get("failed") is False
    assert result["changed"] is False


def test_detection_never_removes_what_it_no_longer_sees(spack: Spack) -> None:
    detect(spack, compilers=True, task_env=LOADED)
    result = detect(spack, compilers=True)
    assert (result["changed"], result["removed"]) == (False, [])
    assert "mycompiler@12.2.0" in registered(spack)


def test_check_mode_runs_nothing_and_says_it_cannot_preview(spack: Spack) -> None:
    result = detect(spack, compilers=True, externals=True, require=["mycompiler"], check=True)
    assert (result["changed"], result["previewed"]) == (False, False)
    assert spack.calls("compiler") == []
    assert spack.calls("external") == []


def test_something_must_be_looked_for(spack: Spack) -> None:
    assert "nothing to look for" in detect(spack, compilers=False)["msg"]


def test_externals_takes_true_false_or_names(spack: Spack) -> None:
    assert "externals must be true, false or a list" in detect(spack, externals="some")["msg"]


def helps(spack: Spack) -> list[list[str]]:
    """The help calls the stand-in saw, as the command words each was for."""
    return [call[:-1] for call in spack.calls() if call[-1:] == ["--help"]]


def test_yes_to_all_reads_the_detection_help_and_adds_nothing_it_does_not_list(spack: Spack) -> None:
    result = detect(spack, compilers=True, externals=["cmake"], yes_to_all=True)
    assert result["failed"] is False, result.get("msg")
    assert helps(spack) == [["compiler", "find"], ["external", "find"]]


def test_without_yes_to_all_detection_reads_no_help(spack: Spack) -> None:
    detect(spack, compilers=True, externals=["cmake"])
    assert helps(spack) == []
