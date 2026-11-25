"""spack_gpg_key against the stand-in Spack: public keys Spack trusts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from conftest import Spack

ONE = "7500481A18F8F903534D953AC6F328B79BE7166C"
TWO = "E0C894426081BF7A184E2AC8F2D4DFC4FD63F7FB"


def key_file(spack: Spack, *fingerprints: str, name: str = "site.pub") -> str:
    path = spack.env.parent / name
    path.write_text("".join(f"FAKE-PUBLIC-KEY {fingerprint}\n" for fingerprint in fingerprints))
    return str(path)


def trust(spack: Spack, *, check: bool = False, **options: Any) -> dict:
    return spack.module("spack_gpg_key", check=check, **options)


def test_a_key_file_is_trusted_and_its_fingerprint_reported(spack: Spack) -> None:
    path = key_file(spack, ONE)
    result = trust(spack, key=path)
    assert (result["changed"], result["trusted"]) == (True, [ONE])
    assert spack.state["trusted"] == [ONE]
    # Spack 1.2 asks before trusting each key; the option, which its help lists, answers it.
    assert spack.calls("gpg", "trust") == [["gpg", "trust", "--help"], ["gpg", "trust", "--yes-to-all", path]]


def test_a_second_run_changes_nothing_and_does_not_ask_spack_to_trust_again(spack: Spack) -> None:
    trust(spack, key=key_file(spack, ONE))
    again = trust(spack, key=key_file(spack, ONE))
    assert (again["changed"], again["trusted"]) == (False, [])
    assert len([call for call in spack.calls("gpg", "trust") if call[-1] != "--help"]) == 1


def test_with_a_fingerprint_a_trusted_key_is_not_even_read(spack: Spack) -> None:
    spack.update(trusted=[ONE])
    result = trust(spack, key=str(spack.env.parent / "not-there.pub"), fingerprint=ONE)
    assert result["changed"] is False
    assert spack.calls("gpg", "trust") == []


def test_a_fingerprint_may_be_written_with_spaces_and_in_lower_case(spack: Spack) -> None:
    spaced = " ".join(ONE[index : index + 4] for index in range(0, 40, 4)).lower()
    assert trust(spack, key=key_file(spack, ONE), fingerprint=spaced)["trusted"] == [ONE]


def test_a_file_holding_another_key_is_refused(spack: Spack) -> None:
    result = trust(spack, key=key_file(spack, TWO), fingerprint=ONE)
    assert result["failed"] is True
    assert f"holds the key {TWO}, not {ONE}" in result["msg"]
    assert spack.state.get("trusted", []) == []


def test_a_file_that_holds_no_key_is_refused_though_spack_would_exit_0(spack: Spack) -> None:
    path = Path(key_file(spack))
    path.write_text("not a key\n")
    result = trust(spack, key=str(path))
    assert result["failed"] is True
    assert "holds no OpenPGP public key" in result["msg"]
    assert spack.calls("gpg", "trust") == []


def test_a_missing_key_file_is_refused(spack: Spack) -> None:
    assert "there is no key file" in trust(spack, key="/nowhere/site.pub")["msg"]


def test_a_badly_formed_fingerprint_is_refused(spack: Spack) -> None:
    assert "40 hexadecimal digits" in trust(spack, key=key_file(spack, ONE), fingerprint="ABCD")["msg"]


def test_one_of_key_and_from_mirrors_is_needed(spack: Spack) -> None:
    assert "give key, or from_mirrors=true" in trust(spack, from_mirrors=False)["msg"]


def test_the_keys_the_mirrors_publish_are_trusted(spack: Spack) -> None:
    spack.module("spack_mirror", name="site-cache", url="https://cache.example.org", type=["binary"])
    spack.update(mirror_keys={"site-cache": [ONE, TWO]})
    result = trust(spack, from_mirrors=True)
    assert (result["changed"], result["trusted"]) == (True, sorted([ONE, TWO]))
    assert spack.calls("buildcache", "keys") == [
        ["buildcache", "keys", "--help"],
        ["buildcache", "keys", "--yes-to-all", "--install", "--trust"],
    ]
    # Spack asks again for keys it trusts already; a second run is answered too, and changes nothing.
    assert trust(spack, from_mirrors=True)["changed"] is False


def test_from_mirrors_with_no_binary_mirror_fails_as_spack_does(spack: Spack) -> None:
    result = trust(spack, from_mirrors=True)
    assert result["failed"] is True
    assert "Please add a spack mirror" in result["msg"]


def test_check_mode_knows_about_a_key_file(spack: Spack) -> None:
    result = trust(spack, key=key_file(spack, ONE), check=True)
    assert (result["changed"], result["trusted"], result["previewed"]) == (True, [ONE], True)
    assert spack.state.get("trusted", []) == []
    assert spack.calls("gpg", "trust") == []
    assert [call for call in spack.calls() if call[-1:] == ["--help"]] == []


def test_check_mode_cannot_know_what_the_mirrors_would_give(spack: Spack) -> None:
    result = trust(spack, from_mirrors=True, check=True)
    assert (result["changed"], result["previewed"]) == (False, False)
    assert spack.calls("buildcache", "keys") == []
    assert [call for call in spack.calls() if call[-1:] == ["--help"]] == []


def test_the_mirrors_keys_are_answered_for_whatever_yes_to_all_says(spack: Spack) -> None:
    # Asking for from_mirrors, or for a key, is the consent: yes_to_all is not needed.
    spack.module("spack_mirror", name="site-cache", url="https://cache.example.org", type=["binary"])
    spack.update(mirror_keys={"site-cache": [ONE]})
    assert trust(spack, from_mirrors=True, yes_to_all=False)["trusted"] == [ONE]
    assert trust(spack, key=key_file(spack, TWO), yes_to_all=False)["trusted"] == [TWO]


def test_spack_1_0_and_1_1_are_run_without_the_option_they_refuse(spack: Spack) -> None:
    # They have neither the question nor --yes-to-all, and fail with
    # "unrecognized arguments: -y" when given it (research.md, R2).
    spack.update(spack_like="1.1")
    spack.module("spack_mirror", name="site-cache", url="https://cache.example.org", type=["binary"])
    spack.update(mirror_keys={"site-cache": [ONE]})
    from_mirrors = trust(spack, from_mirrors=True)
    assert (from_mirrors["failed"], from_mirrors["changed"], from_mirrors["trusted"]) == (False, True, [ONE])
    from_file = trust(spack, key=key_file(spack, TWO))
    assert (from_file["failed"], from_file["changed"], from_file["trusted"]) == (False, True, [TWO])
    assert spack.calls("buildcache", "keys", "--install") == [["buildcache", "keys", "--install", "--trust"]]
    trusts = [call[2:] for call in spack.calls("gpg", "trust") if call[-1] != "--help"]
    assert trusts == [[key_file(spack, TWO)]]
    assert trust(spack, from_mirrors=True)["changed"] is False


def test_each_trust_reads_its_help_once(spack: Spack) -> None:
    spack.module("spack_mirror", name="site-cache", url="https://cache.example.org", type=["binary"])
    spack.update(mirror_keys={"site-cache": [ONE]})
    trust(spack, key=key_file(spack, TWO), from_mirrors=True)
    helps = [call for call in spack.calls() if call[-1:] == ["--help"]]
    assert helps == [["gpg", "trust", "--help"], ["buildcache", "keys", "--help"]]
