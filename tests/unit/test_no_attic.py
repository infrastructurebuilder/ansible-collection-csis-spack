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
