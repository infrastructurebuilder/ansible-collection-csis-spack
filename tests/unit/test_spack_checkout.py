"""spack_checkout: Spack installed at a path at a version, by git, and left alone the second time.

The module runs the real ``git`` against a repository each test makes
(``spack_source.py``), whose ``bin/spack`` answers ``--version`` as Spack does.
A ``git`` wrapper on ``PATH`` records every call, and what called it.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from pathlib import Path
from typing import Any

import pytest
from conftest import Spack
from spack_source import git, make_source

REAL_GIT = shutil.which("git") or "git"
# What the module may run over a Spack it leaves alone: reading only.
READS = {"--version", "rev-parse", "symbolic-ref", "status"}


class Git:
    """A ``git`` on PATH that records each call (and the program that made it), then runs the real one."""

    def __init__(self, where: Path, *, version: str | None = None) -> None:
        self.bin = where / "git-wrapper"
        self.bin.mkdir()
        self.log = where / "git-calls.jsonl"
        answer = (
            f"if sys.argv[1:] == ['--version']:\n    print('git version {version}')\n    sys.exit(0)\n"
            if version
            else ""
        )
        program = self.bin / "git"
        program.write_text(
            f"#!{sys.executable}\n"
            "import json, os, subprocess, sys\n"
            "parent = subprocess.run(['ps', '-o', 'comm=', '-p', str(os.getppid())],\n"
            "                        capture_output=True, text=True).stdout.strip()\n"
            f"with open({str(self.log)!r}, 'a') as log:\n"
            "    log.write(json.dumps({'args': sys.argv[1:], 'parent': parent,\n"
            "                          'proxy': os.environ.get('HTTPS_PROXY')}) + '\\n')\n"
            f"{answer}"
            f"os.execv({REAL_GIT!r}, [{REAL_GIT!r}] + sys.argv[1:])\n"
        )
        program.chmod(0o755)

    def env(self, spack: Spack) -> dict[str, str]:
        return {"PATH": f"{self.bin}{os.pathsep}{spack.environ['PATH']}"}

    @property
    def calls(self) -> list[dict[str, Any]]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    @property
    def subcommands(self) -> list[str]:
        """Each call's subcommand, past any ``-C <dir>``."""
        out = []
        for call in self.calls:
            args = call["args"]
            while args[:1] == ["-C"]:
                args = args[2:]
            out.append(args[0] if args else "")
        return out


@pytest.fixture
def source(tmp_path: Path) -> tuple[str, dict[str, str]]:
    return make_source(tmp_path)


def checkout(
    spack: Spack, *, check: bool = False, task_env: dict[str, str] | None = None, **args: Any
) -> dict:
    return spack.module("spack_checkout", check=check, task_env=task_env, **args)


def head(path: Path) -> str:
    return git("rev-parse", "HEAD", cwd=path)


def hidden_beside(path: Path) -> list[str]:
    return sorted(
        entry.name for entry in path.parent.iterdir() if entry.name.startswith(f".{path.name}.install-")
    )


