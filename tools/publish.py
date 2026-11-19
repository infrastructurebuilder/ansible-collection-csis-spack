"""Upload the release tarball to Ansible Galaxy: what ``just publish`` runs.

It runs the same way on the operator's machine and in the GitHub Actions
workflow ``.github/workflows/publish.yml``. It refuses to upload:

- without ``GALAXY_API_KEY`` in the environment. The key is never read from a
  file, and is handed to ``ansible-galaxy`` in its environment, not on its
  command line, so it does not show in the process list;
- unless HEAD is tagged with galaxy.yml's version (as ``0.0.1``, the form of
  this repository's tags) and the working tree is clean, so that what is
  uploaded is what was released;
- a version the server already has. It says so and exits 0 without uploading,
  so a version published from one place and then from the other is harmless.
  Galaxy keeps every version for good, so a number is never reused.

``GALAXY_SERVER`` names another server with Galaxy's API, such as a private
Automation Hub (default: galaxy.ansible.com).
"""

from __future__ import annotations

import os
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import yaml

DEFAULT_SERVER = "https://galaxy.ansible.com/api/"
KEY_VARIABLE = "GALAXY_API_KEY"


def metadata(root: Path) -> tuple[str, str, str]:
    """Return galaxy.yml's namespace, name and version."""
    meta = yaml.safe_load((root / "galaxy.yml").read_text())
    return str(meta["namespace"]), str(meta["name"]), str(meta["version"])


def problems(version: str, tags_at_head: list[str], clean: bool, key: str | None) -> list[str]:
    """Say why this checkout must not be published; empty when it may be."""
    found = []
    if not key:
        found.append(f"{KEY_VARIABLE} is not set: nothing is published without the operator's key")
    if version not in tags_at_head:
        found.append(
            f"HEAD is not tagged {version}: cut the release (just release, then the tag) "
            f"and publish from the tag"
        )
    if not clean:
        found.append("the working tree has changes: publish from a clean checkout of the tag")
    return found


def version_url(server: str, namespace: str, name: str, version: str) -> str:
    """The URL of one version of a collection in Galaxy's API."""
    return (
        f"{server.rstrip('/')}/v3/plugin/ansible/content/published/collections/index/"
        f"{namespace}/{name}/versions/{version}/"
    )


Opener = Callable[[str], Any]


def published(url: str, opener: Opener = urllib.request.urlopen) -> bool:
    """Say whether the server has this version: 200 yes, 404 no, anything else fails."""
    try:
        with opener(url):
            return True
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return False
        raise


def git_state(root: Path) -> tuple[list[str], bool]:
    """Return the tags at HEAD, and whether the working tree is clean."""

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
        ).stdout

    return git("tag", "--points-at", "HEAD").split(), not git("status", "--porcelain").strip()


def upload_environment(environ: Mapping[str, str], server: str, key: str) -> dict[str, str]:
    """ansible-galaxy's configuration for one server, the key in it, from the environment only."""
    return {
        **environ,
        "ANSIBLE_GALAXY_SERVER_LIST": "release",
        "ANSIBLE_GALAXY_SERVER_RELEASE_URL": server,
        "ANSIBLE_GALAXY_SERVER_RELEASE_TOKEN": key,
    }


def main(
    argv: list[str],
    environ: Mapping[str, str] | None = None,
    root: Path | None = None,
    state: Callable[[Path], tuple[list[str], bool]] = git_state,
    is_published: Callable[[str], bool] = published,
    run: Callable[..., Any] = subprocess.run,
) -> int:
    if len(argv) != 1:
        print("usage: publish.py <tarball>", file=sys.stderr)
        return 2
    tarball = argv[0]
    root = root or Path.cwd()
    environ = os.environ if environ is None else environ
    namespace, name, version = metadata(root)
    server = environ.get("GALAXY_SERVER") or DEFAULT_SERVER
    key = environ.get(KEY_VARIABLE)
    tags, clean = state(root)

    refused = problems(version, tags, clean, key)
    if refused:
        for problem in refused:
            print(f"not published: {problem}", file=sys.stderr)
        return 1
    if not Path(tarball).is_file():
        print(f"not published: {tarball} does not exist", file=sys.stderr)
        return 1
    if is_published(version_url(server, namespace, name, version)):
        print(f"{namespace}.{name} {version} is already on {server}: nothing uploaded")
        return 0

    assert key is not None  # problems() refused an empty key
    print(f"publishing {tarball} to {server}")
    result = run(
        ["ansible-galaxy", "collection", "publish", tarball],
        env=upload_environment(environ, server, key),
        check=False,
    )
    return int(result.returncode)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
