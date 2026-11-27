"""spack_buildcache_push against the fake Spack: what it runs, and what it reports."""

from __future__ import annotations

import json
from typing import Any

from conftest import CLANG, GMAKE, ZLIB, Spack, lock, spec


def installed(spack: Spack) -> Spack:
    spack.module("spack_env", path=str(spack.env))
    return spack


def names(result: dict) -> list[str]:
    return sorted(item["spec"] for item in result["pushed"])


def test_a_first_push_pushes_what_was_built_and_says_so(spack: Spack) -> None:
    result = installed(spack).module(
        "spack_buildcache_push", env=str(spack.env), mirror="/srv/mirror", unsigned=True
    )
    assert result["changed"] is True
    assert names(result) == ["gmake", "zlib"]
    assert {item["hash"] for item in result["pushed"]} == {ZLIB["hash"], GMAKE["hash"]}
    assert result["mirror_url"] == "file:///srv/mirror"
    assert spack.calls("buildcache", "push") == [["buildcache", "push", "--unsigned", "/srv/mirror"]]


def test_a_second_push_changes_nothing(spack: Spack) -> None:
    installed(spack).module("spack_buildcache_push", env=str(spack.env), mirror="/srv/mirror", unsigned=True)
    again = spack.module("spack_buildcache_push", env=str(spack.env), mirror="/srv/mirror", unsigned=True)
    assert again["changed"] is False
    assert again["pushed"] == []


def test_the_options_reach_spack(spack: Spack) -> None:
    installed(spack).module(
        "spack_buildcache_push",
        env=str(spack.env),
        mirror="/srv/mirror",
        key="ABCDEF",
        update_index=True,
        only="package",
        force=True,
    )
    assert spack.calls("buildcache", "push") == [
        [
            "buildcache",
            "push",
            "--key",
            "ABCDEF",
            "--update-index",
            "--only",
            "package",
            "--force",
            "/srv/mirror",
        ]
    ]


def test_key_and_unsigned_together_are_refused(spack: Spack) -> None:
    result = spack.module("spack_buildcache_push", env=str(spack.env), mirror="m", key="K", unsigned=True)
    assert result["failed"] is True
    assert "mutually exclusive" in result["msg"]


def test_a_mirror_named_in_spack_is_resolved_to_its_url(spack: Spack) -> None:
    installed(spack).update(mirrors={"s3-mirror": "s3://bucket/spack"})
    result = spack.module("spack_buildcache_push", env=str(spack.env), mirror="s3-mirror", unsigned=True)
    assert result["mirror_url"] == "s3://bucket/spack"
    assert spack.calls("buildcache", "push")[0][-1] == "s3-mirror"


def test_an_unknown_mirror_name_is_refused(spack: Spack) -> None:
    result = installed(spack).module("spack_buildcache_push", env=str(spack.env), mirror="nowhere")
    assert result["failed"] is True
    assert "no mirror named 'nowhere'" in result["msg"]
    assert spack.calls("buildcache", "push") == []


def test_check_mode_lists_what_the_mirror_lacks_and_pushes_nothing(spack: Spack) -> None:
    installed(spack).update(mirror_contents=[GMAKE["hash"]])
    result = spack.module(
        "spack_buildcache_push", env=str(spack.env), mirror="/srv/mirror", unsigned=True, check=True
    )
    assert result["changed"] is True
    assert result["pushed"] == [{"spec": "zlib", "hash": ZLIB["hash"]}]
    assert spack.calls("buildcache", "push") == []
    checks = spack.calls("buildcache", "check")
    assert len(checks) == 1
    assert checks[0][:5] == ["buildcache", "check", "-m", "file:///srv/mirror", "-o"]
    assert spack.state["mirror_contents"] == [GMAKE["hash"]]


def test_check_mode_never_counts_externals(spack: Spack) -> None:
    result = installed(spack).module(
        "spack_buildcache_push", env=str(spack.env), mirror="/srv/mirror", unsigned=True, check=True
    )
    assert CLANG["hash"] not in [item["hash"] for item in result["pushed"]]


