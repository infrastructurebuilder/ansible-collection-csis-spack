"""The configurations under docs/examples: each can be carried out, and does what it says.

They are data, not behaviour of the collection: the differences between one
kind of site and another are all in the lists.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml
from ansible_collections.infrastructurebuilder.csis_spack.plugins.filter.setup_problems import setup_problems
from conftest import FAKE, Spack
from runner import ROOT
from spack_source import make_source

EXAMPLES = sorted((ROOT / "docs" / "examples").glob("*.yml"))
KEY = "7500481A18F8F903534D953AC6F328B79BE7166C"


def load(name: str) -> dict[str, Any]:
    return yaml.safe_load((ROOT / "docs" / "examples" / name).read_text())


def lists(example: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """The lists of steps in an example: its variables named spack_setup, or spack_setup_<when>."""
    return {
        name: value
        for name, value in example.items()
        if name.startswith("spack_setup") and isinstance(value, list)
    }


def registered(spack: Spack, scope: str = "site") -> list[str]:
    return sorted(
        external["spec"]
        for entry in spack.scope(scope, "packages").values()
        for external in entry.get("externals", [])
    )


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda path: path.stem)
def test_every_example_is_a_list_that_can_be_carried_out(path: Path) -> None:
    found = lists(yaml.safe_load(path.read_text()))
    assert found, "no spack_setup list in the example"
    for name, steps in found.items():
        assert setup_problems(steps) == [], name


def test_there_is_an_example_for_each_situation_the_plan_names() -> None:
    assert [path.stem for path in EXAMPLES] == [
        "cloud-sandbox",
        "compiler-built-by-spack",
        "compiler-in-environment-modules",
        "compiler-toolset",
        "site-mirror-with-key",
        "spack-installed-by-the-role",
        "system-compiler",
        "unwanted-compilers",
    ]


def test_the_systems_compiler(spack: Spack) -> None:
    spack.update(
        machine={
            "compilers": [{"package": "gcc", "spec": "gcc@14.3.1"}],
            "externals": [{"package": "git", "spec": "git@2.47"}],
        },
        mirror_keys={"public-cache": [KEY]},
    )
    steps = load("system-compiler.yml")["spack_setup"]
    first = spack.setup(steps)
    assert first.rc == 0, first.output
    assert first.changed == [True, True, True, True]
    assert registered(spack) == ["gcc@14.3.1", "git@2.47"]
    assert spack.setup(steps).changed == [False, False, False, False]


def test_a_compiler_behind_environment_modules(spack: Spack) -> None:
    spack.update(
        machine={
            "compilers": [
                {"package": "gcc", "spec": "gcc@14.3.1"},
                {"package": "mycompiler", "spec": "mycompiler@12.2.0", "needs": "MYCOMPILER_LOADED"},
            ]
        }
    )
    steps = load("compiler-in-environment-modules.yml")["spack_setup"]
    # The example's shell lines load modules this machine does not have; what
    # they stand for here is that the compiler becomes visible.
    steps[0]["shell"] = "export MYCOMPILER_LOADED=1"
    played = spack.setup(steps)
    assert played.rc == 0, played.output
    assert "mycompiler@12.2.0" in registered(spack)
    packages = spack.scope("site", "packages")
    assert packages["mympi"]["buildable"] is False
    assert packages["all"]["providers"] == {"mpi": ["mympi"]}
    assert spack.setup(steps).changed == [False, False, False]


def test_a_compiler_built_by_spack(spack: Spack) -> None:
    prefix = "/opt/spack/opt/mycompiler-12.2.0"
    spack.update(
        machine={
            "compilers": [
                {"package": "gcc", "spec": "gcc@14.3.1"},
                {"package": "mycompiler", "spec": "mycompiler@12.2.0", "path": prefix},
            ]
        }
    )
    example = load("compiler-built-by-spack.yml")
    before = spack.setup(example["spack_setup_before"])
    assert before.rc == 0, before.output
    assert registered(spack) == ["gcc@14.3.1"]
    after = spack.setup(example["spack_setup_after"], mycompiler_prefix=prefix)
    assert after.rc == 0, after.output
    assert registered(spack) == ["gcc@14.3.1", "mycompiler@12.2.0"]


def test_a_toolset_beside_the_systems_compiler(spack: Spack) -> None:
    spack.update(
        machine={
            "compilers": [
                {"package": "gcc", "spec": "gcc@14.3.1"},
                {"package": "gcc", "spec": "gcc@15.1.0", "path": "/opt/toolset/usr"},
            ]
        }
    )
    played = spack.setup(load("compiler-toolset.yml")["spack_setup"])
    assert played.rc == 0, played.output
    assert registered(spack) == ["gcc@14.3.1", "gcc@15.1.0"]
    assert played.results[1]["label"] == "the toolset's compiler"


def test_compilers_that_are_not_wanted(spack: Spack) -> None:
    spack.update(
        machine={
            "compilers": [
                {"package": "gcc", "spec": "gcc@14.3.1"},
                {"package": "oldcompiler", "spec": "oldcompiler@4.8.5"},
            ]
        }
    )
    steps = load("unwanted-compilers.yml")["spack_setup"]
    played = spack.setup(steps)
    assert played.rc == 0, played.output
    assert registered(spack) == ["gcc@14.3.1"]
    # Detection finds it again and the next step removes it again: such a list
    # is never "nothing changed", as the example itself says.
    assert spack.setup(steps).changed == [True, True]


def test_a_site_mirror_with_its_key(spack: Spack) -> None:
    steps = load("site-mirror-with-key.yml")["spack_setup"]
    key = spack.env.parent / "mirror.pub"
    key.write_text(f"FAKE-PUBLIC-KEY {steps[0]['fingerprint']}\n")
    steps[0]["key"] = str(key)  # the example fetches it from a URL
    played = spack.setup(steps)
    assert played.rc == 0, played.output
    assert played.changed == [True, True, False]
    assert spack.state["trusted"] == [KEY]
    assert spack.scope("site", "mirrors")["site-cache"]["signed"] is True
    assert spack.setup(steps).changed == [False, False, False]


# --- The Cloud Sandbox's two scripts ---------------------------------------

SANDBOX_MACHINE = {
    "compilers": [
        {"package": "gcc", "spec": "gcc@14.3.1"},
        {"package": "llvm", "spec": "llvm@19.1.7"},
        {
            "package": "intel-oneapi-compilers",
            "spec": "intel-oneapi-compilers@2024.2.1",
            "needs": "INTEL_LOADED",
        },
    ],
    "externals": [
        {"package": "git", "spec": "git@2.47"},
        {"package": "cmake", "spec": "cmake@3.31.8"},
    ],
}

# What the sandbox's shell runs, in its order: roles/spack/tasks/main.yml
# L102-L111, then the three Spack tasks of roles/intel_oneapi. The heredoc
# that appends the two externals to site/packages.yaml is written as the
# "config add -f" that has the same effect.
# "buildcache keys" has --yes-to-all, as the sandbox now runs it: Spack 1.2
# asks before trusting each key, and the stand-in follows it (spec 003).
SCRIPT_BASE = [
    ["config", "add", "config:install_tree:padded_length:73"],
    ["config", "add", "modules:default:enable:[tcl]"],
    ["compiler", "find", "--scope", "site"],
    ["external", "find", "--scope", "site"],
    ["external", "find", "--not-buildable", "--scope", "site", "cmake"],
    ["mirror", "add", "--scope", "site", "spack-public", "https://cache.spack.io"],
    ["buildcache", "keys", "--install", "--trust", "--yes-to-all"],
]
SCRIPT_INTEL = [
    ["compiler", "find", "--scope", "site"],
    "externals",
    *[
        ["config", "--scope", "site", "add", f"packages:all:providers:{virtual}:[{provider}]"]
        for virtual, provider in [
            ("mkl", "intel-oneapi-mkl"),
            ("blas", "intel-oneapi-mkl"),
            ("lapack", "intel-oneapi-mkl"),
            ("scalapack", "intel-oneapi-mkl"),
            ("mpi", "intel-oneapi-mpi"),
        ]
    ],
    ["buildcache", "keys", "--install", "--trust", "--yes-to-all"],
]
SCRIPT_EXTERNALS = {
    "packages": {
        "intel-oneapi-mkl": {
            "externals": [{"spec": "intel-oneapi-mkl@2024.2", "prefix": "/opt/intel/oneapi"}],
            "buildable": False,
        },
        "intel-oneapi-mpi": {
            "externals": [{"spec": "intel-oneapi-mpi@2021.13", "prefix": "/opt/intel/oneapi"}],
            "buildable": False,
        },
    }
}


def run_script(state_file: Path, commands: list, extra_env: dict[str, str], scratch: Path) -> None:
    """Run the sandbox's Spack commands, as its shell does, against a stand-in of their own."""
    env = os.environ | {"FAKE_SPACK_STATE": str(state_file)} | extra_env
    for command in commands:
        if command == "externals":
            file = scratch / "externals.json"
            file.write_text(json.dumps(SCRIPT_EXTERNALS))
            command = ["config", "--scope", "site", "add", "-f", str(file)]
        subprocess.run([sys.executable, str(FAKE), *command], env=env, check=True, capture_output=True)


