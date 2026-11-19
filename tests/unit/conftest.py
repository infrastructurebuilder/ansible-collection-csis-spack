"""Run the collection's modules through Ansible, against the fake ``spack``."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from runner import COLLECTIONS, Played, run_module, run_setup

FAKE = Path(__file__).with_name("fake_spack.py")


def spec(name: str, digest: str, *, external: bool = False) -> dict[str, Any]:
    record: dict[str, Any] = {"name": name, "version": "1.0"}
    if external:
        record["external"] = {"path": "/usr", "module": None}
    return record | {"hash": digest}


def lock(*specs: dict[str, Any], roots: list[str]) -> dict[str, Any]:
    concrete = {record["hash"]: {k: v for k, v in record.items() if k != "hash"} for record in specs}
    by_name = {record["name"]: record["hash"] for record in specs}
    return {
        "_meta": {"lockfile-version": 6},
        "roots": [{"spec": name, "hash": by_name[name]} for name in roots],
        "concrete_specs": concrete,
    }


ZLIB = spec("zlib", "u7p436iplfqo6sroidvaws3xrweeryq2")
GMAKE = spec("gmake", "77tetl5sgzmktotuakiy2p42kosqdaid")
CLANG = spec("apple-clang", "chjqsswqp3xbq5a7gqwd4f5dk6yhbr3n", external=True)
ONE_PACKAGE = lock(ZLIB, GMAKE, CLANG, roots=["zlib"])


@dataclass
class Spack:
    """A fake Spack, its state, and an environment for it."""

    bin: Path
    state_file: Path
    env: Path
    root: Path

    @property
    def state(self) -> dict[str, Any]:
        return json.loads(self.state_file.read_text())

    def update(self, **values: Any) -> None:
        self.state_file.write_text(json.dumps(self.state | values))

    def calls(self, *prefix: str) -> list[list[str]]:
        """The calls made so far, without "-e <env>", that start with ``prefix``."""
        out = []
        for call in self.state.get("calls", []):
            if call[:1] == ["-e"]:
                call = call[2:]
            if call[: len(prefix)] == list(prefix):
                out.append(call)
        return out

    def scope(self, scope: str, section: str) -> dict[str, Any]:
        """One section of one configuration scope, as the stand-in holds it."""
        return self.state.get("scopes", {}).get(scope, {}).get(section, {})

    @property
    def environ(self) -> dict[str, str]:
        """What a process needs in its environment to meet the stand-ins."""
        return {
            "FAKE_SPACK_STATE": str(self.state_file),
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
        }

    def module(
        self, name: str, /, *, check: bool = False, task_env: dict[str, str] | None = None, **args: Any
    ) -> dict[str, Any]:
        """Run ``infrastructurebuilder.csis_spack.<name>`` with ``args`` against the fake.

        ``task_env`` stands for the task's ``environment:`` keyword.
        """
        return run_module(name, args, check=check, env=self.environ | (task_env or {}))

    def setup(self, steps: list[dict[str, Any]], *, check: bool = False, **variables: Any) -> Played:
        """Apply the collection's setup role with ``steps`` against the fake."""
        return run_setup(steps, self.env.parent, env=self.environ, check=check, variables=variables)


@pytest.fixture
def spack(tmp_path: Path) -> Spack:
    if not (COLLECTIONS / "ansible_collections" / "infrastructurebuilder" / "csis_spack").exists():
        pytest.fail("run `just tree` first: the collection is not where Ansible looks for it")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    program = bin_dir / "spack"
    program.write_text(
        f"#!{sys.executable}\nimport runpy, sys\nrunpy.run_path({str(FAKE)!r}, run_name='__main__')\n"
    )
    program.chmod(0o755)
    # A stand-in gpg too, for reading the fingerprints of a (stand-in) key file.
    gpg = bin_dir / "gpg"
    gpg.write_text(
        f"#!{sys.executable}\n"
        "import sys\n"
        "for line in open(sys.argv[-1]).read().splitlines():\n"
        "    if line.startswith('FAKE-PUBLIC-KEY '):\n"
        "        print('fpr:::::::::' + line.split()[1] + ':')\n"
    )
    gpg.chmod(0o755)
    root = tmp_path / "spack-root"
    root.mkdir()
    env = tmp_path / "env"
    env.mkdir()
    (env / "spack.yaml").write_text("spack:\n  specs: [zlib]\n")
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"root": str(root), "lock": ONE_PACKAGE, "installed": [], "calls": []}))
    return Spack(bin=bin_dir, state_file=state_file, env=env, root=root)
