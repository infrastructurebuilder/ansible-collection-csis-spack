"""Run one of the collection's modules through ``ansible``, and give its result."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
# `just tree` puts the collection where Ansible looks for it.
COLLECTIONS = ROOT / ".tmp" / "collections"


def run_module(
    name: str, args: dict[str, Any], *, env: dict[str, str], check: bool = False
) -> dict[str, Any]:
    """Run ``infrastructurebuilder.csis_spack.<name>`` on localhost with ``args`` and ``env``."""
    command = [
        str(Path(sys.executable).parent / "ansible"),
        "localhost",
        "-i",
        "localhost,",
        "-c",
        "local",
        "-e",
        f"ansible_python_interpreter={sys.executable}",
        "-m",
        f"infrastructurebuilder.csis_spack.{name}",
        "-a",
        json.dumps(args),
    ]
    if check:
        command.append("--check")
    full_env = (
        os.environ
        | {
            "ANSIBLE_COLLECTIONS_PATH": str(COLLECTIONS),
            # ansible-core's own ad-hoc output: "localhost | CHANGED => {json}".
            "ANSIBLE_STDOUT_CALLBACK": "minimal",
            "ANSIBLE_LOAD_CALLBACK_PLUGINS": "1",
            "ANSIBLE_NOCOLOR": "1",
            "ANSIBLE_LOCALHOST_WARNING": "0",
        }
        | env
    )
    done = subprocess.run(command, capture_output=True, text=True, env=full_env, check=False)
    host, separator, body = done.stdout.partition(" => ")
    try:
        result = json.loads(body)
    except json.JSONDecodeError:
        raise AssertionError(done.stdout + done.stderr) from None
    assert separator, done.stdout + done.stderr
    # The minimal callback says "FAILED!" in the header and drops the key.
    result.setdefault("failed", "FAILED!" in host)
    # Ansible prints a module's warnings on stderr, wrapped, and takes them out of the result.
    result["_stderr"] = " ".join(done.stderr.split())
    return result


@dataclass
class Played:
    """What applying the setup role gave."""

    rc: int
    results: list[dict[str, Any]]
    output: str

    @property
    def changed(self) -> list[bool]:
        return [step["changed"] for step in self.results]


PLAYBOOK = """
- name: Apply the setup role
  hosts: localhost
  connection: local
  gather_facts: false
  vars_files:
    - variables.json
  tasks:
    - name: Apply it
      ansible.builtin.import_role:
        name: infrastructurebuilder.csis_spack.setup
    - name: Keep the results for the test
      ansible.builtin.copy:
        content: "{{ spack_setup_results | to_json }}"
        dest: "{{ playbook_dir }}/results.json"
        mode: "0644"
      check_mode: false
      changed_when: false
"""


def run_setup(
    steps: list[dict[str, Any]],
    where: Path,
    *,
    env: dict[str, str],
    check: bool = False,
    variables: dict[str, Any] | None = None,
) -> Played:
    """Apply ``infrastructurebuilder.csis_spack.setup`` on localhost with ``steps``."""
    directory = where / "play"
    directory.mkdir(exist_ok=True)
    (directory / "site.yml").write_text(PLAYBOOK)
    (directory / "variables.json").write_text(json.dumps({"spack_setup": steps} | (variables or {})))
    results = directory / "results.json"
    results.unlink(missing_ok=True)
    command = [
        str(Path(sys.executable).parent / "ansible-playbook"),
        "-i",
        "localhost,",
        "-e",
        f"ansible_python_interpreter={sys.executable}",
        str(directory / "site.yml"),
    ]
    if check:
        command.append("--check")
    full_env = (
        os.environ
        | {
            "ANSIBLE_COLLECTIONS_PATH": str(COLLECTIONS),
            "ANSIBLE_NOCOLOR": "1",
            "ANSIBLE_LOCALHOST_WARNING": "0",
        }
        | env
    )
    done = subprocess.run(command, capture_output=True, text=True, env=full_env, check=False)
    found = json.loads(results.read_text()) if results.is_file() else []
    return Played(rc=done.returncode, results=found, output=done.stdout + done.stderr)
