"""The setup role against the real Spack 1.0.0, 1.1.0 and 1.2.0, on the local machine (just full-test).

Everything is written to a user scope and a keyring made for the test, so
the Spack in .tmp/spack, which the other integration test shares, is left as
it was. The first test builds and fetches nothing. The second, of a mirror
that publishes a key, installs zlib with --fake (nothing is compiled) into a
store of its own, and pushes it signed to a mirror in a directory of its own.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml
from real_spack import keyring as signing_keyring
from real_spack import local_scopes, on_path, publish_keys, signing_key, spack_env, spack_version
from runner import ROOT, run_setup

pytestmark = pytest.mark.integration

KEY = ROOT / "tests" / "fixtures" / "throwaway-mirror-key.pub"
FINGERPRINT = "7500481A18F8F903534D953AC6F328B79BE7166C"
# The compiler this machine's Spack will find without anything loaded.
COMPILER = "apple-clang" if platform.system() == "Darwin" else "gcc"


__all__ = ["spack_env", "spack_version"]  # fixtures, each run once per version


@pytest.fixture
def keyring() -> Iterator[str]:
    """A keyring of the test's own. gpg's agent socket needs a short path, so not under tmp_path."""
    home = tempfile.mkdtemp(prefix="csis-gpg-")
    yield home
    subprocess.run(["gpgconf", "--homedir", home, "--kill", "gpg-agent"], check=False, capture_output=True)
    shutil.rmtree(home, ignore_errors=True)


def test_the_setup_role_against_the_real_spack(
    tmp_path: Path,
    spack_env: dict[str, str],
    spack_version: str,
    keyring: str,
) -> None:
    # The other integration test turns the user and system scopes off, so as
    # not to read this machine's own. Here the user scope is what is written
    # to, so both are pointed at directories of the test's instead.
    env = {name: value for name, value in spack_env.items() if name != "SPACK_DISABLE_LOCAL_CONFIG"} | {
        **local_scopes(tmp_path, spack_version),
        "SPACK_GNUPGHOME": keyring,
    }
    spack = on_path(spack_env)
    variables = {"spack_setup_executable": spack, "spack_setup_scope": "user"}

    def user(section: str) -> dict[str, Any]:
        # As YAML, which every Spack prints: 1.0 has no "config get --json".
        done = subprocess.run(
            [spack, "config", "--scope", "user", "get", section],
            env=env, capture_output=True, text=True, check=True,
        )  # fmt: skip
        return yaml.safe_load(done.stdout)[section]

    def apply(steps: list[dict[str, Any]], check: bool = False) -> list[bool]:
        played = run_setup(steps, tmp_path, env=env, check=check, variables=variables)
        assert played.rc == 0, played.output
        return played.changed

    steps: list[dict[str, Any]] = [
        {
            "kind": "config",
            "settings": {
                "config": {"build_jobs": 2},
                "packages": {
                    "all": {"providers": {"mpi": ["mympi", "othermpi"]}},
                    "mympi": {
                        "externals": [{"spec": "mympi@4.1", "prefix": "/opt/mympi"}],
                        "buildable": False,
                    },
                },
            },
        },
        {"kind": "environment", "name": "marked", "shell": "export CSIS_SPACK_TEST=1"},
        {"kind": "detect", "compilers": True, "environment": "marked", "require": [COMPILER]},
        {"kind": "detect", "externals": ["git"], "not_buildable": True},
        {
            "kind": "mirror",
            "name": "local",
            "url": f"file://{tmp_path}/mirror",
            "type": ["binary"],
            "signed": False,
        },
        {"kind": "gpg_key", "key": str(KEY), "fingerprint": FINGERPRINT},
        {
            "kind": "command",
            "args": ["config", "--scope", "user", "add", "config:connect_timeout:15"],
            "changes": "config",
            "sections": ["config"],
        },
    ]

    # Check mode names what is declared, runs no discovery, and writes nothing.
    assert apply(steps, check=True) == [True, False, False, False, True, True, True]
    assert not (tmp_path / "user").exists() or not list((tmp_path / "user").glob("*.yaml"))

    assert apply(steps) == [True, False, True, True, True, True, True]
    packages = user("packages")
    assert packages["all"]["providers"] == {"mpi": ["mympi", "othermpi"]}
    assert packages["mympi"] == {
        "externals": [{"spec": "mympi@4.1", "prefix": "/opt/mympi"}],
        "buildable": False,
    }
    assert any(name == COMPILER for name in packages), sorted(packages)
    assert packages["git"]["buildable"] is False
    assert user("config") == {"build_jobs": 2, "connect_timeout": 15}
    assert user("mirrors")["local"] == {
        "url": f"file://{tmp_path}/mirror",
        "binary": True,
        "source": False,
        "signed": False,
    }

    # A second application changes nothing, though Spack has rewritten packages.yaml.
    assert apply(steps) == [False] * len(steps)

    # A list is set exactly: Spack alone would merge the new item into the old ones.
    shorter = [{"kind": "config", "settings": {"packages": {"all": {"providers": {"mpi": ["othermpi"]}}}}}]
    assert apply(shorter) == [True]
    assert user("packages")["all"]["providers"] == {"mpi": ["othermpi"]}
    assert apply(shorter) == [False]

    # A changed mirror is corrected, and absent removes what is named and nothing else.
    moved = [
        {"kind": "mirror", "name": "local", "url": f"file://{tmp_path}/elsewhere", "type": ["binary"]},
        {"kind": "config", "state": "absent", "settings": {"packages": {"mympi": None}}},
    ]
    assert apply(moved) == [True, True]
    assert user("mirrors")["local"]["url"] == f"file://{tmp_path}/elsewhere"
    assert "mympi" not in user("packages")
    assert "git" in user("packages")
    assert apply(moved) == [False, False]

    # Removing a setting's only key: Spack would leave "install_tree: {}"
    # behind; the module removes the emptied mapping instead.
    padding = [{"kind": "config", "settings": {"config": {"install_tree": {"padded_length": 64}}}}]
    assert apply(padding) == [True]
    remove = [
        {
            "kind": "config",
            "state": "absent",
            "settings": {"config": {"install_tree": {"padded_length": None}}},
        }
    ]
    assert apply(remove) == [True]
    assert "install_tree" not in user("config")
    assert apply(remove) == [False]

    # A value Spack's schema refuses fails, and the scope is as it was.
    before = user("packages")
    refused = run_setup(
        [{"kind": "config", "settings": {"packages": {"git": {"buildable": "maybe"}}}}],
        tmp_path, env=env, variables=variables,
    )  # fmt: skip
    assert refused.rc != 0
    assert user("packages") == before


def test_the_setup_role_trusts_the_keys_a_mirror_publishes(
    tmp_path: Path,
    spack_env: dict[str, str],
    spack_version: str,
    keyring: str,
) -> None:
    """A gpg_key step of from_mirrors: true, against a mirror that publishes a key (spec 003, SC-001).

    The mirror is made here: zlib installed with --fake, pushed signed with a
    key made for the test, and the mirror's key index written.
    """
    env = {name: value for name, value in spack_env.items() if name != "SPACK_DISABLE_LOCAL_CONFIG"} | {
        **local_scopes(tmp_path, spack_version),
        "SPACK_GNUPGHOME": keyring,
    }
    spack = on_path(spack_env)
    built = tmp_path / "env"
    built.mkdir()
    (built / "spack.yaml").write_text(
        "spack:\n  specs: [zlib]\n  view: false\n  config:\n"
        f"    install_tree:\n      root: {tmp_path / 'store'}\n"
    )
    mirror = tmp_path / "mirror"
    with signing_keyring() as signing:
        key = signing_key(spack_env, signing, "Key A")
        signer = os.environ | spack_env | {"SPACK_GNUPGHOME": signing}
        push = ["buildcache", "push", "--key", key, str(mirror)]
        for args in (["concretize"], ["install", "--fake"], push):
            subprocess.run([spack, "-e", str(built), *args], env=signer, capture_output=True, check=True)
        publish_keys(spack_env, signing, mirror)

    steps: list[dict[str, Any]] = [
        {"kind": "mirror", "name": "signed", "url": f"file://{mirror}", "type": ["binary"]},
        {"kind": "gpg_key", "from_mirrors": True},
    ]
    variables = {"spack_setup_executable": spack, "spack_setup_scope": "user"}

    def apply() -> list[bool]:
        played = run_setup(steps, tmp_path, env=env, variables=variables)
        assert played.rc == 0, played.output
        return played.changed

    assert apply() == [True, True]
    assert apply() == [False, False]
