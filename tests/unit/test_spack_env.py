"""spack_env against the fake Spack: what it runs, and what it reports."""

from __future__ import annotations

import json
import shutil
from typing import Any

from conftest import CLANG, GMAKE, ONE_PACKAGE, ZLIB, Spack, lock, spec


def test_a_first_run_concretizes_and_installs(spack: Spack) -> None:
    result = spack.module("spack_env", path=str(spack.env))
    assert result["changed"] is True
    assert result["concretized"] is True
    assert sorted(item["spec"] for item in result["installed"]) == ["gmake", "zlib"]
    assert result["roots"] == [{"spec": "zlib", "hash": ZLIB["hash"]}]
    assert result["spack_version"] == "1.2.0"
    assert spack.calls("concretize") == [["concretize", "--force", "-q", "--fresh"]]
    assert spack.calls("install") == [["install"]]


def test_a_second_run_changes_nothing(spack: Spack) -> None:
    spack.module("spack_env", path=str(spack.env))
    again = spack.module("spack_env", path=str(spack.env))
    assert again["changed"] is False
    assert again["concretized"] is False
    assert again["installed"] == []


def test_externals_are_never_reported_as_installed(spack: Spack) -> None:
    result = spack.module("spack_env", path=str(spack.env))
    assert CLANG["hash"] not in [item["hash"] for item in result["installed"]]


def test_a_new_lock_is_a_change_even_with_nothing_to_install(spack: Spack) -> None:
    spack.module("spack_env", path=str(spack.env))
    spack.update(lock=lock(ZLIB, GMAKE, CLANG, roots=["zlib", "gmake"]))
    result = spack.module("spack_env", path=str(spack.env))
    assert result["changed"] is True
    assert result["concretized"] is True
    assert result["installed"] == []


def test_state_concretized_does_not_install(spack: Spack) -> None:
    result = spack.module("spack_env", path=str(spack.env), state="concretized")
    assert result["concretized"] is True
    assert result["installed"] == []
    assert spack.calls("install") == []
    assert "log_file" not in result


def test_fresh_false_leaves_out_fresh(spack: Spack) -> None:
    spack.module("spack_env", path=str(spack.env), fresh=False)
    assert spack.calls("concretize") == [["concretize", "--force", "-q"]]


def test_install_args_are_passed_as_they_are_and_the_log_is_kept(spack: Spack) -> None:
    result = spack.module("spack_env", path=str(spack.env), install_args=["--cache-only", "-j", "8"])
    assert spack.calls("install") == [["install", "--cache-only", "-j", "8"]]
    log = spack.env / "log.install"
    assert result["log_file"] == str(log)
    assert "zlib" in log.read_text()


def test_a_log_file_can_be_named(spack: Spack) -> None:
    elsewhere = spack.env.parent / "build.log"
    result = spack.module("spack_env", path=str(spack.env), log_file=str(elsewhere))
    assert result["log_file"] == str(elsewhere)
    assert elsewhere.is_file()


def test_spack_is_found_on_the_path_by_default(spack: Spack) -> None:
    result = spack.module("spack_env", path=str(spack.env))
    assert result.get("failed") is not True
    assert spack.calls("--version")


def test_module_files_are_regenerated_and_a_change_is_reported_once(spack: Spack) -> None:
    first = spack.module("spack_env", path=str(spack.env), modules=["tcl"])
    assert first["modules_refreshed"] == ["tcl"]
    assert spack.calls("module") == [["module", "tcl", "refresh", "-y", "--delete-tree"]]
    tree = spack.root / "share" / "spack" / "modules"
    assert sorted(path.name for path in tree.iterdir()) == ["gmake-77tetl5", "zlib-u7p436i"]
    again = spack.module("spack_env", path=str(spack.env), modules=["tcl"], refresh_modules="always")
    assert again["modules_refreshed"] == []
    assert again["changed"] is False
    assert len(spack.calls("module")) == 2


def test_module_files_changing_alone_is_a_change(spack: Spack) -> None:
    spack.module("spack_env", path=str(spack.env), modules=["tcl"])
    spack.update(module_text="#%Module1.0\n# changed\n")
    result = spack.module("spack_env", path=str(spack.env), modules=["tcl"], refresh_modules="always")
    assert result["changed"] is True
    assert result["modules_refreshed"] == ["tcl"]
    assert result["modules_reason"] == "always"


TREE = ("share", "spack", "modules")


def built_with_modules(spack: Spack) -> dict:
    """Run once with modules=[tcl]; give the result."""
    return spack.module("spack_env", path=str(spack.env), modules=["tcl"])


