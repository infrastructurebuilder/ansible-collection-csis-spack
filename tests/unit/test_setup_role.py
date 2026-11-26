"""The setup role against the stand-in Spack: one list of steps, carried out in order."""

from __future__ import annotations

import shlex
from pathlib import Path

import yaml
from conftest import Spack
from runner import ROOT
from spack_source import make_source
from test_spack_detect import MACHINE

STEPS = [
    {"kind": "config", "settings": {"config": {"build_jobs": 4}}},
    {"kind": "environment", "name": "loaded", "shell": "export MYCOMPILER_LOADED=1"},
    {"kind": "detect", "compilers": True, "environment": "loaded", "require": ["mycompiler@12"]},
    {"kind": "detect", "externals": ["mybuildtool"], "not_buildable": True},
    {"kind": "mirror", "name": "site-cache", "url": "https://cache.example.org", "type": ["binary"]},
    {"kind": "gpg_key", "from_mirrors": True},
    {"kind": "command", "args": ["buildcache", "update-index", "site-cache"], "changes": "never"},
]
KEY = "7500481A18F8F903534D953AC6F328B79BE7166C"


def ready(spack: Spack) -> Spack:
    spack.update(machine=MACHINE, mirror_keys={"site-cache": [KEY]})
    return spack


def test_the_roles_defaults_are_empty_and_name_no_site() -> None:
    defaults = yaml.safe_load((ROOT / "roles" / "setup" / "defaults" / "main.yml").read_text())
    assert defaults == {
        "spack_setup": [],
        # Plain `spack`, unless the variable's name before 0.0.1 is set.
        "spack_setup_executable": "{{ spack_setup_spack | default('spack') }}",
        "spack_setup_scope": "site",
        # Off: a confirmation is answered only where a site asks for it.
        "spack_setup_yes_to_all": False,
    }


def test_with_no_steps_the_role_does_nothing(spack: Spack) -> None:
    played = spack.setup([])
    assert (played.rc, played.results) == (0, [])
    assert spack.calls() == []


def test_every_step_is_carried_out_in_the_order_written(spack: Spack) -> None:
    played = ready(spack).setup(STEPS)
    assert played.rc == 0, played.output
    assert [step["kind"] for step in played.results] == [step["kind"] for step in STEPS]
    assert [step["step"] for step in played.results] == list(range(1, len(STEPS) + 1))
    assert played.changed == [True, False, True, True, True, True, False]
    order = [
        call[:2]
        for call in spack.calls()
        if call[0] in ("compiler", "external", "mirror", "buildcache") and call[-1] != "--help"
    ]
    assert order == [
        ["compiler", "find"],
        ["external", "find"],
        ["mirror", "add"],
        ["buildcache", "keys"],
        ["buildcache", "update-index"],
    ]
    assert spack.scope("site", "config") == {"build_jobs": 4}
    assert spack.scope("site", "packages")["mybuildtool"]["buildable"] is False
    assert "mycompiler@12.2.0" in played.results[2]["result"]["added"]
    assert spack.state["trusted"] == [KEY]


def test_a_second_application_changes_nothing(spack: Spack) -> None:
    ready(spack).setup(STEPS)
    again = spack.setup(STEPS)
    assert again.rc == 0, again.output
    assert again.changed == [False] * len(STEPS)
    assert "changed=0" in again.output


def test_the_results_name_each_step(spack: Spack) -> None:
    played = ready(spack).setup(STEPS)
    assert [step["label"] for step in played.results] == [
        "config: config",
        "environment: loaded",
        "detect: compilers",
        "detect: mybuildtool",
        "mirror: site-cache",
        "gpg_key: from the mirrors",
        "command: buildcache update-index site-cache",
    ]
    assert "Declare a mirror | mirror: site-cache" in played.output


