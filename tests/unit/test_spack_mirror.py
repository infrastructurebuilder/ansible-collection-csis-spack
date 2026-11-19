"""spack_mirror against the stand-in Spack: one mirror, declared."""

from __future__ import annotations

from typing import Any

from conftest import Spack

URL = "https://cache.example.org/spack"


def mirror(spack: Spack, *, check: bool = False, **options: Any) -> dict:
    args: dict[str, Any] = {"name": "site-cache"} | options
    return spack.module("spack_mirror", check=check, **args)


def test_a_missing_mirror_is_added(spack: Spack) -> None:
    result = mirror(spack, url=URL)
    assert (result["changed"], result["action"]) == (True, "added")
    assert result["mirror"] == {"url": URL}
    assert spack.scope("site", "mirrors") == {"site-cache": URL}
    assert spack.calls("mirror", "add") == [["mirror", "add", "--scope", "site", "site-cache", URL]]


def test_a_second_run_changes_nothing(spack: Spack) -> None:
    mirror(spack, url=URL)
    again = mirror(spack, url=URL)
    assert (again["changed"], again["action"]) == (False, "none")
    assert len(spack.calls("mirror", "add")) == 1


def test_a_changed_url_is_corrected(spack: Spack) -> None:
    mirror(spack, url=URL)
    result = mirror(spack, url=URL + "/v2")
    assert result["action"] == "replaced"
    assert spack.scope("site", "mirrors") == {"site-cache": URL + "/v2"}


def test_type_and_signed_reach_spack_and_are_compared(spack: Spack) -> None:
    result = mirror(spack, url=URL, type=["binary"], signed=True)
    assert result["mirror"] == {"url": URL, "binary": True, "source": False, "signed": True}
    assert spack.calls("mirror", "add")[0] == [
        "mirror", "add", "--scope", "site", "--type", "binary", "--signed", "site-cache", URL
    ]  # fmt: skip
    assert mirror(spack, url=URL, type=["binary"], signed=True)["changed"] is False
    assert mirror(spack, url=URL, type=["binary"], signed=False)["action"] == "replaced"
    assert mirror(spack, url=URL, type=["binary", "source"], signed=False)["action"] == "replaced"


def test_properties_not_given_are_not_compared(spack: Spack) -> None:
    mirror(spack, url=URL, type=["binary"], signed=True)
    assert mirror(spack, url=URL)["changed"] is False


def test_a_bare_mirror_holds_both_kinds(spack: Spack) -> None:
    mirror(spack, url=URL)
    assert mirror(spack, url=URL, type=["binary", "source"])["changed"] is False
    assert mirror(spack, url=URL, type=["source"])["action"] == "replaced"


def test_absent_removes_it_once(spack: Spack) -> None:
    mirror(spack, url=URL)
    result = mirror(spack, state="absent")
    assert (result["changed"], result["action"], result["mirror"]) == (True, "removed", {})
    assert spack.scope("site", "mirrors") == {}
    assert mirror(spack, state="absent")["changed"] is False


def test_present_needs_a_url(spack: Spack) -> None:
    result = mirror(spack)
    assert result["failed"] is True
    assert "url" in result["msg"]


def test_check_mode_says_what_it_would_do_and_does_not(spack: Spack) -> None:
    assert mirror(spack, url=URL, check=True)["action"] == "added"
    assert spack.scope("site", "mirrors") == {}
    mirror(spack, url=URL)
    assert mirror(spack, url=URL + "/v2", check=True)["action"] == "replaced"
    assert mirror(spack, state="absent", check=True)["action"] == "removed"
    assert spack.scope("site", "mirrors") == {"site-cache": URL}


def test_another_scope_can_be_named(spack: Spack) -> None:
    mirror(spack, url=URL, scope="user")
    assert spack.scope("user", "mirrors") == {"site-cache": URL}