def detections(calls: list[list[str]]) -> list[list[str]]:
    return [call for call in calls if call[0] in ("compiler", "external")]


def test_the_sandbox_example_leaves_spack_as_the_sandboxes_shell_does(spack: Spack, tmp_path: Path) -> None:
    keys = {"spack-public": [KEY]}
    spack.update(machine=SANDBOX_MACHINE, mirror_keys=keys)
    example = load("cloud-sandbox.yml")
    assert example["spack_setup_scope"] == "site"
    intel = example["spack_setup_intel"]
    intel[0]["shell"] = "export INTEL_LOADED=1"  # stands for loading the five modules

    by_shell = tmp_path / "by-shell.json"
    by_shell.write_text(json.dumps({"machine": SANDBOX_MACHINE, "mirror_keys": keys, "calls": []}))
    run_script(by_shell, SCRIPT_BASE, {}, tmp_path)
    base = spack.setup(example["spack_setup_base"])
    assert base.rc == 0, base.output
    halfway = json.loads(by_shell.read_text())
    assert spack.state["scopes"] == halfway["scopes"]

    run_script(by_shell, SCRIPT_INTEL, {"INTEL_LOADED": "1"}, tmp_path)
    second = spack.setup(intel)
    assert second.rc == 0, second.output
    theirs, ours = json.loads(by_shell.read_text()), spack.state
    assert ours["scopes"] == theirs["scopes"]
    assert ours["trusted"] == theirs["trusted"]
    # The discovery commands, which depend on order, in the script's order.
    # (Spack takes the options of "external find" in either order.)
    assert [sorted(call) for call in detections(spack.calls())] == [
        sorted(call) for call in detections(theirs["calls"])
    ]
    # The two settings the script adds without --scope are in the user scope.
    assert ours["scopes"]["user"]["config"] == {"install_tree": {"padded_length": 73}}
    assert "intel-oneapi-compilers@2024.2.1" in registered(spack)

    again = spack.setup(example["spack_setup_base"]).changed + spack.setup(intel).changed
    assert not any(again)


