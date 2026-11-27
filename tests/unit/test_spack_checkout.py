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


# Found by T032's check of every requirement against a test.


def test_a_repeat_run_needs_no_network(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    """FR-005: whether the Spack there is at the version is read from it, not from the source."""
    path = tmp_path / "spack"
    for version in ("v1.2.0", "releases/v1.2", source[1]["v1.0.0"]):
        target = tmp_path / version.replace("/", "-")
        assert checkout(spack, version=version, path=str(target), source=source[0])["changed"] is True
        unreachable = "https://git.invalid/spack.git"
        again = checkout(spack, version=version, path=str(target), source=unreachable)
        assert (again["failed"], again["changed"]) == (False, False), again.get("msg")
    assert not path.exists()


def test_a_spack_that_prints_no_version_fails(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    """FR-006: an answer whose first word is not a version fails, here over a Spack already there."""
    path = tmp_path / "spack"
    assert checkout(spack, version="v1.2.0", path=str(path), source=source[0])["changed"] is True
    (path / "bin" / "spack").write_text('#!/bin/sh\necho "Spack, of some version"\n')
    result = checkout(spack, version="v1.2.0", path=str(path), source=source[0])
    assert result["failed"] is True
    assert "did not print a version" in result["msg"]


# Spec 005: with move, a Spack at another version is moved to the one named, in place.

NOT_CHECKED = "found only when the move is made"


def moving_beside(path: Path) -> list[str]:
    return sorted(
        entry.name for entry in path.parent.iterdir() if entry.name.startswith(f".{path.name}.move-")
    )


def objects(path: Path) -> dict[str, str]:
    """What git counts in .git, to see that check mode fetched nothing."""
    counted = dict(line.split(": ", 1) for line in git("count-objects", "-v", cwd=path).splitlines())
    return {key: counted[key] for key in ("count", "in-pack")}


def installed(spack: Spack, path: Path, version: str, url: str) -> None:
    result = checkout(spack, version=version, path=str(path), source=url)
    assert (result["failed"], result["changed"]) == (False, True), result.get("msg")


def test_a_move_forward_then_back(spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]) -> None:
    url, commits = source
    path = tmp_path / "spack"
    installed(spack, path, "v1.0.0", url)
    for old, new, shown in [("v1.0.0", "v1.2.0", "1.0.0 ("), ("v1.2.0", "v1.0.0", "1.2.0 (")]:
        moved = checkout(spack, version=new, path=str(path), source=url, move=True)
        assert moved["failed"] is False, moved.get("msg")
        assert (moved["changed"], moved["found"]) == (True, "spack")
        assert f"tag {old}" in moved["moved_from"]
        assert shown in moved["moved_from"]
        assert moved["spack_version"].startswith(new.removeprefix("v") + " ")
        assert head(path) == commits[new]
        assert git("status", "--porcelain", cwd=path) == ""
        assert moving_beside(path) == []
        again = checkout(spack, version=new, path=str(path), source=url, move=True)
        assert (again["failed"], again["changed"]) == (False, False), again.get("msg")
        assert "moved_from" not in again


def test_a_move_to_a_branch(spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]) -> None:
    url, commits = source
    path = tmp_path / "spack"
    installed(spack, path, "v1.0.0", url)
    moved = checkout(spack, version="releases/v1.2", path=str(path), source=url, move=True)
    assert (moved["failed"], moved["changed"]) == (False, True), moved.get("msg")
    assert git("symbolic-ref", "--short", "HEAD", cwd=path) == "releases/v1.2"
    assert head(path) == commits["releases/v1.2"]
    again = checkout(spack, version="releases/v1.2", path=str(path), source=url, move=True)
    assert (again["failed"], again["changed"]) == (False, False)


def test_a_move_to_a_commit(spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]) -> None:
    url, commits = source
    path = tmp_path / "spack"
    installed(spack, path, "v1.2.0", url)
    moved = checkout(spack, version=commits["v1.0.0"], path=str(path), source=url, move=True)
    assert (moved["failed"], moved["changed"]) == (False, True), moved.get("msg")
    assert head(path) == commits["v1.0.0"]
    again = checkout(spack, version=commits["v1.0.0"], path=str(path), source=url, move=True)
    assert (again["failed"], again["changed"]) == (False, False)


def test_a_move_from_another_source_makes_it_the_origin(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    path = tmp_path / "spack"
    installed(spack, path, "v1.0.0", source[0])
    second, commits = make_source(tmp_path / "second")
    moved = checkout(spack, version="v1.2.0", path=str(path), source=second, move=True)
    assert (moved["failed"], moved["changed"]) == (False, True), moved.get("msg")
    assert head(path) == commits["v1.2.0"]
    assert git("remote", "get-url", "origin", cwd=path) == second


def test_without_move_another_version_still_fails(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    path = tmp_path / "spack"
    installed(spack, path, "v1.0.0", source[0])
    result = checkout(spack, version="v1.2.0", path=str(path), source=source[0])
    assert result["failed"] is True
    assert "v1.2.0 was asked for" in result["msg"]
    assert "Nothing was changed" in result["msg"]
    assert head(path) == source[1]["v1.0.0"]


@pytest.mark.parametrize("version", ["v9.9.9", "v0.23.0"])
def test_a_move_that_cannot_be_made_leaves_the_spack_as_it_was(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]], version: str
) -> None:
    path = tmp_path / "spack"
    installed(spack, path, "v1.0.0", source[0])
    before = (head(path), git("tag", cwd=path), listing(path), objects(path))
    result = checkout(spack, version=version, path=str(path), source=source[0], move=True)
    assert result["failed"] is True
    assert ("not found" if version == "v9.9.9" else "needs Spack 1.0 or later") in result["msg"]
    assert (head(path), git("tag", cwd=path), listing(path), objects(path)) == before
    assert moving_beside(path) == []


