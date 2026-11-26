"""A git repository to install Spack from, made in a test, with real ``git``.

It stands for Spack's own repository: commits tagged ``v0.23.0``, ``v1.0.0``
and ``v1.2.0`` (the last an annotated tag, as a release may be), and a branch
``releases/v1.2`` with one commit more. At each commit ``bin/spack`` answers
``--version`` the way the real one does (research.md R5): its version, then
a commit's hash in brackets. With ``runs``, ``bin/spack`` instead runs the
stand-in ``spack`` with its arguments, so that a role test's later steps have
a Spack to work on; with ``mark`` as well, it first touches that file, so a
test can tell it was run.
"""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

# Whatever the machine's own git configuration says (signing, hooks, a
# default branch), these repositories are made the same way.
GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.org",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.org",
}
RELEASES = [("v0.23.0", "0.23.0"), ("v1.0.0", "1.0.0"), ("v1.2.0", "1.2.0")]
BRANCH = ("releases/v1.2", "1.2.1.dev0")
# What a real checkout prints after the version; any 40 hex digits will do.
SHOWN_HASH = "63962ed90680d339004305075da272ae93c04a41"


def git(*args: str, cwd: Path | None = None) -> str:
    """Run git with ``args`` and give what it printed."""
    done = subprocess.run(
        ["git", *args], cwd=cwd, env=os.environ | GIT_ENV, capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def program(version: str, runs: Path | None, mark: Path | None) -> str:
    if runs is not None:
        touch = f"touch {shlex.quote(str(mark))}\n" if mark is not None else ""
        return f'#!/bin/sh\n{touch}exec {shlex.quote(str(runs))} "$@"\n'
    return (
        "#!/bin/sh\n"
        f'if [ "$1" = "--version" ]; then echo "{version} ({SHOWN_HASH})"; exit 0; fi\n'
        f'echo "==> Error: this stand-in Spack {version} answers only --version" >&2\n'
        "exit 1\n"
    )


def make_source(
    directory: Path, *, runs: Path | None = None, mark: Path | None = None
) -> tuple[str, dict[str, str]]:
    """Make the repository under ``directory``; give its ``file://`` address and each version's commit."""
    repo = directory / "spack-source"
    (repo / "bin").mkdir(parents=True)
    git("init", "--quiet", "--initial-branch", "develop", str(repo))
    commits: dict[str, str] = {}

    def commit(version: str) -> str:
        spack = repo / "bin" / "spack"
        spack.write_text(program(version, runs, mark))
        spack.chmod(0o755)
        (repo / "README.md").write_text(f"Spack {version}, as a test makes it.\n")
        git("add", "--all", cwd=repo)
        git("commit", "--quiet", "--message", f"Spack {version}", cwd=repo)
        return git("rev-parse", "HEAD", cwd=repo)

    for tag, version in RELEASES:
        commits[tag] = commit(version)
        if tag == "v1.2.0":
            git("tag", "--annotate", "--message", f"Spack {version}", tag, cwd=repo)
        else:
            git("tag", tag, cwd=repo)
    git("checkout", "--quiet", "-b", BRANCH[0], cwd=repo)
    commits[BRANCH[0]] = commit(BRANCH[1])
    git("checkout", "--quiet", "develop", cwd=repo)
    return repo.as_uri(), commits