def again(spack: Spack, *, check: bool = False, **options: Any) -> dict:
    return spack.module("spack_env", path=str(spack.env), modules=["tcl"], check=check, **options)


def mtimes(spack: Spack) -> dict[str, int]:
    return {path.name: path.stat().st_mtime_ns for path in spack.root.joinpath(*TREE).iterdir()}


def test_by_default_a_repeat_run_does_not_touch_the_module_files(spack: Spack) -> None:
    first = built_with_modules(spack)
    assert first["modules_reason"] == "concretized"
    before = mtimes(spack)
    second = again(spack)
    assert second["modules_reason"] == "not_needed"
    assert (second["changed"], second["modules_refreshed"]) == (False, [])
    assert len(spack.calls("module")) == 1
    assert mtimes(spack) == before


def test_installing_alone_is_a_reason_to_regenerate(spack: Spack) -> None:
    spack.module("spack_env", path=str(spack.env), state="concretized")
    assert built_with_modules(spack)["modules_reason"] == "installed"


def test_the_stamp_records_what_the_module_files_were_made_from(spack: Spack) -> None:
    built_with_modules(spack)
    stamp = json.loads((spack.env / ".spack-env" / "csis_spack.modules.json").read_text())
    assert stamp["version"] == 1
    assert set(stamp) == {"version", "lock", "config", "trees"}
    assert stamp["trees"]["tcl"]["root"] == str(spack.root.joinpath(*TREE))


def test_a_module_file_deleted_by_hand_is_put_back(spack: Spack) -> None:
    built_with_modules(spack)
    spack.root.joinpath(*TREE, "zlib-u7p436i").unlink()
    result = again(spack)
    assert result["modules_reason"] == "files_changed"
    assert (result["changed"], result["modules_refreshed"]) == (True, ["tcl"])
    assert spack.root.joinpath(*TREE, "zlib-u7p436i").is_file()
    assert again(spack)["modules_reason"] == "not_needed"


def test_a_module_file_edited_by_hand_is_put_back(spack: Spack) -> None:
    built_with_modules(spack)
    module = spack.root.joinpath(*TREE, "zlib-u7p436i")
    module.write_text(module.read_text() + "setenv EDITED 1\n")
    result = again(spack)
    assert result["modules_reason"] == "files_changed"
    assert "EDITED" not in module.read_text()


def test_the_time_spack_writes_into_a_module_file_is_not_a_change(spack: Spack) -> None:
    built_with_modules(spack)
    module = spack.root.joinpath(*TREE, "zlib-u7p436i")
    lines = module.read_text().splitlines()
    assert "Module file created by spack" in lines[-1]
    lines[-1] = (
        "## Module file created by spack (https://github.com/spack/spack) on 2001-01-01 00:00:00.000000"
    )
    module.write_text("\n".join(lines) + "\n")
    assert again(spack)["modules_reason"] == "not_needed"


def test_a_changed_modules_configuration_regenerates(spack: Spack) -> None:
    built_with_modules(spack)
    spack.update(modules_config={"suffix": "-new"})
    result = again(spack)
    assert result["modules_reason"] == "config_changed"
    assert result["modules_refreshed"] == ["tcl"]
    assert spack.root.joinpath(*TREE, "zlib-u7p436i-new").is_file()


def test_a_missing_module_root_regenerates(spack: Spack) -> None:
    built_with_modules(spack)
    shutil.rmtree(spack.root.joinpath(*TREE))
    result = again(spack)
    assert result["modules_reason"] == "missing_root"
    assert result["modules_refreshed"] == ["tcl"]


def test_without_its_stamp_the_module_regenerates_and_writes_one(spack: Spack) -> None:
    built_with_modules(spack)
    stamp = spack.env / ".spack-env" / "csis_spack.modules.json"
    stamp.unlink()
    result = again(spack)
    assert result["modules_reason"] == "no_stamp"
    assert (result["changed"], result["modules_refreshed"]) == (False, [])
    assert stamp.is_file()


def test_a_lock_that_changed_behind_the_stamp_regenerates(spack: Spack) -> None:
    built_with_modules(spack)
    stamp = spack.env / ".spack-env" / "csis_spack.modules.json"
    stamp.write_text(json.dumps(json.loads(stamp.read_text()) | {"lock": "0" * 64}))
    assert again(spack)["modules_reason"] == "lock_changed"


