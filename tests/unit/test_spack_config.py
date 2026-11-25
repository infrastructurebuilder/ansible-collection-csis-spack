"""spack_config against the stand-in Spack: declared settings in a scope."""

from __future__ import annotations

from typing import Any

from conftest import Spack

SETTINGS = {
    "config": {"install_tree": {"padded_length": 73}},
    "modules": {"default": {"enable": ["tcl"]}},
    "packages": {
        "all": {"providers": {"mpi": ["mympi"], "blas": ["myblas"]}},
        "mympi": {"externals": [{"spec": "mympi@4.1", "prefix": "/opt/mympi"}], "buildable": False},
    },
}


def config(spack: Spack, settings: dict, *, check: bool = False, **options: Any) -> dict:
    return spack.module("spack_config", settings=settings, check=check, **options)


def test_settings_are_written_to_the_site_scope_and_named(spack: Spack) -> None:
    result = config(spack, SETTINGS)
    assert result["changed"] is True
    assert result["scope"] == "site"
    assert result["paths"] == [
        "config:install_tree",
        "modules:default",
        "packages:all",
        "packages:mympi",
    ]
    for section, data in SETTINGS.items():
        assert spack.scope("site", section) == data


def test_a_second_run_changes_nothing_and_writes_nothing(spack: Spack) -> None:
    config(spack, SETTINGS)
    writes = len(spack.calls("config", "--scope", "site", "add"))
    again = config(spack, SETTINGS)
    assert (again["changed"], again["paths"]) == (False, [])
    assert len(spack.calls("config", "--scope", "site", "add")) == writes
    assert spack.calls("config", "--scope", "site", "remove") == []


def test_one_file_is_added_per_section(spack: Spack) -> None:
    config(spack, SETTINGS)
    assert len(spack.calls("config", "--scope", "site", "add", "-f")) == len(SETTINGS)


def test_a_changed_list_is_set_exactly_not_merged(spack: Spack) -> None:
    config(spack, SETTINGS)
    result = config(spack, {"packages": {"all": {"providers": {"mpi": ["othermpi"]}}}})
    assert result["paths"] == ["packages:all:providers:mpi"]
    providers = spack.scope("site", "packages")["all"]["providers"]
    assert providers == {"mpi": ["othermpi"], "blas": ["myblas"]}
    assert spack.calls("config", "--scope", "site", "remove") == [
        ["config", "--scope", "site", "remove", "packages:all:providers:mpi"]
    ]


def test_an_external_whose_version_changed_is_corrected(spack: Spack) -> None:
    config(spack, SETTINGS)
    newer = {"packages": {"mympi": {"externals": [{"spec": "mympi@5.0", "prefix": "/opt/mympi5"}]}}}
    assert config(spack, newer)["changed"] is True
    assert spack.scope("site", "packages")["mympi"] == {
        "externals": [{"spec": "mympi@5.0", "prefix": "/opt/mympi5"}],
        "buildable": False,
    }


def test_merge_leaves_what_it_was_not_given_alone(spack: Spack) -> None:
    config(spack, SETTINGS)
    config(spack, {"packages": {"mytool": {"buildable": False}}})
    assert set(spack.scope("site", "packages")) == {"all", "mympi", "mytool"}


def test_replace_makes_a_section_exactly_what_is_given(spack: Spack) -> None:
    config(spack, SETTINGS)
    only = {"packages": {"mytool": {"buildable": False}}}
    result = config(spack, only, mode="replace")
    assert result["paths"] == ["packages:all", "packages:mympi", "packages:mytool"]
    assert spack.scope("site", "packages") == only["packages"]
    assert spack.scope("site", "config") == SETTINGS["config"]
    assert config(spack, only, mode="replace")["changed"] is False


def test_absent_removes_the_paths_named_and_only_those(spack: Spack) -> None:
    config(spack, SETTINGS)
    result = config(
        spack, {"packages": {"mympi": None, "all": {"providers": {"blas": None}}}}, state="absent"
    )
    assert result["paths"] == ["packages:all:providers:blas", "packages:mympi"]
    assert spack.scope("site", "packages") == {"all": {"providers": {"mpi": ["mympi"]}}}
    again = config(spack, {"packages": {"mympi": None}}, state="absent")
    assert again["changed"] is False


def test_another_scope_can_be_named(spack: Spack) -> None:
    config(spack, {"config": {"build_jobs": 4}}, scope="user")
    assert spack.scope("user", "config") == {"build_jobs": 4}
    assert spack.scope("site", "config") == {}


def test_check_mode_names_the_paths_and_writes_nothing(spack: Spack) -> None:
    result = config(spack, SETTINGS, check=True)
    assert result["changed"] is True
    assert len(result["paths"]) == 4
    assert spack.state.get("scopes", {}) == {}
    assert spack.calls("config", "--scope", "site", "add") == []


