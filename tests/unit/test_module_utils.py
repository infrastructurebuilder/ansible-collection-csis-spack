"""The helpers in plugins/module_utils/spack.py that read Spack's output."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from ansible_collections.infrastructurebuilder.csis_spack.plugins.module_utils.spack import (
    Configuration,
    Spack,
    SpackError,
    behaviour,
    data_digest,
    external_specs,
    file_digest,
    fingerprints,
    listed_fingerprints,
    lock_specs,
    merged,
    mirror_record,
    mirror_url,
    module_tree_digest,
    nest,
    parse_mirror_list,
    parse_version,
    path_text,
    plan_absent,
    plan_merge,
    plan_replace,
    read_state,
    satisfies,
    tree_digest,
    without,
    write_state,
)
from conftest import Spack as StandIn


def test_versions_are_read_from_spack_version() -> None:
    assert parse_version("1.2.0 (63962ed90680d339004305075da272ae93c04a41)") == (1, 2, 0)
    assert parse_version("0.22.5") == (0, 22, 5)
    assert parse_version("1.1") == (1, 1, 0)
    with pytest.raises(SpackError):
        parse_version("not a version")


def test_mirror_list_is_read_as_spack_v1_2_prints_it() -> None:
    output = "localm       [sb] file:///tmp/mirror\nspack-public [s ] https://mirror.spack.io\n"
    assert parse_mirror_list(output) == {
        "localm": "file:///tmp/mirror",
        "spack-public": "https://mirror.spack.io",
    }


def test_a_mirror_is_a_url_a_path_or_a_name() -> None:
    known = {"s3-mirror": "s3://bucket/spack"}
    assert mirror_url("s3://other/x", known) == "s3://other/x"
    assert mirror_url("/srv/mirror", known) == "file:///srv/mirror"
    assert mirror_url("s3-mirror", known) == "s3://bucket/spack"
    with pytest.raises(SpackError, match="no mirror named 'nope'"):
        mirror_url("nope", known)


def test_a_missing_lock_has_no_specs(tmp_path: Path) -> None:
    assert lock_specs(str(tmp_path)) == ({}, [])


def test_a_lock_gives_its_specs_and_roots(tmp_path: Path) -> None:
    (tmp_path / "spack.lock").write_text(
        json.dumps({"roots": [{"spec": "zlib", "hash": "aaa"}], "concrete_specs": {"aaa": {"name": "zlib"}}})
    )
    assert lock_specs(str(tmp_path)) == ({"aaa": {"name": "zlib"}}, [{"spec": "zlib", "hash": "aaa"}])


def test_digests_see_contents_and_names(tmp_path: Path) -> None:
    assert file_digest(str(tmp_path / "absent")) is None
    assert tree_digest(str(tmp_path / "absent")) is None
    (tmp_path / "a").write_text("one")
    first = tree_digest(str(tmp_path))
    (tmp_path / "a").write_text("two")
    second = tree_digest(str(tmp_path))
    (tmp_path / "a").rename(tmp_path / "b")
    third = tree_digest(str(tmp_path))
    assert len({first, second, third}) == 3


def test_a_module_tree_digest_leaves_out_when_spack_wrote_each_file(tmp_path: Path) -> None:
    header = "#%Module1.0\n## Module file created by spack (https://github.com/spack/spack) on {}\n"
    module = tmp_path / "zlib-u7p436i"
    module.write_text(header.format("2026-11-13 11:00:30.218360") + "prepend-path PATH /a\n")
    first, plain = module_tree_digest(str(tmp_path)), tree_digest(str(tmp_path))
    module.write_text(header.format("2026-11-13 11:00:33.130380") + "prepend-path PATH /a\n")
    assert module_tree_digest(str(tmp_path)) == first
    assert tree_digest(str(tmp_path)) != plain
    module.write_text(header.format("2026-11-13 11:00:33.130380") + "prepend-path PATH /b\n")
    assert module_tree_digest(str(tmp_path)) != first


def test_a_data_digest_does_not_depend_on_the_order_of_keys() -> None:
    assert data_digest({"a": 1, "b": [1, 2]}) == data_digest({"b": [1, 2], "a": 1})
    assert data_digest({"a": 1}) != data_digest({"a": 2})


def test_state_is_kept_in_the_environments_spack_env_directory(tmp_path: Path) -> None:
    assert read_state(str(tmp_path), "x.json") is None
    write_state(str(tmp_path), "x.json", {"version": 1})
    assert json.loads((tmp_path / ".spack-env" / "x.json").read_text()) == {"version": 1}
    assert read_state(str(tmp_path), "x.json") == {"version": 1}
    assert not list((tmp_path / ".spack-env").glob("*.tmp"))


def test_state_that_cannot_be_read_counts_as_none(tmp_path: Path) -> None:
    (tmp_path / ".spack-env").mkdir()
    (tmp_path / ".spack-env" / "x.json").write_text("{ not json")
    assert read_state(str(tmp_path), "x.json") is None
    (tmp_path / ".spack-env" / "x.json").write_text("[1, 2]")
    assert read_state(str(tmp_path), "x.json") is None


# --- Planning changes to a configuration section ---------------------------

CURRENT = {
    "all": {"providers": {"mpi": ["a"], "blas": ["b"]}},
    "tool": {"externals": [{"spec": "tool@1", "prefix": "/usr"}], "buildable": False},
}


def test_a_merge_plan_touches_only_what_differs() -> None:
    assert plan_merge(CURRENT, CURRENT) == ([], [])
    removes, adds = plan_merge(CURRENT, {"all": {"providers": {"mpi": ["c"], "lapack": ["b"]}}})
    assert removes == [["all", "providers", "mpi"]]
    assert adds == [(["all", "providers", "mpi"], ["c"]), (["all", "providers", "lapack"], ["b"])]


def test_a_merge_plan_adds_a_new_subtree_whole_and_removes_nothing_for_it() -> None:
    assert plan_merge(CURRENT, {"new": {"buildable": False}}) == ([], [(["new"], {"buildable": False})])


def test_a_merge_plan_replaces_a_value_whose_kind_changed() -> None:
    removes, adds = plan_merge({"a": 1}, {"a": {"b": 2}})
    assert (removes, adds) == ([["a"]], [(["a"], {"b": 2})])


def test_merged_lays_one_mapping_over_another() -> None:
    assert merged(CURRENT, {"all": {"providers": {"mpi": ["c"]}}})["all"]["providers"] == {
        "mpi": ["c"],
        "blas": ["b"],
    }
    assert merged({"a": [1, 2]}, {"a": [3]}) == {"a": [3]}


def test_a_replace_plan_makes_the_section_exactly_what_is_given() -> None:
    removes, adds = plan_replace(CURRENT, {"tool": CURRENT["tool"], "other": {"buildable": True}})
    assert removes == [["all"]]
    assert adds == [(["other"], {"buildable": True})]
    assert plan_replace(CURRENT, CURRENT) == ([], [])


def test_an_absent_plan_removes_only_what_is_there() -> None:
    unwanted = {"tool": None, "all": {"providers": {"blas": None, "nothere": None}}, "gone": None}
    assert plan_absent(CURRENT, unwanted) == [["tool"], ["all", "providers", "blas"]]


def test_without_takes_an_emptied_mapping_away_too() -> None:
    assert without({"a": {"b": {"c": 1}}, "d": 2}, ["a", "b", "c"]) == {"d": 2}
    assert without({"a": {"b": 1, "c": 2}}, ["a", "b"]) == {"a": {"c": 2}}
    assert without({"a": 1}, ["x", "y"]) == {"a": 1}


def test_paths_and_nesting() -> None:
    assert path_text(["packages", "all", "providers"]) == "packages:all:providers"
    assert nest(["a", "b"], 1) == {"a": {"b": 1}}
    with pytest.raises(SpackError, match="cannot contain a colon"):
        path_text(["a:b"])


def test_external_specs_are_read_from_a_packages_section() -> None:
    assert external_specs(CURRENT) == ["tool@1"]
    assert external_specs({}) == []


def test_a_recorded_spec_satisfies_its_package_and_a_version_no_more_exact() -> None:
    recorded = "gcc@14.3.1 languages:='c,c++'"
    for required in ["gcc", "gcc@14", "gcc@14.3", "gcc@14.3.1"]:
        assert satisfies(recorded, required), required
    for required in ["gcc@13", "gcc@14.3.10", "gcc@1", "llvm", "gcc-runtime"]:
        assert not satisfies(recorded, required), required
    assert satisfies("llvm@19.1.7+clang~flang", "llvm@19.1")


def test_fingerprints_are_read_as_spack_v1_2_prints_them() -> None:
    printed = (
        "==> Trusted keys\n"
        "pub:-:2048:1:F2D4DFC4FD63F7FB:1794662002:::-:::cs::::::23::0:\n"
        "fpr:::::::::E0C894426081BF7A184E2AC8F2D4DFC4FD63F7FB:\n"
        "uid:-::::1794662002::2A02::Test Mirror <test@example.invalid>::::::::::0:pub:-:2048:1:C6F3:1:::-:\n"
        "fpr:::::::::7500481A18F8F903534D953AC6F328B79BE7166C:\n"
    )
    assert fingerprints(printed) == [
        "7500481A18F8F903534D953AC6F328B79BE7166C",
        "E0C894426081BF7A184E2AC8F2D4DFC4FD63F7FB",
    ]
    assert fingerprints("==> Trusted keys\n") == []


def test_a_mirror_kept_as_a_bare_url_is_read_as_a_mapping() -> None:
    assert mirror_record("https://x") == {"url": "https://x"}
    assert mirror_record({"url": "https://x", "signed": True}) == {"url": "https://x", "signed": True}
    assert mirror_record(None) == {}


def test_an_absent_plan_removes_the_highest_mapping_it_would_empty() -> None:
    current = {"install_tree": {"padded_length": 73}, "build_jobs": 4, "a": {"b": {"c": 1}}}
    assert plan_absent(current, {"install_tree": {"padded_length": None}}) == [["install_tree"]]
    assert plan_absent(current, {"a": {"b": {"c": None}}}) == [["a"]]
    assert plan_absent(
        current, {"build_jobs": None, "install_tree": {"padded_length": None}}, ["config"]
    ) == [
        ["config", "build_jobs"],
        ["config", "install_tree"],
    ]
    partly = {"providers": {"mpi": ["x"], "blas": ["y"]}}
    assert plan_absent(partly, {"providers": {"mpi": None}}) == [["providers", "mpi"]]
    assert plan_absent(partly, {"providers": {"mpi": None, "blas": None}}) == [["providers"]]


# --- Answering Spack's confirmations: Spack.answered() ------------------------
#
# Against the stand-in spack, whose help texts are the real Spack's
# (fake_spack_help.json), through a module object that runs it as
# AnsibleModule.run_command would.


class StandInModule:
    """What Spack needs of an AnsibleModule: run_command, with the stand-in's environment."""

    def __init__(self, environ: dict[str, str]) -> None:
        self.environ = environ

    def run_command(self, command: list[str]) -> tuple[int, str, str]:
        done = subprocess.run(
            command, env=os.environ | self.environ, capture_output=True, text=True, check=False
        )
        return done.returncode, done.stdout, done.stderr


