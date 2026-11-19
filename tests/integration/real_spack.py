"""The real Spack the integration tests run against, cloned once into .tmp/spack."""

from __future__ import annotations

import os
import subprocess

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
