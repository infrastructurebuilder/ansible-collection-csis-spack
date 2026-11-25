"""The real Spacks the integration tests run against, each cloned once into .tmp/.

The pin, v1.2.0, is the version the tests are written to, in .tmp/spack.
They also run against the other versions the collection supports, 1.0 and
1.1, each in .tmp/spack-<version> (specs/003-mirror-keys-yes-to-all, FR-010).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from runner import ROOT

SPACK_VERSION = "v1.2.0"
SPACK_VERSIONS = ("v1.0.0", "v1.1.0", SPACK_VERSION)
TMP = ROOT / ".tmp"
SPACK = TMP / "spack"


def spack_root(version: str = SPACK_VERSION) -> Path:
    """Where a version is cloned: the pin in .tmp/spack, any other in .tmp/spack-<version>."""
    return SPACK if version == SPACK_VERSION else TMP / f"spack-{version}"


def spack_executable(version: str = SPACK_VERSION) -> str:
    return str(spack_root(version) / "bin" / "spack")


def real_spack_env(version: str = SPACK_VERSION) -> dict[str, str]:
    """Clone a Spack if it is not there, and give the environment that points at it.

    Its user configuration and caches are kept in .tmp/ too, one of each per
    version, and the machine's own user and system scopes are not read.
    """
    root = spack_root(version)
    if not (root / "bin" / "spack").exists():
        subprocess.run(
            ["git", "clone", "--quiet", "--depth", "1", "--branch", version,
             "https://github.com/spack/spack.git", str(root)],
            check=True,
        )  # fmt: skip
    suffix = "" if version == SPACK_VERSION else f"-{version}"
    return {
        "SPACK_USER_CONFIG_PATH": str(TMP / f"spack-user{suffix}"),
        "SPACK_USER_CACHE_PATH": str(TMP / f"spack-cache{suffix}"),
        "SPACK_DISABLE_LOCAL_CONFIG": "1",
        "PATH": f"{root / 'bin'}{os.pathsep}{os.environ['PATH']}",
    }


@pytest.fixture(scope="module", params=SPACK_VERSIONS)
def spack_version(request: pytest.FixtureRequest) -> str:
    """Each version the integration tests run against, in turn."""
    return request.param


@pytest.fixture(scope="module")
def spack_env(spack_version: str) -> dict[str, str]:
    return real_spack_env(spack_version)


def on_path(env: dict[str, str]) -> str:
    """The spack an environment from real_spack_env runs."""
    found = shutil.which("spack", path=env["PATH"])
    assert found, env["PATH"]
    return found


@contextmanager
def keyring() -> Iterator[str]:
    """A GPG home of a test's own. gpg's agent socket needs a short path, so not under tmp_path."""
    home = tempfile.mkdtemp(prefix="csis-gpg-")
    try:
        yield home
    finally:
        kill = ["gpgconf", "--homedir", home, "--kill", "gpg-agent"]
        subprocess.run(kill, check=False, capture_output=True)
        shutil.rmtree(home, ignore_errors=True)


def signing_key(env: dict[str, str], home: str, name: str) -> str:
    """Make a signing key in ``home`` with ``spack gpg create``, and give its fingerprint."""
    spack = on_path(env)
    run_env = os.environ | env | {"SPACK_GNUPGHOME": home}

    def signing() -> set[str]:
        # gpg's own listing: Spack 1.0 and 1.1 have no --fmt colons.
        listed = subprocess.run(
            [spack, "gpg", "list", "--signing"], env=run_env, capture_output=True, text=True, check=True
        )
        return set(re.findall(r"^\s+([0-9A-F]{40})\s*$", listed.stdout, re.MULTILINE))

    before = signing()
    subprocess.run(
        [spack, "gpg", "create", name, f"{name.lower().replace(' ', '-')}@example.invalid"],
        env=run_env, capture_output=True, check=True,
    )  # fmt: skip
    (made,) = signing() - before
    return made


def publish_keys(env: dict[str, str], home: str, mirror: Path) -> None:
    """Write a mirror's key index, without which ``buildcache keys`` finds none of its keys.

    ``buildcache push --key`` writes the key's manifest, but only
    ``buildcache update-index --keys`` lists it (Spack v1.2.0;
    specs/003-mirror-keys-yes-to-all/research.md, R4).
    """
    subprocess.run(
        [on_path(env), "buildcache", "update-index", "--keys", str(mirror)],
        env=os.environ | env | {"SPACK_GNUPGHOME": home}, capture_output=True, check=True,
    )  # fmt: skip


def local_scopes(tmp_path: Path, version: str) -> dict[str, str]:
    """Point the user and system scopes at directories of a test's own.

    Spack 1.1 has no scope at all whose directory does not exist (they are
    "optional" includes), and refuses to write to it; the modules then fail
    and say so, and do not make it (the operator's decision, 2026-11-25). So
    on 1.1 the user scope's directory is made first, as a site would
    (specs/003-mirror-keys-yes-to-all/research.md, R8).
    """
    if version == "v1.1.0":
        (tmp_path / "user").mkdir(exist_ok=True)
    return {
        "SPACK_USER_CONFIG_PATH": str(tmp_path / "user"),
        "SPACK_SYSTEM_CONFIG_PATH": str(tmp_path / "system"),
    }