def answering(spack: StandIn, *, yes_to_all: bool = False) -> Spack:
    return Spack(StandInModule(spack.environ), str(spack.bin / "spack"), yes_to_all=yes_to_all)


def helps(spack: StandIn) -> list[list[str]]:
    """The help calls the stand-in saw, as the command words each was for."""
    return [call[:-1] for call in spack.calls() if call[-1:] == ["--help"]]


def test_with_the_flag_off_and_no_consent_nothing_is_added_or_read(spack: StandIn) -> None:
    assert answering(spack).answered(["gc"], words=1) == ["gc"]
    assert answering(spack).answered(["gc"]) == ["gc"]
    assert helps(spack) == []


def test_the_option_goes_straight_after_the_commands_words(spack: StandIn) -> None:
    assert answering(spack, yes_to_all=True).answered(["install", "--fake"], words=1) == [
        "install",
        "--yes-to-all",
        "--fake",
    ]
    assert helps(spack) == [["install"]]


def test_a_command_whose_help_does_not_list_it_is_left_alone(spack: StandIn) -> None:
    assert answering(spack, yes_to_all=True).answered(["mirror", "add", "n", "u"], words=2) == [
        "mirror",
        "add",
        "n",
        "u",
    ]
    assert helps(spack) == [["mirror", "add"]]


