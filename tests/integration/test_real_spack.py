"""The modules against the real Spack 1.0.0, 1.1.0 and 1.2.0, on the local machine (just full-test).

Spack is cloned once into .tmp/spack, and keeps its user configuration and
caches in .tmp/ too, so nothing of the local machine's own Spack is read or
written. Packages are installed with ``--fake``: nothing is compiled. The
first concretization bootstraps Spack's solver and takes a few minutes.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from ansible_collections.infrastructurebuilder.csis_spack.plugins.module_utils.spack import Spack
from real_spack import (
    keyring,
    local_scopes,
    on_path,
    publish_keys,
    signing_key,
    spack_env,
    spack_root,
    spack_version,
)
from runner import run_module

pytestmark = pytest.mark.integration
__all__ = ["spack_env", "spack_version"]  # fixtures, each run once per version


def test_both_modules_against_the_real_spack(
    tmp_path: Path, spack_env: dict[str, str], spack_version: str
) -> None:
    env = tmp_path / "env"
    env.mkdir()
    modules = tmp_path / "modules"

    # Its own install tree and module root, so that every run starts from nothing.
    def write_manifest(extra: str = "") -> None:
        (env / "spack.yaml").write_text(
            "spack:\n"
            "  specs: [zlib]\n"
            "  view: false\n"
            "  config:\n"
            f"    install_tree:\n      root: {tmp_path / 'store'}\n"
            "  modules:\n"
            "    default:\n"
            "      enable: [tcl]\n"
            f"      roots:\n        tcl: {modules}\n" + extra
        )

    def module_files() -> dict[str, int]:
        return {
            str(path.relative_to(modules)): path.stat().st_mtime_ns
            for path in modules.rglob("*")
            if path.is_file()
        }

    write_manifest()
    mirror = tmp_path / "mirror"
    build = {"path": str(env), "install_args": ["--fake"], "modules": ["tcl"]}
    push = {"env": str(env), "mirror": str(mirror), "unsigned": True}

    def run(name: str, args: dict, check: bool = False) -> dict:
        result = run_module(name, args, env=spack_env, check=check)
        assert result["failed"] is False, result.get("msg")
        return result

    before = run("spack_env", build, check=True)
    assert before["changed"] is True
    assert before["concretized"] is True
    assert "zlib" in [item["spec"] for item in before["installed"]]
    assert not (env / "spack.lock").exists(), "check mode wrote the environment's lock"
    assert before["spack_version"] == spack_version.lstrip("v")

    first = run("spack_env", build)
    assert first["changed"] is True
    assert first["concretized"] is True
    assert "zlib" in [item["spec"] for item in first["installed"]]
    assert first["modules_refreshed"] == ["tcl"]
    assert first["modules_reason"] == "concretized"
    assert [root["spec"] for root in first["roots"]] == ["zlib"]
    written = module_files()
    assert any("zlib" in name for name in written)

    second = run("spack_env", build)
    assert (second["changed"], second["concretized"], second["installed"], second["modules_refreshed"]) == (
        False,
        False,
        [],
        [],
    )
    assert second["modules_reason"] == "not_needed"
    assert module_files() == written, "a repeat run touched the module files"
    assert run("spack_env", build, check=True)["changed"] is False

    # Asked to, it regenerates every time; Spack's new time in each file is not a change.
    always = run("spack_env", build | {"refresh_modules": "always"})
    assert (always["changed"], always["modules_reason"]) == (False, "always")
    rewritten = module_files()
    assert set(rewritten) == set(written)
    assert rewritten != written
    assert run("spack_env", build)["modules_reason"] == "not_needed"

    # A module file deleted by hand is put back.
    zlib_module = next(modules / name for name in rewritten if "zlib" in name)
    zlib_module.unlink()
    assert run("spack_env", build, check=True)["modules_refreshed"] == ["tcl"]
    repaired = run("spack_env", build)
    assert (repaired["changed"], repaired["modules_reason"]) == (True, "files_changed")
    assert zlib_module.is_file()

    # A change to the modules configuration regenerates, with nothing new to install.
    write_manifest("      tcl:\n        hash_length: 3\n")
    reconfigured = run("spack_env", build)
    assert reconfigured["installed"] == []
    assert reconfigured["modules_reason"] == "config_changed"
    assert reconfigured["modules_refreshed"] == ["tcl"]
    assert set(module_files()) != set(rewritten)
    assert run("spack_env", build)["changed"] is False

    would_push = run("spack_buildcache_push", push, check=True)
    assert would_push["changed"] is True
    assert "zlib" in [item["spec"] for item in would_push["pushed"]]
    assert not mirror.exists(), "check mode pushed"

    pushed = run("spack_buildcache_push", push)
    assert pushed["changed"] is True
    assert {item["hash"] for item in pushed["pushed"]} == {item["hash"] for item in would_push["pushed"]}
    assert list(mirror.glob("v3/manifests/spec/zlib/*.spec.manifest.json"))

    assert run("spack_buildcache_push", push)["changed"] is False
    assert run("spack_buildcache_push", push, check=True)["changed"] is False

    # force=once overwrites each package one time; force=true every time, with a warning.
    once = run("spack_buildcache_push", push | {"force": "once"})
    assert {item["hash"] for item in once["pushed"]} == {item["hash"] for item in pushed["pushed"]}
    assert run("spack_buildcache_push", push | {"force": "once"})["changed"] is False
    forced = run("spack_buildcache_push", push | {"force": True})
    assert {item["hash"] for item in forced["pushed"]} == {item["hash"] for item in pushed["pushed"]}
    assert "force=true overwrites every package" in forced["_stderr"]


def test_the_keys_a_mirror_publishes_are_trusted_with_no_prompt(
    tmp_path: Path, spack_env: dict[str, str], spack_version: str
) -> None:
    """spack_gpg_key from_mirrors against a mirror that publishes keys (spec 003, FR-003).

    Spack 1.2 asks "Trust key: <fingerprint> [y/N]" for every key a mirror
    publishes, trusted already or not; under Ansible the question reads end of
    file, and 0.0.2's module failed here with exit 3.
    """
    env = tmp_path / "env"
    env.mkdir()
    (env / "spack.yaml").write_text(
        "spack:\n  specs: [zlib]\n  view: false\n  config:\n"
        f"    install_tree:\n      root: {tmp_path / 'store'}\n"
    )
    mirror = tmp_path / "mirror"

    def run(name: str, args: dict, env: dict[str, str]) -> dict:
        result = run_module(name, args, env=env)
        assert result["failed"] is False, result.get("msg")
        return result

    run("spack_env", {"path": str(env), "install_args": ["--fake"]}, spack_env)
    with keyring() as signing, keyring() as trusting:
        signer = spack_env | {"SPACK_GNUPGHOME": signing}
        # The mirror is read from a user scope of the test's own: with
        # SPACK_DISABLE_LOCAL_CONFIG, "mirror add" would write to Spack's own
        # site scope in .tmp/spack (research.md, R4).
        local = {name: value for name, value in spack_env.items() if name != "SPACK_DISABLE_LOCAL_CONFIG"}
        truster = local | {
            **local_scopes(tmp_path, spack_version),
            "SPACK_GNUPGHOME": trusting,
        }
        first_key = signing_key(spack_env, signing, "Key A")
        run("spack_buildcache_push", {"env": str(env), "mirror": str(mirror), "key": first_key}, signer)
        publish_keys(spack_env, signing, mirror)
        added = {"name": "signed", "url": f"file://{mirror}", "type": ["binary"], "scope": "user"}
        run("spack_mirror", added, truster)

        first = run("spack_gpg_key", {"from_mirrors": True}, truster)
        assert (first["changed"], first["trusted"]) == (True, [first_key])
        # Spack asks again for a key it trusts; answered, nothing changes.
        again = run("spack_gpg_key", {"from_mirrors": True}, truster)
        assert (again["changed"], again["trusted"]) == (False, [])

        # A mirror that publishes two keys: the one not yet trusted is the change.
        second_key = signing_key(spack_env, signing, "Key B")
        push = {"env": str(env), "mirror": str(mirror), "key": second_key, "force": True}
        run("spack_buildcache_push", push, signer)
        publish_keys(spack_env, signing, mirror)
        both = run("spack_gpg_key", {"from_mirrors": True}, truster)
        assert (both["changed"], both["trusted"]) == (True, [second_key])
        assert run("spack_gpg_key", {"from_mirrors": True}, truster)["changed"] is False


class RealModule:
    """What Spack needs of an AnsibleModule, running the real spack of an environment."""

    def __init__(self, env: dict[str, str]) -> None:
        self.env = env

    def run_command(self, command: list[str]) -> tuple[int, str, str]:
        done = subprocess.run(command, env=os.environ | self.env, capture_output=True, text=True, check=False)
        return done.returncode, done.stdout, done.stderr


def test_the_yes_to_all_help_check_reads_the_real_spacks_help(spack_env: dict[str, str]) -> None:
    """yes_to_all's help check against the real Spack (spec 003, FR-007): the same on 1.0, 1.1 and 1.2."""
    spack = Spack(RealModule(spack_env), on_path(spack_env), yes_to_all=True)
    assert spack.answered(["install", "--fake"], words=1) == ["install", "--yes-to-all", "--fake"]
    assert spack.answered(["mirror", "add", "n", "file:///nowhere"], words=2) == [
        "mirror",
        "add",
        "n",
        "file:///nowhere",
    ]
    # Walked to: module, then tcl, then refresh, whose help lists it.
    assert spack.answered(["module", "tcl", "refresh", "--delete-tree"]) == [
        "module",
        "tcl",
        "refresh",
        "--yes-to-all",
        "--delete-tree",
    ]
    # --scope before the subcommand: only config's own help is read, which does not list it.
    command = ["config", "--scope", "user", "add", "config:build_jobs:2"]
    assert spack.answered(command) == command


def test_checkout_installs_the_real_spack_from_its_clone_then_leaves_it_alone(
    tmp_path: Path, spack_env: dict[str, str], spack_version: str
) -> None:
    """spack_checkout from the local clone of each version (no network: the clone is the source)."""
    source = spack_root(spack_version).as_uri()
    path = tmp_path / "spack"
    args = {"version": spack_version, "path": str(path), "source": source}
    result = run_module("spack_checkout", args, env=spack_env)
    assert result["failed"] is False, result.get("msg")
    assert (result["changed"], result["found"]) == (True, "nothing")
    number = spack_version.removeprefix("v")
    assert result["spack_version"].startswith(f"{number} "), result["spack_version"]
    shown = subprocess.run(
        [str(path / "bin" / "spack"), "--version"], capture_output=True, text=True, check=True
    ).stdout
    assert shown.startswith(f"{number} ")

    again = run_module("spack_checkout", args, env=spack_env)
    assert again["failed"] is False, again.get("msg")
    assert (again["changed"], again["found"]) == (False, "spack")