def test_a_value_spack_refuses_fails_and_leaves_the_scope_as_it_was(spack: Spack) -> None:
    config(spack, SETTINGS)
    result = config(spack, {"packages": {"mympi": {"buildable": "maybe"}}})
    assert result["failed"] is True
    assert "is not of type 'boolean'" in result["msg"]
    assert spack.scope("site", "packages") == SETTINGS["packages"]


def test_a_section_must_be_a_mapping(spack: Spack) -> None:
    result = config(spack, {"config": ["a list"]})
    assert result["failed"] is True
    assert "must be a mapping" in result["msg"]


def test_a_key_with_a_colon_is_refused(spack: Spack) -> None:
    result = config(spack, {"config": {"a:b": 1}})
    assert result["failed"] is True
    assert "cannot contain a colon" in result["msg"]


def test_spack_before_1_0_is_refused(spack: Spack) -> None:
    spack.update(version="0.22.5 (abcdef)")
    assert "too old" in config(spack, SETTINGS)["msg"]


def test_a_scope_that_has_not_been_made_yet_holds_nothing_and_can_be_written(spack: Spack) -> None:
    spack.update(unmade_scopes=["user"])
    result = config(spack, {"config": {"build_jobs": 4}}, scope="user")
    assert result.get("failed") is False
    assert result["changed"] is True
    assert spack.scope("user", "config") == {"build_jobs": 4}


def test_spack_1_0_reads_and_writes_a_scope_not_made_yet(spack: Spack) -> None:
    # Through "spack python -c", as 1.0 has no "config get --json" (research.md, R7, R8).
    spack.update(version="1.0.0 (73eaea13f381e3495299284856fd02a64e1d154c)", unmade_scopes=["user"])
    result = config(spack, {"config": {"build_jobs": 4}}, scope="user")
    assert (result.get("failed"), result["changed"]) == (False, True)
    assert spack.scope("user", "config") == {"build_jobs": 4}
    assert spack.calls("python")
    assert config(spack, {"config": {"build_jobs": 4}}, scope="user")["changed"] is False


def test_spack_1_1_cannot_write_a_scope_whose_directory_is_missing_and_says_so(spack: Spack) -> None:
    spack.update(version="1.1.0 (0c2be44e4ece21eb091ad5de4c97716b7c6d4c87)", unmade_scopes=["user"])
    preview = config(spack, {"config": {"build_jobs": 4}}, scope="user", check=True)
    assert (preview.get("failed"), preview["changed"]) == (False, True)
    result = config(spack, {"config": {"build_jobs": 4}}, scope="user")
    assert result["failed"] is True
    assert "Spack 1.1.0 has no configuration scope 'user' until its directory exists" in result["msg"]
    assert "Make the directory, then run again" in result["msg"]


def test_any_other_failure_to_read_a_scope_still_fails(spack: Spack) -> None:
    spack.update(fail={"config": True})
    assert config(spack, {"config": {"build_jobs": 4}})["failed"] is True


def test_removing_a_settings_only_key_removes_the_mapping_it_would_leave_empty(spack: Spack) -> None:
    """Spack leaves emptied mappings behind ("install_tree: {}"); the module removes them instead."""
    config(spack, {"config": {"install_tree": {"padded_length": 73}, "build_jobs": 4}}, scope="user")
    result = config(
        spack, {"config": {"install_tree": {"padded_length": None}}}, scope="user", state="absent"
    )
    assert result.get("failed") is False, result.get("msg")
    assert result["paths"] == ["config:install_tree"]
    assert spack.scope("user", "config") == {"build_jobs": 4}
    assert (
        config(spack, {"config": {"install_tree": {"padded_length": None}}}, scope="user", state="absent")[
            "changed"
        ]
        is False
    )


def test_removing_the_only_setting_of_a_section_leaves_the_section_empty(spack: Spack) -> None:
    config(spack, {"modules": {"default": {"enable": ["tcl"]}}}, scope="user")
    result = config(spack, {"modules": {"default": {"enable": None}}}, scope="user", state="absent")
    assert result.get("failed") is False, result.get("msg")
    assert result["paths"] == ["modules:default"]
    assert spack.scope("user", "modules") == {}


def test_a_mapping_that_keeps_other_keys_is_not_removed(spack: Spack) -> None:
    config(
        spack, {"config": {"install_tree": {"padded_length": 73, "root": "/opt/spack/store"}}}, scope="user"
    )
    result = config(
        spack, {"config": {"install_tree": {"padded_length": None}}}, scope="user", state="absent"
    )
    assert result["paths"] == ["config:install_tree:padded_length"]
    assert spack.scope("user", "config") == {"install_tree": {"root": "/opt/spack/store"}}
