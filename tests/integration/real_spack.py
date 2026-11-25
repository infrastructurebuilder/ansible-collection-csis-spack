"""The real Spack the integration tests run against, cloned once into .tmp/spack."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from runner import ROOT

SPACK_VERSION = "v1.2.0"
TMP = ROOT / ".tmp"
SPACK = TMP / "spack"


def real_spack_env() -> dict[str, str]:
    """Clone Spack if it is not there, and give the environment that points at it.

    Its user configuration and caches are kept in .tmp/ too, and the machine's
    own user and system scopes are not read.
    """
    if not (SPACK / "bin" / "spack").exists():
        subprocess.run(
            ["git", "clone", "--quiet", "--depth", "1", "--branch", SPACK_VERSION,
             "https://github.com/spack/spack.git", str(SPACK)],
            check=True,
        )  # fmt: skip
    return {
        "SPACK_USER_CONFIG_PATH": str(TMP / "spack-user"),
        "SPACK_USER_CACHE_PATH": str(TMP / "spack-cache"),
        "SPACK_DISABLE_LOCAL_CONFIG": "1",
        "PATH": f"{SPACK / 'bin'}{os.pathsep}{os.environ['PATH']}",
    }


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
    spack = str(SPACK / "bin" / "spack")
    run_env = os.environ | env | {"SPACK_GNUPGHOME": home}

    def signing() -> set[str]:
        listed = subprocess.run(
            [spack, "gpg", "list", "--signing", "--fmt", "colons"],
            env=run_env, capture_output=True, text=True, check=True,
        )  # fmt: skip
        return {line.split(":")[9] for line in listed.stdout.splitlines() if line.startswith("fpr:")}

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
        [str(SPACK / "bin" / "spack"), "buildcache", "update-index", "--keys", str(mirror)],
        env=os.environ | env | {"SPACK_GNUPGHOME": home}, capture_output=True, check=True,
    )  # fmt: skip
