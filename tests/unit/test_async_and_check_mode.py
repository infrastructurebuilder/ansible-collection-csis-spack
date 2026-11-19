"""A spack_env task that builds asynchronously can still be previewed.

Ansible refuses a task that is both asynchronous and in check mode. The
documentation gives a form whose async and poll fall to 0 in check mode;
these tests hold the documentation to that form and the module to working
with it.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml
from conftest import Spack
from runner import COLLECTIONS, ROOT

FORM_ASYNC = '"{{ 0 if ansible_check_mode else 86400 }}"'
FORM_POLL = '"{{ 0 if ansible_check_mode else 60 }}"'
# An async or poll given as a plain number: the form that cannot be previewed.
LITERAL = re.compile(r"^\s*(async|poll):\s*\d+\s*$", re.MULTILINE)


def documentation_of(module: str) -> tuple[dict, str]:
    source = (ROOT / "plugins" / "modules" / f"{module}.py").read_text()
    documentation = source.split('DOCUMENTATION = r"""', 1)[1].split('"""', 1)[0]
    examples = source.split('EXAMPLES = r"""', 1)[1].split('"""', 1)[0]
    return yaml.safe_load(documentation), examples


def test_the_notes_say_why_and_give_the_form() -> None:
    documentation, _examples = documentation_of("spack_env")
    notes = " ".join(documentation["notes"])
    assert "check mode and async cannot be used on same task" in notes
    assert FORM_ASYNC.strip('"') in notes
    assert FORM_POLL.strip('"') in notes


def test_no_example_gives_async_as_a_plain_number() -> None:
    _documentation, examples = documentation_of("spack_env")
    texts = {"spack_env EXAMPLES": examples, "README.md": (ROOT / "README.md").read_text()}
    for name in ("README.md", "roles/setup/README.md"):
        texts[name] = (ROOT / name).read_text()
    found = {name: LITERAL.findall(text) for name, text in texts.items() if LITERAL.search(text)}
    assert not found, found
    assert f"async: {FORM_ASYNC}" in examples
    assert f"poll: {FORM_POLL}" in examples


PLAY = f"""
- name: A build, as the documentation writes it
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Build the environment
      infrastructurebuilder.csis_spack.spack_env:
        path: "{{{{ env_path }}}}"
      async: {FORM_ASYNC}
      poll: {FORM_POLL}
"""


def play(spack: Spack, *, check: bool) -> subprocess.CompletedProcess[str]:
    directory = spack.env.parent / "play"
    directory.mkdir(exist_ok=True)
    (directory / "site.yml").write_text(PLAY)
    command = [
        str(Path(sys.executable).parent / "ansible-playbook"),
        "-i",
        "localhost,",
        "-e",
        json.dumps({"ansible_python_interpreter": sys.executable, "env_path": str(spack.env)}),
        str(directory / "site.yml"),
    ]
    if check:
        command.append("--check")
    env = os.environ | {"ANSIBLE_COLLECTIONS_PATH": str(COLLECTIONS), "ANSIBLE_NOCOLOR": "1"} | spack.environ
    return subprocess.run(command, capture_output=True, text=True, env=env, check=False)


def test_the_form_previews_without_building(spack: Spack) -> None:
    previewed = play(spack, check=True)
    assert previewed.returncode == 0, previewed.stdout + previewed.stderr
    assert "check mode and async cannot be used" not in previewed.stdout
    assert spack.calls("install") == []
    assert not (spack.env / "spack.lock").exists()


def test_the_form_builds_asynchronously_when_not_previewing(spack: Spack) -> None:
    built = play(spack, check=False)
    assert built.returncode == 0, built.stdout + built.stderr
    assert spack.calls("install") == [["install"]]
    assert "ASYNC" in built.stdout or "changed: [localhost]" in built.stdout


def test_a_plain_number_cannot_be_previewed(spack: Spack) -> None:
    """Why the form is needed: what Ansible does with async: 86400 in check mode."""
    directory = spack.env.parent / "play"
    directory.mkdir(exist_ok=True)
    (directory / "site.yml").write_text(PLAY.replace(FORM_ASYNC, "86400").replace(FORM_POLL, "60"))
    command = [
        str(Path(sys.executable).parent / "ansible-playbook"),
        "-i",
        "localhost,",
        "-e",
        json.dumps({"ansible_python_interpreter": sys.executable, "env_path": str(spack.env)}),
        "--check",
        str(directory / "site.yml"),
    ]
    env = os.environ | {"ANSIBLE_COLLECTIONS_PATH": str(COLLECTIONS), "ANSIBLE_NOCOLOR": "1"} | spack.environ
    done = subprocess.run(command, capture_output=True, text=True, env=env, check=False)
    assert done.returncode != 0
    assert "check mode and async cannot be used on same task" in done.stdout