def test_a_tag_is_installed_where_nothing_was_then_left_alone(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    url, commits = source
    path = tmp_path / "opt" / "spack"
    path.parent.mkdir()
    result = checkout(spack, version="v1.2.0", path=str(path), source=url)
    assert result["failed"] is False, result.get("msg")
    assert result["changed"] is True
    assert result["found"] == "nothing"
    assert result["spack"] == str(path / "bin" / "spack")
    assert result["spack_version"].startswith("1.2.0 ")
    assert head(path) == commits["v1.2.0"]
    assert git("status", "--porcelain", cwd=path) == ""
    assert hidden_beside(path) == []

    again = checkout(spack, version="v1.2.0", path=str(path), source=url)
    assert again["failed"] is False, again.get("msg")
    assert (again["changed"], again["found"]) == (False, "spack")
    assert again["spack_version"].startswith("1.2.0 ")


def test_a_branch_is_installed_on_that_branch_then_left_alone(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    url, commits = source
    path = tmp_path / "spack"
    result = checkout(spack, version="releases/v1.2", path=str(path), source=url)
    assert result["failed"] is False, result.get("msg")
    assert result["changed"] is True
    assert result["spack_version"].startswith("1.2.1.dev0 ")
    assert git("symbolic-ref", "--short", "HEAD", cwd=path) == "releases/v1.2"
    assert head(path) == commits["releases/v1.2"]
    again = checkout(spack, version="releases/v1.2", path=str(path), source=url)
    assert (again["failed"], again["changed"]) == (False, False)


def test_a_commit_is_installed_by_its_full_hash_then_left_alone(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    url, commits = source
    path = tmp_path / "spack"
    result = checkout(spack, version=commits["v1.0.0"], path=str(path), source=url)
    assert result["failed"] is False, result.get("msg")
    assert result["changed"] is True
    assert result["spack_version"].startswith("1.0.0 ")
    assert head(path) == commits["v1.0.0"]
    assert git("remote", "get-url", "origin", cwd=path) == url
    again = checkout(spack, version=commits["v1.0.0"], path=str(path), source=url)
    assert (again["failed"], again["changed"]) == (False, False)


def test_the_missing_directories_above_the_path_are_made(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    path = tmp_path / "a" / "b" / "spack"
    result = checkout(spack, version="v1.2.0", path=str(path), source=source[0])
    assert result["failed"] is False, result.get("msg")
    assert (path / "bin" / "spack").is_file()


def test_an_empty_directory_is_installed_into_and_keeps_its_mode(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    path = tmp_path / "spack"
    path.mkdir(mode=0o750)
    path.chmod(0o750)
    preview = checkout(spack, check=True, version="v1.2.0", path=str(path), source=source[0])
    assert (preview["failed"], preview["changed"], preview["found"]) == (False, True, "empty")
    assert list(path.iterdir()) == []

    result = checkout(spack, version="v1.2.0", path=str(path), source=source[0])
    assert result["failed"] is False, result.get("msg")
    assert (result["changed"], result["found"]) == (True, "empty")
    assert stat.S_IMODE(path.stat().st_mode) == 0o750
    assert head(path) == source[1]["v1.2.0"]


def test_check_mode_makes_nothing_where_nothing_was(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    parent = tmp_path / "opt"
    parent.mkdir()
    path = parent / "spack"
    result = checkout(spack, check=True, version="v1.2.0", path=str(path), source=source[0])
    assert result["failed"] is False, result.get("msg")
    assert (result["changed"], result["found"]) == (True, "nothing")
    assert list(parent.iterdir()) == []


def test_check_mode_over_a_spack_at_the_version_only_reads(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    path = tmp_path / "spack"
    assert checkout(spack, version="v1.2.0", path=str(path), source=source[0])["changed"] is True
    recorder = Git(tmp_path)
    result = checkout(
        spack, check=True, task_env=recorder.env(spack), version="v1.2.0", path=str(path), source=source[0]
    )
    assert (result["failed"], result["changed"]) == (False, False)
    assert recorder.subcommands, "the wrapper saw no call"
    assert set(recorder.subcommands) <= READS, recorder.subcommands


def test_a_stale_directory_from_a_killed_run_is_left_alone(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    path = tmp_path / "spack"
    stale = tmp_path / ".spack.install-old"
    stale.mkdir()
    (stale / "half").write_text("a clone that was stopped\n")
    result = checkout(spack, version="v1.2.0", path=str(path), source=source[0])
    assert result["failed"] is False, result.get("msg")
    assert (path / "bin" / "spack").is_file()
    assert (stale / "half").is_file()
    assert hidden_beside(path) == [".spack.install-old"]


def test_a_version_not_in_the_source_leaves_nothing(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    path = tmp_path / "spack"
    result = checkout(spack, version="v9.9.9", path=str(path), source=source[0])
    assert result["failed"] is True
    assert "v9.9.9" in result["msg"]
    assert "not found" in result["msg"]
    assert not path.exists()
    assert hidden_beside(path) == []


@pytest.mark.parametrize("version", ["63962ed9", "deadbeef", "a" * 39])
def test_a_short_hash_is_refused_before_git_runs(spack: Spack, tmp_path: Path, version: str) -> None:
    recorder = Git(tmp_path)
    result = checkout(spack, task_env=recorder.env(spack), version=version, path=str(tmp_path / "spack"))
    assert result["failed"] is True
    assert "give the commit's full hash" in result["msg"]
    assert recorder.calls == []


def test_a_version_below_1_0_is_refused_and_leaves_nothing(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    path = tmp_path / "spack"
    result = checkout(spack, version="v0.23.0", path=str(path), source=source[0])
    assert result["failed"] is True
    assert "0.23.0" in result["msg"]
    assert "1.0" in result["msg"]
    assert not path.exists()
    assert hidden_beside(path) == []


def test_a_source_that_does_not_exist_fails_and_leaves_nothing(spack: Spack, tmp_path: Path) -> None:
    path = tmp_path / "spack"
    result = checkout(spack, version="v1.2.0", path=str(path), source=(tmp_path / "nowhere").as_uri())
    assert result["failed"] is True
    assert not path.exists()
    assert hidden_beside(path) == []


def without_git(where: Path) -> str:
    """A PATH with every program of this one but git: Ansible itself needs the rest on the node."""
    tools = where / "no-git"
    tools.mkdir()
    for directory in os.environ["PATH"].split(os.pathsep):
        if not Path(directory).is_dir():
            continue
        for entry in Path(directory).iterdir():
            link = tools / entry.name
            if entry.name != "git" and not link.exists() and not link.is_symlink():
                link.symlink_to(entry)
    return str(tools)


def test_without_git_it_fails_naming_git(spack: Spack, tmp_path: Path) -> None:
    path = without_git(tmp_path)
    result = checkout(spack, task_env={"PATH": path}, version="v1.2.0", path=str(tmp_path / "spack"))
    assert result["failed"] is True, result
    assert 'executable "git"' in result["msg"]
    assert not (tmp_path / "spack").exists()


def test_a_relative_path_is_refused(spack: Spack, source: tuple[str, dict[str, str]]) -> None:
    result = checkout(spack, version="v1.2.0", path="spack", source=source[0])
    assert result["failed"] is True
    assert "absolute" in result["msg"]


def test_a_symbolic_link_is_followed(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    to_nothing = tmp_path / "link-to-nothing"
    to_nothing.symlink_to(tmp_path / "target")
    result = checkout(spack, version="v1.2.0", path=str(to_nothing), source=source[0])
    assert result["failed"] is False, result.get("msg")
    assert to_nothing.is_symlink()
    assert (tmp_path / "target" / "bin" / "spack").is_file()

    empty = tmp_path / "empty"
    empty.mkdir()
    to_empty = tmp_path / "link-to-empty"
    to_empty.symlink_to(empty)
    result = checkout(spack, version="v1.2.0", path=str(to_empty), source=source[0])
    assert (result["failed"], result.get("found")) == (False, "empty"), result.get("msg")
    assert (empty / "bin" / "spack").is_file()


@pytest.mark.parametrize(
    "address", ["https://user:secret@git.example.org/spack.git", "https://token@git.example.org/spack.git"]
)
def test_a_source_holding_a_credential_is_refused_before_git_runs(
    spack: Spack, tmp_path: Path, address: str
) -> None:
    recorder = Git(tmp_path)
    result = checkout(
        spack, task_env=recorder.env(spack), version="v1.2.0", path=str(tmp_path / "spack"), source=address
    )
    assert result["failed"] is True
    assert "credential" in result["msg"]
    assert recorder.calls == []
    shown = json.dumps(result)
    assert "secret" not in shown
    assert "token" not in shown


def test_a_git_older_than_2_18_is_refused(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    old = Git(tmp_path, version="2.17.1")
    result = checkout(
        spack, task_env=old.env(spack), version="v1.2.0", path=str(tmp_path / "spack"), source=source[0]
    )
    assert result["failed"] is True
    assert "2.17.1" in result["msg"]
    assert "2.18" in result["msg"]
    assert old.subcommands == ["--version"]
    assert not (tmp_path / "spack").exists()


@pytest.mark.skipif(os.geteuid() == 0, reason="root can write anywhere")
def test_a_parent_that_cannot_be_written_to_fails_with_nothing_made(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0o555)
    try:
        result = checkout(spack, version="v1.2.0", path=str(locked / "spack"), source=source[0])
        assert result["failed"] is True
        assert list(locked.iterdir()) == []
    finally:
        locked.chmod(0o755)


def test_git_is_run_as_an_argument_list_never_through_a_shell(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    recorder = Git(tmp_path)
    env = recorder.env(spack)
    path = str(tmp_path / "spack")
    assert checkout(spack, task_env=env, version="v1.2.0", path=path, source=source[0])["changed"] is True
    assert checkout(spack, task_env=env, version="v1.2.0", path=path, source=source[0])["changed"] is False
    commit = source[1]["v1.0.0"]
    other = str(tmp_path / "by-hash")
    assert checkout(spack, task_env=env, version=commit, path=other, source=source[0])["changed"] is True
    assert recorder.calls
    shells = {"sh", "bash", "zsh", "dash", "/bin/sh", "/bin/bash", "/bin/zsh"}
    assert not [call for call in recorder.calls if call["parent"] in shells], recorder.calls


# User Story 2: a Spack already there is respected, and anything else is refused untouched.


def listing(path: Path) -> list[str]:
    return sorted(str(entry.relative_to(path)) for entry in path.rglob("*") if ".git" not in entry.parts)


@pytest.mark.parametrize("version", ["v1.0.0", "releases/v1.2"])
def test_a_spack_cloned_by_hand_at_the_version_is_left_alone(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]], version: str
) -> None:
    path = tmp_path / "spack"
    git("clone", "--quiet", "--depth", "1", "--branch", version, source[0], str(path))
    before = head(path)
    result = checkout(spack, version=version, path=str(path), source=source[0])
    assert result["failed"] is False, result.get("msg")
    assert (result["changed"], result["found"], result["edited"]) == (False, "spack", [])
    assert head(path) == before


@pytest.mark.parametrize("check", [False, True])
def test_a_spack_at_another_version_fails_and_is_left_as_it_was(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]], check: bool
) -> None:
    path = tmp_path / "spack"
    assert checkout(spack, version="v1.2.0", path=str(path), source=source[0])["changed"] is True
    before = (head(path), git("status", "--porcelain", cwd=path), listing(path))
    result = checkout(spack, check=check, version="v1.0.0", path=str(path), source=source[0])
    assert result["failed"] is True
    assert "tag v1.2.0" in result["msg"]
    assert "1.2.0 (" in result["msg"]
    assert "v1.0.0 was asked for" in result["msg"]
    assert "Nothing was changed" in result["msg"]
    assert (head(path), git("status", "--porcelain", cwd=path), listing(path)) == before


def not_a_spack(where: Path, case: str) -> Path:
    """Something at a path that is not a Spack, made as ``case`` says."""
    if case == "a file":
        path = where / "spack"
        path.write_text("not a directory\n")
        return path
    if case == "a directory that is not a git repository":
        path = where / "spack"
        path.mkdir()
        (path / "notes.txt").write_text("a site's own files\n")
        return path
    if case == "a git repository with no bin/spack":
        path = where / "spack"
        path.mkdir()
        git("init", "--quiet", str(path))
        (path / "notes.txt").write_text("a repository, but not Spack\n")
        return path
    # Inside another repository. (An empty directory there is an empty directory, FR-004.)
    outer = where / "outer"
    outer.mkdir()
    git("init", "--quiet", str(outer))
    path = outer / "sub"
    path.mkdir()
    (path / "notes.txt").write_text("inside another repository\n")
    return path


CASES = [
    "a file",
    "a directory that is not a git repository",
    "a git repository with no bin/spack",
    "a directory inside the git repository at",
]


@pytest.mark.parametrize("check", [False, True])
@pytest.mark.parametrize("case", CASES)
def test_what_is_not_a_spack_fails_and_is_left_as_it_was(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]], case: str, check: bool
) -> None:
    path = not_a_spack(tmp_path, case)
    before = path.read_text() if path.is_file() else listing(path)
    result = checkout(spack, check=check, version="v1.2.0", path=str(path), source=source[0])
    assert result["failed"] is True
    assert case in result["msg"]
    assert "it is not a Spack. Nothing was changed" in result["msg"]
    assert (path.read_text() if path.is_file() else listing(path)) == before


def test_a_spack_at_the_version_with_edited_files_is_left_alone_with_a_warning(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    path = tmp_path / "spack"
    assert checkout(spack, version="v1.2.0", path=str(path), source=source[0])["changed"] is True
    (path / "README.md").write_text("a site's own change\n")
    result = checkout(spack, version="v1.2.0", path=str(path), source=source[0])
    assert result["failed"] is False, result.get("msg")
    assert (result["changed"], result["edited"]) == (False, ["README.md"])
    assert "README.md" in result["_stderr"]
    assert (path / "README.md").read_text() == "a site's own change\n"


# User Story 3: the source a site names is the one used; with none, Spack's own repository.


@pytest.mark.parametrize("version", ["v1.2.0", "releases/v1.2", "full hash"])
def test_spack_is_fetched_from_the_source_named(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]], version: str
) -> None:
    url, commits = source
    named = commits["v1.0.0"] if version == "full hash" else version
    path = tmp_path / "spack"
    result = checkout(spack, version=named, path=str(path), source=url)
    assert result["failed"] is False, result.get("msg")
    assert result["source"] == url
    assert git("remote", "get-url", "origin", cwd=path) == url


def test_with_no_source_named_spacks_own_repository_is_the_one_used(spack: Spack, tmp_path: Path) -> None:
    # Check mode, so that nothing is fetched: the tests have no network (research.md R2 is the real fetch).
    result = checkout(spack, check=True, version="v1.2.0", path=str(tmp_path / "spack"))
    assert result["failed"] is False, result.get("msg")
    assert result["source"] == "https://github.com/spack/spack.git"
    assert not (tmp_path / "spack").exists()


def test_the_steps_environment_reaches_git(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    recorder = Git(tmp_path)
    environment = recorder.env(spack) | {"HTTPS_PROXY": "http://proxy.example.org:3128"}
    step = {
        "kind": "spack",
        "version": "v1.2.0",
        "path": str(tmp_path / "spack"),
        "source": source[0],
        "environment": environment,
    }
    played = spack.setup([step])
    assert played.rc == 0, played.output
    assert recorder.calls
    assert {call["proxy"] for call in recorder.calls} == {"http://proxy.example.org:3128"}
