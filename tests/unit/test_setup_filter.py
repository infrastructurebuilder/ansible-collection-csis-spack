"""The checks made on a spack_setup list before any step runs, and the step labels."""

from __future__ import annotations

from pathlib import Path

import yaml
from ansible_collections.infrastructurebuilder.csis_spack.plugins.filter.setup_problems import (
    COMMON,
    KINDS,
    setup_label,
    setup_problems,
)

ROOT = Path(__file__).resolve().parents[2]
GOOD = [
    {"kind": "environment", "name": "loaded", "shell": "export A=1"},
    {"kind": "config", "settings": {"config": {"build_jobs": 4}}},
    {"kind": "detect", "compilers": True, "environment": "loaded", "require": ["gcc"]},
    {"kind": "detect", "externals": ["git"], "environment": {"A": "1"}},
    {"kind": "mirror", "name": "site-cache", "url": "https://cache.example.org"},
    {"kind": "gpg_key", "from_mirrors": True, "label": "the mirror's keys"},
    {"kind": "command", "args": ["gpg", "init"], "changes": "always"},
]


def test_a_good_list_has_no_problems() -> None:
    assert setup_problems(GOOD) == []
    assert setup_problems([]) == []


def test_the_list_must_be_a_list_of_mappings() -> None:
    assert setup_problems({"kind": "config"}) == ["spack_setup must be a list of steps, not dict"]
    assert setup_problems(["detect"]) == ["step 1 is not a mapping"]


def test_an_unknown_or_missing_kind_is_named_with_the_steps_number() -> None:
    problems = setup_problems([GOOD[1], {"kind": "install"}, {"settings": {}}])
    assert len(problems) == 2
    assert problems[0].startswith("step 2: kind is 'install'; it must be one of command, config, detect")
    assert problems[1].startswith("step 3: kind is None")


def test_an_option_of_another_kind_is_refused() -> None:
    assert setup_problems([{"kind": "detect", "compilers": True, "url": "x"}]) == [
        "step 1 (detect): 'url' is not an option of this kind"
    ]


def test_required_options_are_asked_for() -> None:
    assert setup_problems(
        [{"kind": "config"}, {"kind": "command", "args": ["x"]}, {"kind": "environment"}]
    ) == [
        "step 1 (config): 'settings' is required",
        "step 2 (command): 'changes' is required",
        "step 3 (environment): 'name' is required",
        "step 3 (environment): 'shell' is required",
    ]


def test_an_environment_must_be_captured_before_it_is_named() -> None:
    late = [GOOD[2], GOOD[0]]
    assert setup_problems(late) == ["step 1 (detect): no earlier step captures an environment named 'loaded'"]
    assert setup_problems([GOOD[0], GOOD[0]]) == [
        "step 2 (environment): an earlier step already captures 'loaded'"
    ]
    assert setup_problems([{"kind": "detect", "compilers": True, "environment": 3}]) == [
        "step 1 (detect): environment must be a name or a mapping of variables"
    ]


def test_an_environment_step_cannot_itself_run_in_one() -> None:
    step = {"kind": "environment", "name": "b", "shell": ":", "environment": "a"}
    assert "step 1 (environment): 'environment' is not an option of this kind" in setup_problems([step])


def test_every_problem_is_reported_not_only_the_first() -> None:
    assert len(setup_problems([{"kind": "nope"}, {"kind": "config"}, {"kind": "mirror", "nam": "x"}])) == 4


def test_each_kinds_options_are_its_modules_options() -> None:
    """The table in the filter and the modules' own options cannot drift apart."""
    for kind, spec in KINDS.items():
        source = (ROOT / "plugins" / "modules" / f"{spec['module']}.py").read_text()
        documentation = source.split('DOCUMENTATION = r"""', 1)[1].split('"""', 1)[0]
        options = set(yaml.safe_load(documentation)["options"]) - {"spack"}
        # An environment step's "name" is the role's, not the module's.
        mine = set(spec["required"]) | set(spec["optional"])
        if kind == "environment":
            mine.discard("name")
        assert mine == options, kind
        assert not (mine & set(COMMON)) or kind == "mirror", kind


def test_labels() -> None:
    assert [setup_label(step) for step in GOOD] == [
        "environment: loaded",
        "config: config",
        "detect: compilers",
        "detect: git",
        "mirror: site-cache",
        "the mirror's keys",
        "command: gpg init",
    ]
    assert setup_label({"kind": "config", "state": "absent", "settings": {"packages": {}}}) == (
        "config: remove from packages"
    )
    assert (
        setup_label({"kind": "detect", "compilers": True, "externals": True})
        == "detect: compilers and externals"
    )
    assert setup_label({"kind": "gpg_key", "key": "/k.pub"}) == "gpg_key: /k.pub"
    assert setup_label("nonsense") == "?"


def test_yes_to_all_is_an_option_of_every_kind_that_runs_spack() -> None:
    for kind in ("config", "mirror", "gpg_key", "detect", "command"):
        assert "yes_to_all" in KINDS[kind]["optional"], kind
    problems = setup_problems([{"kind": "environment", "name": "e", "shell": "true", "yes_to_all": True}])
    assert problems == ["step 1 (environment): 'yes_to_all' is not an option of this kind"]