def test_a_captured_environment_reaches_only_the_steps_that_name_it(spack: Spack) -> None:
    steps = [
        STEPS[1],
        {"kind": "detect", "compilers": True, "label": "without"},
        {"kind": "detect", "compilers": True, "environment": "loaded", "label": "with"},
    ]
    played = ready(spack).setup(steps)
    assert played.results[1]["result"]["added"] == ["gcc@14.3.1 languages:='c,c++'"]
    assert played.results[2]["result"]["added"] == ["mycompiler@12.2.0"]


def test_a_step_may_give_its_environment_as_a_mapping(spack: Spack) -> None:
    steps = [{"kind": "detect", "compilers": True, "environment": {"MYCOMPILER_LOADED": "1"}}]
    played = ready(spack).setup(steps)
    assert "mycompiler@12.2.0" in played.results[0]["result"]["added"]


def test_a_bad_list_is_refused_before_anything_is_changed(spack: Spack) -> None:
    steps = [STEPS[0], {"kind": "detect", "compilers": True, "url": "x"}, {"kind": "install"}]
    played = ready(spack).setup(steps)
    assert played.rc != 0
    assert "spack_setup cannot be carried out, and nothing was changed" in played.output
    assert "step 2 (detect): 'url' is not an option of this kind" in played.output
    assert "step 3: kind is 'install'" in played.output
    assert spack.calls() == []
    assert spack.state.get("scopes", {}) == {}


def test_a_failing_step_stops_the_rest(spack: Spack) -> None:
    steps = [
        STEPS[0],
        {"kind": "detect", "compilers": True, "require": ["mycompiler@12"]},
        STEPS[4],
    ]
    played = ready(spack).setup(steps)
    assert played.rc != 0
    assert "not registered after detection: mycompiler@12" in played.output
    assert spack.scope("site", "config") == {"build_jobs": 4}
    assert spack.calls("mirror") == []


def elsewhere(spack: Spack, where: Path) -> tuple[Path, Path]:
    """A second way to the stand-in, outside PATH, and the mark it leaves when it is run.

    The stand-in is on PATH in every test, so a role that ignored its variable
    and ran plain ``spack`` would still do the work. Only the mark tells them apart.
    """
    mark = where / "ran-from-elsewhere"
    program = where / "elsewhere" / "spack"
    program.parent.mkdir()
    program.write_text(
        f'#!/bin/sh\ntouch {shlex.quote(str(mark))}\nexec {shlex.quote(str(spack.bin / "spack"))} "$@"\n'
    )
    program.chmod(0o755)
    return program, mark


def test_the_executable_and_the_default_scope_are_the_roles_variables(spack: Spack, tmp_path: Path) -> None:
    program, mark = elsewhere(spack, tmp_path)
    steps = [STEPS[0], {"kind": "config", "scope": "site", "settings": {"config": {"build_jobs": 8}}}]
    played = spack.setup(steps, spack_setup_scope="user", spack_setup_executable=str(program))
    assert played.rc == 0, played.output
    assert mark.exists(), "the role did not run the executable it was given"
    assert spack.scope("user", "config") == {"build_jobs": 4}
    assert spack.scope("site", "config") == {"build_jobs": 8}


def test_without_the_variable_the_role_runs_spack_from_the_path(spack: Spack, tmp_path: Path) -> None:
    mark = elsewhere(spack, tmp_path)[1]
    played = spack.setup([STEPS[0]])
    assert played.rc == 0, played.output
    assert not mark.exists()
    assert spack.scope("site", "config") == {"build_jobs": 4}


def test_the_executables_name_before_0_0_1_still_works(spack: Spack, tmp_path: Path) -> None:
    program, mark = elsewhere(spack, tmp_path)
    played = spack.setup([STEPS[0]], spack_setup_spack=str(program))
    assert played.rc == 0, played.output
    assert mark.exists(), "the role ignored spack_setup_spack"


def test_given_both_names_the_role_runs_the_new_one(spack: Spack, tmp_path: Path) -> None:
    program, mark = elsewhere(spack, tmp_path)
    played = spack.setup(
        [STEPS[0]],
        spack_setup_executable=str(program),
        spack_setup_spack=str(tmp_path / "there-is-no-spack-here"),
    )
    assert played.rc == 0, played.output
    assert mark.exists(), "the role did not run spack_setup_executable"


