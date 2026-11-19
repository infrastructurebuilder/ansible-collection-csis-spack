"""Publishing to Galaxy refuses what it should, and keeps the key off the command line.

Nothing here reaches a network: the server and ``ansible-galaxy`` are stood in for.
"""

from __future__ import annotations

import re
import subprocess
import urllib.error
from email.message import Message
from pathlib import Path
from typing import Any

import pytest
import yaml
from publish import DEFAULT_SERVER, main, problems, published, upload_environment, version_url

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "publish.yml"
KEY = "not-a-real-key-0123"


def version() -> str:
    return str(yaml.safe_load((ROOT / "galaxy.yml").read_text())["version"])


class Recorder:
    """Stands in for subprocess.run, keeping what it was given."""

    def __init__(self, returncode: int = 0) -> None:
        self.calls: list[tuple[list[str], dict[str, str]]] = []
        self.returncode = returncode

    def __call__(self, command: list[str], env: dict[str, str], check: bool) -> Any:
        self.calls.append((command, env))
        return subprocess.CompletedProcess(command, self.returncode)


def run_main(
    tmp_path: Path,
    *,
    environ: dict[str, str] | None = None,
    tags: list[str] | None = None,
    clean: bool = True,
    on_server: bool = False,
    tarball: bool = True,
    returncode: int = 0,
) -> tuple[int, Recorder, list[str]]:
    path = tmp_path / "collection.tar.gz"
    if tarball:
        path.write_bytes(b"tarball")
    asked: list[str] = []
    recorder = Recorder(returncode)

    def is_published(url: str) -> bool:
        asked.append(url)
        return on_server

    code = main(
        [str(path)],
        environ={"GALAXY_API_KEY": KEY} if environ is None else environ,
        root=ROOT,
        state=lambda _root: ([version()] if tags is None else tags, clean),
        is_published=is_published,
        run=recorder,
    )
    return code, recorder, asked


def test_a_tagged_clean_checkout_with_a_key_may_be_published() -> None:
    assert problems("1.2.3", ["1.2.3"], True, KEY) == []


@pytest.mark.parametrize(
    ("tags", "clean", "key", "says"),
    [
        (["1.2.3"], True, None, "GALAXY_API_KEY is not set"),
        (["1.2.3"], True, "", "GALAXY_API_KEY is not set"),
        ([], True, KEY, "HEAD is not tagged 1.2.3"),
        (["v1.2.3"], True, KEY, "HEAD is not tagged 1.2.3"),
        (["1.2.3"], False, KEY, "the working tree has changes"),
    ],
)
def test_each_reason_to_refuse_is_given(tags: list[str], clean: bool, key: str | None, says: str) -> None:
    found = problems("1.2.3", tags, clean, key)
    assert len(found) == 1
    assert says in found[0]


def test_the_version_url_is_galaxys_published_index() -> None:
    assert version_url(DEFAULT_SERVER, "infrastructurebuilder", "csis_spack", "0.0.1") == (
        "https://galaxy.ansible.com/api/v3/plugin/ansible/content/published/collections/index/"
        "infrastructurebuilder/csis_spack/versions/0.0.1/"
    )
    assert version_url("https://hub.example.invalid/api", "a", "b", "1.0.0").startswith(
        "https://hub.example.invalid/api/v3/"
    )


class Answer:
    def __enter__(self) -> Answer:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def answering(code: int) -> Any:
    def opener(url: str) -> Answer:
        if code == 200:
            return Answer()
        raise urllib.error.HTTPError(url, code, "stand-in", Message(), None)

    return opener


def test_published_reads_200_as_there_and_404_as_not() -> None:
    assert published("https://x.invalid/", answering(200)) is True
    assert published("https://x.invalid/", answering(404)) is False


def test_published_fails_on_any_other_answer_rather_than_guess() -> None:
    with pytest.raises(urllib.error.HTTPError):
        published("https://x.invalid/", answering(500))


def test_it_uploads_with_the_key_in_the_environment_only(tmp_path: Path) -> None:
    code, recorder, asked = run_main(tmp_path)
    assert code == 0
    assert asked == [version_url(DEFAULT_SERVER, "infrastructurebuilder", "csis_spack", version())]
    ((command, env),) = recorder.calls
    assert command[:3] == ["ansible-galaxy", "collection", "publish"]
    assert KEY not in " ".join(command)
    assert env["ANSIBLE_GALAXY_SERVER_LIST"] == "release"
    assert env["ANSIBLE_GALAXY_SERVER_RELEASE_URL"] == DEFAULT_SERVER
    assert env["ANSIBLE_GALAXY_SERVER_RELEASE_TOKEN"] == KEY


