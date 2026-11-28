"""The plans retired before Spec Kit are in the specs, not in a directory of their own.

Spec 012 removed the ATTIC, the directory that held the plans made before
this repository adopted Spec Kit. Its content is in the specs 001 and 007 to
011, and specs/012-remove-attic/coverage/ records where each part of it
went.
"""

from __future__ import annotations

from runner import ROOT


def test_there_is_no_attic() -> None:
    assert not (ROOT / "ATTIC").exists()


def test_no_live_file_names_the_attic() -> None:
    """No rule, build file, comment or test points at the ATTIC.

    The specs and the changelog are left out: they are history, and they say
    where the ATTIC's content went (spec 012, User Story 1, scenario 2).
    """
    import subprocess

    found = subprocess.run(
        [
            "git",
            "grep",
            "-l",
            "-w",
            "ATTIC",
            "--",
            ".",
            ":!specs",
            ":!CHANGELOG.md",
            ":!tests/unit/test_no_attic.py",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert found.returncode in (0, 1), found.stderr
    assert found.stdout.split() == [], found.stdout