def test_a_command_already_answered_is_left_alone_unread(spack: StandIn) -> None:
    answers = answering(spack, yes_to_all=True)
    assert answers.answered(["gc", "-y"], words=1) == ["gc", "-y"]
    assert answers.answered(["module", "tcl", "refresh", "--yes-to-all"], words=3) == [
        "module",
        "tcl",
        "refresh",
        "--yes-to-all",
    ]
    assert helps(spack) == []


V1_0 = "1.0.0 (73eaea13f381e3495299284856fd02a64e1d154c)"
V1_1 = "1.1.0 (0c2be44e4ece21eb091ad5de4c97716b7c6d4c87)"


def test_each_version_has_its_row_and_a_newer_one_the_last() -> None:
    names = ("config_json", "gpg_colons", "trust_answers", "scope_needs_directory")
    assert behaviour((1, 0, 0)) == dict(zip(names, (False, False, False, False), strict=True))
    assert behaviour((1, 0, 4)) == behaviour((1, 0, 0))
    assert behaviour((1, 1, 1)) == dict(zip(names, (True, False, False, True), strict=True))
    assert behaviour((1, 2, 2)) == dict(zip(names, (True, True, True, False), strict=True))
    assert behaviour((1, 3, 0)) == behaviour((1, 2, 0)) == behaviour((2, 0, 0))