def test_a_version_already_there_is_not_uploaded_again(tmp_path: Path, capsys: Any) -> None:
    code, recorder, asked = run_main(tmp_path, on_server=True)
    assert len(asked) == 1
    assert code == 0
    assert recorder.calls == []
    assert "already on" in capsys.readouterr().out


@pytest.mark.parametrize(
    "kwargs",
    [
        {"environ": {}},
        {"tags": []},
        {"clean": False},
        {"tarball": False},
    ],
)
def test_a_refusal_uploads_nothing_and_fails(tmp_path: Path, kwargs: dict[str, Any]) -> None:
    code, recorder, asked = run_main(tmp_path, **kwargs)
    assert code == 1
    assert recorder.calls == []
    assert asked == []


def test_another_server_can_be_named(tmp_path: Path) -> None:
    server = "https://hub.example.invalid/api/galaxy/"
    code, recorder, asked = run_main(tmp_path, environ={"GALAXY_API_KEY": KEY, "GALAXY_SERVER": server})
    assert asked[0].startswith("https://hub.example.invalid/api/galaxy/v3/")
    assert code == 0
    assert recorder.calls[0][1]["ANSIBLE_GALAXY_SERVER_RELEASE_URL"] == server


def test_a_failed_upload_fails(tmp_path: Path) -> None:
    code, recorder, asked = run_main(tmp_path, returncode=3)
    assert code == 3
    assert len(recorder.calls) == len(asked) == 1


def test_the_upload_environment_keeps_the_rest() -> None:
    env = upload_environment({"PATH": "/bin"}, DEFAULT_SERVER, KEY)
    assert env["PATH"] == "/bin"


def test_the_workflow_publishes_release_tags_with_the_secret() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text())
    # YAML 1.1 reads the key `on` as True.
    trigger = workflow.get("on", workflow.get(True))
    (pattern,) = trigger["push"]["tags"]
    # GitHub's filter `+` repeats the character before it, as in a regular expression.
    as_regex = pattern.replace(".", r"\.")
    assert re.fullmatch(as_regex, version())
    assert not re.fullmatch(as_regex, f"v{version()}")
    steps = workflow["jobs"]["publish"]["steps"]
    (step,) = [step for step in steps if step.get("run") == "just publish"]
    assert step["env"] == {"GALAXY_API_KEY": "${{ secrets.GALAXY_API_KEY }}"}
    runs = [step.get("run") for step in steps]
    assert runs.index("just test") < runs.index("just publish")


def test_the_release_tags_have_the_form_the_workflow_watches() -> None:
    tags = subprocess.run(
        ["git", "-C", str(ROOT), "tag"], check=True, capture_output=True, text=True
    ).stdout.split()
    # Every tag is a release, named by its bare version. There may be none yet:
    # the development tags were withdrawn on 2026-11-18, before 0.0.1 was cut.
    assert not [tag for tag in tags if not re.fullmatch(r"\d+\.\d+\.\d+", tag)]


def test_galaxy_yml_names_the_homepage_and_documentation() -> None:
    meta = yaml.safe_load((ROOT / "galaxy.yml").read_text())
    for field in ("repository", "homepage", "documentation", "issues"):
        assert str(meta[field]).startswith(
            "https://github.com/infrastructurebuilder/ansible-collection-csis-spack"
        ), field


def test_the_release_tools_are_not_in_the_tarball() -> None:
    ignored = yaml.safe_load((ROOT / "galaxy.yml").read_text())["build_ignore"]
    assert {"tools", ".github"} <= set(ignored)


def test_the_file_that_holds_the_key_is_kept_out_of_the_tarball_and_out_of_git() -> None:
    # The build reads the directory, not git: a file git ignores is still packed
    # unless build_ignore names it.
    ignored = yaml.safe_load((ROOT / "galaxy.yml").read_text())["build_ignore"]
    assert ".envrc" in ignored
    assert ".envrc" in (ROOT / ".gitignore").read_text().split()