def test_without_its_environment_the_sandboxes_second_list_fails_loudly(spack: Spack) -> None:
    spack.update(machine=SANDBOX_MACHINE)
    intel = load("cloud-sandbox.yml")["spack_setup_intel"]
    intel[0]["shell"] = ":"  # the modules were not loaded
    played = spack.setup(intel)
    assert played.rc != 0
    assert "not registered after detection: intel-oneapi-compilers@2024.2.1" in played.output


def test_spack_installed_by_the_role(spack: Spack, tmp_path: Path) -> None:
    steps = load("spack-installed-by-the-role.yml")["spack_setup"]
    # The unit tests have no network, and may not write to /opt: the example's
    # spack step is given a source and a path of the test's own.
    mark = tmp_path / "ran-the-installed-spack"
    url, _ = make_source(tmp_path, runs=spack.bin / "spack", mark=mark)
    path = tmp_path / "opt" / "spack"
    assert steps[0]["kind"] == "spack" and "source" not in steps[0]
    steps[0] = steps[0] | {"source": url, "path": str(path)}
    played = spack.setup(steps)
    assert played.rc == 0, played.output
    assert played.changed == [True, True, True]
    assert mark.exists(), "the later steps did not run the Spack the example installs"
    assert spack.scope("site", "config") == {"build_jobs": 8}
    assert spack.setup(steps).changed == [False, False, False]