def test_a_module_system_the_stamp_does_not_know_regenerates(spack: Spack) -> None:
    built_with_modules(spack)
    (spack.root / "share" / "spack" / "lmod").mkdir()
    result = spack.module("spack_env", path=str(spack.env), modules=["tcl", "lmod"])
    assert result["modules_reason"] == "no_stamp"
    assert result["modules_refreshed"] == ["lmod"]


def test_no_modules_asked_for_says_so(spack: Spack) -> None:
    assert spack.module("spack_env", path=str(spack.env))["modules_reason"] == "not_requested"


def test_check_mode_knows_a_hand_change_will_be_put_right(spack: Spack) -> None:
    built_with_modules(spack)
    spack.root.joinpath(*TREE, "zlib-u7p436i").unlink()
    result = again(spack, check=True)
    assert result["modules_reason"] == "files_changed"
    assert (result["changed"], result["modules_refreshed"]) == (True, ["tcl"])
    assert not spack.root.joinpath(*TREE, "zlib-u7p436i").exists()
    assert len(spack.calls("module")) == 1


def test_check_mode_after_a_run_with_modules_reports_no_change(spack: Spack) -> None:
    built_with_modules(spack)
    result = again(spack, check=True)
    assert (result["changed"], result["modules_reason"]) == (False, "not_needed")


def test_an_unknown_refresh_modules_is_refused(spack: Spack) -> None:
    result = again(spack, refresh_modules="sometimes")
    assert result["failed"] is True
    assert "sometimes" in result["msg"]


def test_a_configured_module_root_is_the_one_watched(spack: Spack) -> None:
    root = spack.env.parent / "modules"
    spack.update(module_roots={"tcl": str(root)})
    result = spack.module("spack_env", path=str(spack.env), modules=["tcl"], delete_tree=False)
    assert result["modules_refreshed"] == ["tcl"]
    assert spack.calls("module") == [["module", "tcl", "refresh", "-y"]]
    assert sorted(path.name for path in root.iterdir()) == ["gmake-77tetl5", "zlib-u7p436i"]


def test_check_mode_says_what_would_change_and_touches_nothing(spack: Spack) -> None:
    result = spack.module("spack_env", path=str(spack.env), modules=["tcl"], check=True)
    assert result["changed"] is True
    assert result["concretized"] is True
    assert sorted(item["spec"] for item in result["installed"]) == ["gmake", "zlib"]
    assert not (spack.env / "spack.lock").exists()
    assert spack.calls("install") == []
    assert spack.calls("module") == []
    assert spack.state["installed"] == []


def test_check_mode_after_a_run_reports_no_change(spack: Spack) -> None:
    spack.module("spack_env", path=str(spack.env))
    result = spack.module("spack_env", path=str(spack.env), check=True)
    assert result["changed"] is False
    assert result["installed"] == []


def test_check_mode_sees_a_new_spec_to_install(spack: Spack) -> None:
    spack.module("spack_env", path=str(spack.env))
    bzip2 = spec("bzip2", "cswnif75ihvlnxagiqxgulyyqfunqn4b")
    spack.update(lock=lock(ZLIB, GMAKE, CLANG, bzip2, roots=["zlib", "bzip2"]))
    result = spack.module("spack_env", path=str(spack.env), check=True)
    assert result["concretized"] is True
    assert result["installed"] == [{"spec": "bzip2", "hash": bzip2["hash"]}]
    assert json.loads((spack.env / "spack.lock").read_text()) == ONE_PACKAGE


def test_a_failed_build_fails_with_the_end_of_its_output(spack: Spack) -> None:
    spack.update(fail={"install": True})
    result = spack.module("spack_env", path=str(spack.env))
    assert result["failed"] is True
    assert "install failed on purpose" in result["msg"]
    assert "exit 1" in result["msg"]


def test_a_directory_without_spack_yaml_is_refused(spack: Spack) -> None:
    (spack.env / "spack.yaml").unlink()
    result = spack.module("spack_env", path=str(spack.env))
    assert result["failed"] is True
    assert "not a Spack environment" in result["msg"]
    assert spack.calls() == []


def test_spack_before_1_0_is_refused(spack: Spack) -> None:
    spack.update(version="0.22.5 (abcdef)")
    result = spack.module("spack_env", path=str(spack.env))
    assert result["failed"] is True
    assert "Spack 0.22.5 is too old" in result["msg"]
    assert spack.calls("concretize") == []


def test_an_unknown_option_is_refused(spack: Spack) -> None:
    result = spack.module("spack_env", path=str(spack.env), modules=["dotkit"])
    assert result["failed"] is True
    assert "dotkit" in result["msg"]