def test_check_mode_reports_a_move_and_changes_nothing(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    path = tmp_path / "spack"
    installed(spack, path, "v1.0.0", source[0])
    before = (head(path), git("tag", cwd=path), listing(path), objects(path))
    recorder = Git(tmp_path)
    result = checkout(
        spack, check=True, task_env=recorder.env(spack), version="v1.2.0", path=str(path),
        source=source[0], move=True,
    )  # fmt: skip
    assert (result["failed"], result["changed"]) == (False, True), result.get("msg")
    assert "tag v1.0.0" in result["moved_from"]
    assert NOT_CHECKED in result["msg"]
    assert (head(path), git("tag", cwd=path), listing(path), objects(path)) == before
    assert moving_beside(path) == []
    assert set(recorder.subcommands) <= READS | {"tag"}, recorder.subcommands


def test_check_mode_with_move_over_a_spack_at_the_version_only_reads(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    path = tmp_path / "spack"
    installed(spack, path, "v1.2.0", source[0])
    recorder = Git(tmp_path)
    result = checkout(
        spack, check=True, task_env=recorder.env(spack), version="v1.2.0", path=str(path),
        source=source[0], move=True,
    )  # fmt: skip
    assert (result["failed"], result["changed"]) == (False, False), result.get("msg")
    assert set(recorder.subcommands) <= READS, recorder.subcommands


def test_move_over_what_is_not_a_git_repository_still_fails(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    path = not_a_spack(tmp_path, "a directory that is not a git repository")
    before = listing(path)
    result = checkout(spack, version="v1.2.0", path=str(path), source=source[0], move=True)
    assert result["failed"] is True
    assert "it is not a Spack. Nothing was changed" in result["msg"]
    assert listing(path) == before


def test_a_move_leaves_a_stale_move_directory_alone(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    path = tmp_path / "spack"
    installed(spack, path, "v1.0.0", source[0])
    stale = tmp_path / ".spack.move-old"
    stale.mkdir()
    (stale / "half").write_text("a move that was stopped\n")
    moved = checkout(spack, version="v1.2.0", path=str(path), source=source[0], move=True)
    assert (moved["failed"], moved["changed"]) == (False, True), moved.get("msg")
    assert (stale / "half").is_file()
    assert moving_beside(path) == [".spack.move-old"]


# Spec 005, User Story 2: what a site keeps in its Spack is not lost.


def test_a_move_keeps_the_sites_files(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]]
) -> None:
    path = tmp_path / "spack"
    installed(spack, path, "v1.0.0", source[0])
    kept = {
        "opt/built/package": "a package the old version built\n",
        "etc/site/packages.yaml": "packages: {}\n",
        "notes.txt": "a note of the site's\n",
        "bin/extra": "a tool of the site's\n",
    }
    for name, text in kept.items():
        (path / name).parent.mkdir(parents=True, exist_ok=True)
        (path / name).write_text(text)
    moved = checkout(spack, version="v1.2.0", path=str(path), source=source[0], move=True)
    assert (moved["failed"], moved["changed"]) == (False, True), moved.get("msg")
    assert {name: (path / name).read_text() for name in kept} == kept


@pytest.mark.parametrize("check", [False, True])
def test_a_move_over_edited_files_is_refused(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]], check: bool
) -> None:
    path = tmp_path / "spack"
    installed(spack, path, "v1.0.0", source[0])
    (path / "README.md").write_text("a site's fix to Spack's own file\n")
    result = checkout(spack, check=check, version="v1.2.0", path=str(path), source=source[0], move=True)
    assert result["failed"] is True
    assert "README.md" in result["msg"]
    assert "Nothing was changed" in result["msg"]
    assert head(path) == source[1]["v1.0.0"]
    assert (path / "README.md").read_text() == "a site's fix to Spack's own file\n"
    assert moving_beside(path) == []


@pytest.mark.parametrize("theirs", ["etc/site/README.md", "etc/site"])
def test_a_move_that_would_overwrite_a_sites_file_is_refused(
    spack: Spack, tmp_path: Path, source: tuple[str, dict[str, str]], theirs: str
) -> None:
    """Research R2: git would replace the site's file, ignored on v1.0.0 and tracked on v1.2.0."""
    path = tmp_path / "spack"
    installed(spack, path, "v1.0.0", source[0])
    mine = path / theirs
    mine.parent.mkdir(parents=True, exist_ok=True)
    mine.write_text("MY OWN\n")
    result = checkout(spack, version="v1.2.0", path=str(path), source=source[0], move=True)
    assert result["failed"] is True
    assert theirs in result["msg"]
    assert "move them aside" in result["msg"]
    assert mine.read_text() == "MY OWN\n"
    assert head(path) == source[1]["v1.0.0"]
    assert moving_beside(path) == []
