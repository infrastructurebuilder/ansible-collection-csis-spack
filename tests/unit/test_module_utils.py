"""The helpers in plugins/module_utils/spack.py that read Spack's output."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from ansible_collections.infrastructurebuilder.csis_spack.plugins.module_utils.spack import (
    SpackError,
    data_digest,
    external_specs,
    file_digest,
    fingerprints,
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