def helps(spack: Spack) -> list[list[str]]:
    """The help calls the stand-in saw, as the command words each was for."""
    return [call[:-1] for call in spack.calls() if call[-1:] == ["--help"]]


def test_yes_to_all_answers_install_and_leaves_the_rest_as_they_are(spack: Spack) -> None:
    spack.update(module_roots={"tcl": str(spack.root / "modules")})
    result = spack.module(
        "spack_env", path=str(spack.env), install_args=["--fake"], modules=["tcl"], yes_to_all=True
    )
    assert result["failed"] is False, result.get("msg")
    assert spack.calls("install") == [["install", "--help"], ["install", "--yes-to-all", "--fake"]]
    assert [call for call in spack.calls("concretize") if call[-1] != "--help"] == [
        ["concretize", "--force", "-q", "--fresh"]
    ]
    # It answers with its own -y already, and is run as before.
    (refresh,) = spack.calls("module", "tcl", "refresh")
    assert refresh[:4] == ["module", "tcl", "refresh", "-y"]
    assert "--yes-to-all" not in refresh


def test_without_yes_to_all_spack_env_runs_what_it_did_and_reads_no_help(spack: Spack) -> None:
    spack.module("spack_env", path=str(spack.env), install_args=["--fake"])
    assert spack.calls("install") == [["install", "--fake"]]
    assert helps(spack) == []


# Spec 006: the preview's copy reads relative include and develop paths where they are.
RELATIVE = """spack:
  specs: [zlib]
  include:
  - ./extra.yaml
  - ../shared.yaml
  - path: ../opt.yaml
    optional: true
  - /abs/x.yaml
  - $env/y.yaml
  - ~/site.yaml
  - path: https://example.org/c.yaml
    sha256: abababababababababababababababababababababababababababababababab
  - git: https://git.example.org/c.git
    branch: main
    paths: [c.yaml]
  develop:
    zlib:
      spec: zlib@=1.3.1
      path: ../zlib-src
    gmake:
      spec: gmake@=4.4.1
      path: /abs/gmake
    cmake:
      spec: cmake@=3.30.0
"""


def test_relative_paths_are_rewritten_in_the_copy_only(spack: Spack) -> None:
    import yaml

    (spack.env / "spack.yaml").write_text(RELATIVE)
    result = spack.module("spack_env", path=str(spack.env), check=True)
    assert result["failed"] is False, result.get("msg")
    above = str(spack.env.parent)
    previewed = yaml.safe_load(spack.state["concretized_manifest"])["spack"]
    assert previewed["include"] == [
        f"{spack.env}/extra.yaml",
        f"{above}/shared.yaml",
        {"path": f"{above}/opt.yaml", "optional": True},
        "/abs/x.yaml",
        "$env/y.yaml",
        "~/site.yaml",
        {
            "path": "https://example.org/c.yaml",
            "sha256": "abababababababababababababababababababababababababababababababab",
        },
        {"git": "https://git.example.org/c.git", "branch": "main", "paths": ["c.yaml"]},
    ]
    assert previewed["develop"]["zlib"]["path"] == f"{above}/zlib-src"
    assert previewed["develop"]["gmake"]["path"] == "/abs/gmake"
    # Spack's default for a develop entry with no path is its name, in the environment's directory.
    assert previewed["develop"]["cmake"] == {"spec": "cmake@=3.30.0", "path": f"{spack.env}/cmake"}
    assert (spack.env / "spack.yaml").read_text() == RELATIVE
    calls = [call[0] for call in spack.state["calls"] if call[:1] in (["python"], ["-e"])]
    assert calls[0] == "python", spack.state["calls"]


def test_relative_paths_are_not_looked_for_where_there_are_none(spack: Spack) -> None:
    result = spack.module("spack_env", path=str(spack.env), check=True)
    assert result["failed"] is False, result.get("msg")
    assert spack.calls("python") == []


def test_relative_paths_are_said_in_the_check_mode_note() -> None:
    """Spec 006, FR-003: the documentation says what a preview reads of relative paths."""
    import yaml
    from runner import ROOT

    source = (ROOT / "plugins" / "modules" / "spack_env.py").read_text()
    documentation = source.split('DOCUMENTATION = r"""', 1)[1].split('"""', 1)[0]
    description = " ".join(" ".join(yaml.safe_load(documentation)["description"]).split())
    assert "are read where they are, also above the environment's directory" in description
    assert "records the same develop paths a real run would" in description