def test_check_mode_previews_what_is_declared_and_runs_no_discovery(spack: Spack) -> None:
    played = ready(spack).setup(STEPS, check=True)
    assert played.rc == 0, played.output
    assert played.changed == [True, False, False, False, True, False, False]
    assert played.results[2]["result"]["previewed"] is False
    assert spack.state.get("scopes", {}) == {}
    assert spack.calls("compiler") == []
    assert spack.calls("mirror", "add") == []


def gc_calls(spack: Spack) -> list[list[str]]:
    return [call for call in spack.calls("gc") if call[-1] != "--help"]


def test_the_roles_yes_to_all_answers_every_step(spack: Spack) -> None:
    steps = [{"kind": "command", "args": ["gc"], "changes": "always"}]
    played = spack.setup(steps, spack_setup_yes_to_all=True)
    assert played.rc == 0, played.output
    assert gc_calls(spack) == [["gc", "--yes-to-all"]]


def test_a_steps_own_yes_to_all_overrides_the_roles(spack: Spack) -> None:
    off = [{"kind": "command", "args": ["gc"], "changes": "always", "yes_to_all": False}]
    assert spack.setup(off, spack_setup_yes_to_all=True).rc == 0
    on = [{"kind": "command", "args": ["gc"], "changes": "always", "yes_to_all": True}]
    assert spack.setup(on).rc == 0
    assert gc_calls(spack) == [["gc"], ["gc", "--yes-to-all"]]


# The spack step (spec 004): Spack installed by the first step, and run by the rest.
NOT_PREVIEWED = "Spack is not installed yet: check mode does not install it, so this step cannot be previewed"


def installed_by_the_role(spack: Spack, where: Path) -> tuple[dict, Path, Path]:
    """A spack step whose source's bin/spack runs the stand-in and leaves a mark; its path and mark."""
    mark = where / "ran-the-installed-spack"
    url, _ = make_source(where, runs=spack.bin / "spack", mark=mark)
    path = where / "opt" / "spack"
    return {"kind": "spack", "version": "v1.2.0", "path": str(path), "source": url}, path, mark


def test_the_steps_after_a_spack_step_run_the_spack_it_installed(spack: Spack, tmp_path: Path) -> None:
    step, path, mark = installed_by_the_role(spack, tmp_path)
    played = spack.setup([step, STEPS[0]])
    assert played.rc == 0, played.output
    assert played.changed == [True, True]
    assert (path / "bin" / "spack").is_file()
    assert mark.exists(), "the config step did not run the Spack the spack step installed"
    assert spack.scope("site", "config") == {"build_jobs": 4}
    assert played.results[0]["result"]["spack"] == str(path / "bin" / "spack")

    again = spack.setup([step, STEPS[0]])
    assert again.rc == 0, again.output
    assert again.changed == [False, False]


def test_in_check_mode_the_steps_after_an_install_are_not_previewed(spack: Spack, tmp_path: Path) -> None:
    step, path, _ = installed_by_the_role(spack, tmp_path)
    played = spack.setup([step, STEPS[0]], check=True)
    assert played.rc == 0, played.output
    assert played.changed == [True, False]
    later = played.results[1]["result"]
    assert later["previewed"] is False
    assert later["msg"] == NOT_PREVIEWED
    assert not path.exists()
    assert spack.calls("config") == []


def test_a_spack_setup_executable_that_disagrees_with_the_spack_step_is_refused(
    spack: Spack, tmp_path: Path
) -> None:
    step, path, _ = installed_by_the_role(spack, tmp_path)
    played = spack.setup([step, STEPS[0]], spack_setup_executable="/usr/bin/spack")
    assert played.rc != 0
    assert "/usr/bin/spack" in played.output
    assert str(path / "bin" / "spack") in played.output
    assert played.results == []
    assert not path.exists()