def test_a_trust_is_answered_where_spack_asks_with_the_flag_off(spack: StandIn) -> None:
    assert answering(spack).trusting(["gpg", "trust", "k.pub"], words=2) == [
        "gpg",
        "trust",
        "--yes-to-all",
        "k.pub",
    ]
    assert helps(spack) == []


def test_spack_1_0_and_1_1_are_not_given_the_option_they_do_not_have(spack: StandIn) -> None:
    for version in (V1_0, V1_1):
        spack.update(version=version)
        answers = answering(spack)
        assert answers.trusting(["gpg", "trust", "k.pub"], words=2) == ["gpg", "trust", "k.pub"]
        keys = ["buildcache", "keys", "--install", "--trust"]
        assert answers.trusting(keys, words=2) == keys


def test_configuration_is_read_as_json_or_through_spack_python_on_1_0(spack: StandIn) -> None:
    spack.update(scopes={"site": {"config": {"build_jobs": 4}}})
    assert answering(spack).config_section("config", scope="site") == {"build_jobs": 4}
    assert spack.calls("config")[-1] == ["config", "--scope", "site", "get", "--json", "config"]
    spack.update(version=V1_0)
    assert answering(spack).config_section("config", scope="site") == {"build_jobs": 4}
    assert answering(spack).config_section("config")["build_jobs"] == 4
    python = spack.calls("python")
    assert [call[:2] for call in python] == [["python", "-c"], ["python", "-c"]]
    assert "get_config('config', scope='site')" in python[0][2]
    assert "spack.config.get('config')" in python[1][2]


