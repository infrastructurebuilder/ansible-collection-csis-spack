"""The collection's metadata is complete and agrees with itself."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def galaxy() -> dict[str, object]:
    return yaml.safe_load((ROOT / "galaxy.yml").read_text())


def test_the_collection_is_infrastructurebuilder_csis_spack() -> None:
    meta = galaxy()
    assert (meta["namespace"], meta["name"]) == ("infrastructurebuilder", "csis_spack")


def test_the_version_is_semantic() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?", str(galaxy()["version"]))


def test_the_pyproject_carries_the_same_version() -> None:
    text = (ROOT / "pyproject.toml").read_text()
    assert f'version = "{galaxy()["version"]}"' in text


def test_the_licence_is_gpl3_or_later_and_its_text_is_here() -> None:
    assert galaxy()["license"] == ["GPL-3.0-or-later"]
    text = (ROOT / "LICENSE").read_text()
    assert "GNU GENERAL PUBLIC LICENSE" in text
    assert "Version 3, 29 June 2007" in text


def test_the_ansible_core_requirement_matches_the_tested_series() -> None:
    runtime = yaml.safe_load((ROOT / "meta" / "runtime.yml").read_text())
    assert runtime["requires_ansible"] == ">=2.16.0"
    assert '"ansible-core>=2.16,<2.17"' in (ROOT / "pyproject.toml").read_text()


def test_every_module_has_its_documentation() -> None:
    missing = [
        path.name
        for path in sorted((ROOT / "plugins" / "modules").glob("*.py"))
        if not all(block in path.read_text() for block in ("DOCUMENTATION", "EXAMPLES", "RETURN"))
    ]
    assert not missing, missing
