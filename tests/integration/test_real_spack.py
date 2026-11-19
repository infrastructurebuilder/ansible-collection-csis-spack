"""Both modules against the real Spack v1.2.0, on the local machine (just full-test).

Spack is cloned once into .tmp/spack, and keeps its user configuration and
caches in .tmp/ too, so nothing of the local machine's own Spack is read or
written. Packages are installed with ``--fake``: nothing is compiled. The
first concretization bootstraps Spack's solver and takes a few minutes.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from real_spack import real_spack_env
from runner import run_module

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def spack_env() -> dict[str, str]:
    return real_spack_env()


def test_both_modules_against_the_real_spack(tmp_path: Path, spack_env: dict[str, str]) -> None:
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
    assert before["spack_version"] == "1.2.0"

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