def test_check_mode_after_a_push_reports_no_change(spack: Spack) -> None:
    installed(spack).module("spack_buildcache_push", env=str(spack.env), mirror="/srv/mirror", unsigned=True)
    result = spack.module(
        "spack_buildcache_push", env=str(spack.env), mirror="/srv/mirror", unsigned=True, check=True
    )
    assert result["changed"] is False


def test_check_mode_follows_only(spack: Spack) -> None:
    installed(spack)
    package = spack.module(
        "spack_buildcache_push", env=str(spack.env), mirror="/m", unsigned=True, only="package", check=True
    )
    dependencies = spack.module(
        "spack_buildcache_push",
        env=str(spack.env),
        mirror="/m",
        unsigned=True,
        only="dependencies",
        check=True,
    )
    assert names(package) == ["zlib"]
    assert names(dependencies) == ["gmake"]


def test_check_mode_with_force_lists_everything_built(spack: Spack) -> None:
    installed(spack).module("spack_buildcache_push", env=str(spack.env), mirror="/m", unsigned=True)
    result = spack.module(
        "spack_buildcache_push", env=str(spack.env), mirror="/m", unsigned=True, force=True, check=True
    )
    assert names(result) == ["gmake", "zlib"]


def test_a_failed_push_fails(spack: Spack) -> None:
    installed(spack).update(fail={"push": True})
    result = spack.module("spack_buildcache_push", env=str(spack.env), mirror="/m", unsigned=True)
    assert result["failed"] is True
    assert "push failed on purpose" in result["msg"]


PUSH = {"mirror": "/srv/mirror", "unsigned": True}
BZIP2 = spec("bzip2", "cswnif75ihvlnxagiqxgulyyqfunqn4b")


def push(spack: Spack, *, check: bool = False, **options: Any) -> dict:
    return spack.module("spack_buildcache_push", env=str(spack.env), check=check, **(PUSH | options))


def test_the_mirror_is_asked_before_and_after_a_push(spack: Spack) -> None:
    push(installed(spack))
    kinds = [call[1] for call in spack.calls("buildcache")]
    assert kinds == ["check", "push", "check"]


def test_what_was_pushed_does_not_depend_on_how_spack_words_it(spack: Spack) -> None:
    installed(spack).update(push_format="other")
    result = push(spack)
    assert result["changed"] is True
    assert names(result) == ["gmake", "zlib"]
    assert push(spack)["changed"] is False


def test_only_what_the_mirror_gained_is_reported(spack: Spack) -> None:
    installed(spack).update(mirror_contents=[GMAKE["hash"]])
    assert push(spack)["pushed"] == [{"spec": "zlib", "hash": ZLIB["hash"]}]


def test_force_true_overwrites_and_reports_everything_every_run_and_warns(spack: Spack) -> None:
    push(installed(spack))
    for _run in range(2):
        result = push(spack, force=True)
        assert result["changed"] is True
        assert names(result) == ["gmake", "zlib"]
        assert "[WARNING]: force=true overwrites every package" in result["_stderr"]
    assert sorted(spack.state["overwritten"]) == sorted([GMAKE["hash"], ZLIB["hash"]] * 2)


def test_without_force_there_is_no_warning(spack: Spack) -> None:
    assert "force=true" not in push(installed(spack))["_stderr"]


def test_force_once_overwrites_each_package_one_time(spack: Spack) -> None:
    push(installed(spack))
    first = push(spack, force="once")
    assert first["changed"] is True
    assert names(first) == ["gmake", "zlib"]
    assert sorted(spack.state["overwritten"]) == sorted([GMAKE["hash"], ZLIB["hash"]])
    chosen = sorted(["/" + GMAKE["hash"], "/" + ZLIB["hash"]])
    assert [
        "buildcache",
        "push",
        "--unsigned",
        "--only",
        "package",
        "--force",
        "/srv/mirror",
        *chosen,
    ] in spack.calls("buildcache", "push")

    second = push(spack, force="once")
    assert (second["changed"], second["pushed"]) == (False, [])
    assert len(spack.state["overwritten"]) == 2
    assert "force=true" not in second["_stderr"]