def test_a_scope_not_made_yet_is_empty_in_each_versions_words(spack: StandIn) -> None:
    for version in (V1_0, V1_1, "1.2.0"):
        spack.update(version=version, unmade_scopes=["user"])
        assert Configuration(answering(spack), "user").get("mirrors") == {}, version


def test_the_trusted_keys_are_read_without_fmt_on_1_0_and_1_1(spack: StandIn) -> None:
    keys = ["7500481A18F8F903534D953AC6F328B79BE7166C", "E0C894426081BF7A184E2AC8F2D4DFC4FD63F7FB"]
    spack.update(trusted=keys)
    assert answering(spack).trusted_keys() == keys
    for version in (V1_0, V1_1):
        spack.update(version=version)
        assert answering(spack).trusted_keys() == keys
    assert spack.calls("gpg", "list")[-1] == ["gpg", "list", "--trusted"]


def test_gpgs_own_listing_gives_its_fingerprints() -> None:
    # As Spack 1.1.0 printed it for the throwaway key (research.md, R6).
    printed = (
        "/tmp/csis-q-6X9K/pubring.kbx\n----------------------------\n"
        "pub   rsa2048 2026-11-14 [SC]\n      7500481A18F8F903534D953AC6F328B79BE7166C\n"
        "uid           [ultimate] Test Mirror <test@example.invalid>\n\n"
    )
    assert listed_fingerprints(printed) == ["7500481A18F8F903534D953AC6F328B79BE7166C"]
    assert listed_fingerprints("") == []


def test_a_help_is_read_once_in_a_run(spack: StandIn) -> None:
    answers = answering(spack, yes_to_all=True)
    answers.answered(["gc"], words=1)
    answers.answered(["gc", "--keep-going"], words=1)
    assert helps(spack) == [["gc"]]


def test_the_command_is_walked_to_from_its_first_word(spack: StandIn) -> None:
    answers = answering(spack, yes_to_all=True)
    assert answers.answered(["module", "tcl", "refresh", "--delete-tree"]) == [
        "module",
        "tcl",
        "refresh",
        "--yes-to-all",
        "--delete-tree",
    ]
    assert helps(spack) == [["module"], ["module", "tcl"], ["module", "tcl", "refresh"]]
    assert answers.answered(["gc"]) == ["gc", "--yes-to-all"]


def test_the_walk_stops_at_the_first_option(spack: StandIn) -> None:
    command = ["config", "--scope", "user", "add", "a:b"]
    assert answering(spack, yes_to_all=True).answered(command) == command
    assert helps(spack) == [["config"]]


def test_help_is_never_asked_for_after_a_word_that_is_not_a_subcommand(spack: StandIn) -> None:
    command = ["buildcache", "keys", "mirror1"]
    assert answering(spack, yes_to_all=True).answered(command) == [
        "buildcache",
        "keys",
        "--yes-to-all",
        "mirror1",
    ]
    assert helps(spack) == [["buildcache"], ["buildcache", "keys"]]


def test_an_alias_of_a_subcommand_is_walked_to(spack: StandIn) -> None:
    answering(spack, yes_to_all=True).answered(["buildcache", "create", "--only", "package", "m"])
    assert helps(spack)[-1] == ["buildcache", "create"]


def test_no_command_words_read_no_help(spack: StandIn) -> None:
    answers = answering(spack, yes_to_all=True)
    assert answers.answered(["-d", "install"]) == ["-d", "install"]
    assert answers.answered([]) == []
    assert helps(spack) == []


def test_a_help_that_fails_counts_as_not_taking_it(spack: StandIn) -> None:
    assert answering(spack, yes_to_all=True).answered(["nosuch", "x"]) == ["nosuch", "x"]
    assert helps(spack) == [["nosuch"]]