def test_force_once_remembers_per_mirror_in_the_environment(spack: Spack) -> None:
    push(installed(spack), force="once")
    state = json.loads((spack.env / ".spack-env" / "csis_spack.pushed.json").read_text())
    assert state == {
        "version": 1,
        "mirrors": {"file:///srv/mirror": sorted([GMAKE["hash"], ZLIB["hash"]])},
    }
    other = push(spack, force="once", mirror="/srv/other")
    assert names(other) == ["gmake", "zlib"]
    state = json.loads((spack.env / ".spack-env" / "csis_spack.pushed.json").read_text())
    assert sorted(state["mirrors"]) == ["file:///srv/mirror", "file:///srv/other"]


def test_force_once_overwrites_only_a_package_that_is_new(spack: Spack) -> None:
    push(installed(spack), force="once")
    spack.update(lock=lock(ZLIB, GMAKE, CLANG, BZIP2, roots=["zlib", "bzip2"]))
    spack.module("spack_env", path=str(spack.env))
    result = push(spack, force="once")
    assert result["pushed"] == [{"spec": "bzip2", "hash": BZIP2["hash"]}]
    forced = [call for call in spack.calls("buildcache", "push") if "--force" in call]
    assert forced[-1][-1] == "/" + BZIP2["hash"]
    assert forced[-1][-2] == "/srv/mirror"


def test_force_once_in_check_mode_lists_what_it_would_overwrite(spack: Spack) -> None:
    push(installed(spack))
    result = push(spack, force="once", check=True)
    assert names(result) == ["gmake", "zlib"]
    assert spack.state.get("overwritten", []) == []
    assert not (spack.env / ".spack-env" / "csis_spack.pushed.json").exists()


def test_force_takes_true_false_or_once(spack: Spack) -> None:
    result = push(installed(spack), force="sometimes")
    assert result["failed"] is True
    assert "force must be true, false or once" in result["msg"]
    assert spack.calls("buildcache") == []


def helps(spack: Spack) -> list[list[str]]:
    """The help calls the stand-in saw, as the command words each was for."""
    return [call[:-1] for call in spack.calls() if call[-1:] == ["--help"]]


def test_yes_to_all_reads_the_push_help_and_adds_nothing_it_does_not_list(spack: Spack) -> None:
    installed(spack)
    result = spack.module(
        "spack_buildcache_push", env=str(spack.env), mirror="/srv/mirror", unsigned=True, yes_to_all=True
    )
    assert result["failed"] is False, result.get("msg")
    assert ["buildcache", "push"] in helps(spack)
    assert all("--yes-to-all" not in call for call in spack.calls("buildcache", "push"))


def test_without_yes_to_all_a_push_reads_no_help(spack: Spack) -> None:
    installed(spack)
    spack.module("spack_buildcache_push", env=str(spack.env), mirror="/srv/mirror", unsigned=True)
    assert helps(spack) == []


def test_update_index_says_when_the_index_is_rebuilt() -> None:
    """Spec 006: Spack rebuilds the index only after a push that sent something."""
    from runner import ROOT

    source = (ROOT / "plugins" / "modules" / "spack_buildcache_push.py").read_text()
    documentation = source.split('DOCUMENTATION = r"""', 1)[1].split('"""', 1)[0]
    import yaml

    text = " ".join(yaml.safe_load(documentation)["options"]["update_index"]["description"])
    assert "only after a push that sent something" in text
    assert "spack buildcache update-index" in text
    # The description agrees: no index is rebuilt without a push (spec 006, T022).
    described = " ".join(" ".join(yaml.safe_load(documentation)["description"]).split())
    assert "alone is not reported as a change" not in described
    assert "only after a push that sent something" in described
