"""The collection knows how to do each kind of thing to Spack, and nothing about any site.

docs/examples/cloud-sandbox.yml is a real site's configuration. Nothing that
it names (a package, a compiler, a mirror, a path, a module) may appear in
the collection's plugins or in its role: that would be the site's knowledge,
built in.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from runner import ROOT

# Words of the example that are Spack's own or the collection's, not the site's.
NOT_THE_SITES = {"all", "site", "user", "tcl", "true", "false", "spack"}
# What the site names that the example's structure does not single out.
ALSO = ["oneapi", "x86_64_v3", "/save/", "rhel", "padded_length", "funcs-setup-instance"]


def site_names() -> list[str]:
    example = yaml.safe_load((ROOT / "docs" / "examples" / "cloud-sandbox.yml").read_text())
    names: set[str] = set(ALSO)
    for steps in (value for value in example.values() if isinstance(value, list)):
        for step in steps:
            packages: dict[str, Any] = (step.get("settings") or {}).get("packages") or {}
            names |= set(packages)
            for entry in packages.values():
                names |= {external["prefix"] for external in (entry or {}).get("externals", [])}
                for providers in ((entry or {}).get("providers") or {}).values():
                    names |= set(providers)
            if isinstance(step.get("externals"), list):
                names |= set(step["externals"])
            names |= {spec.split("@")[0] for spec in step.get("require", [])}
            if step["kind"] == "mirror":
                names |= {step["name"], step["url"]}
            if step["kind"] == "environment":
                names |= {word for word in step["shell"].split() if "/" in word}
    return sorted(names - NOT_THE_SITES)


def collection_files() -> list[Path]:
    return sorted(
        path
        for directory in ("plugins", "roles")
        for path in (ROOT / directory).rglob("*")
        if path.is_file() and path.suffix in (".py", ".yml", ".md", ".j2")
    )


def test_the_example_names_enough_to_make_this_a_test() -> None:
    names = site_names()
    for expected in [
        "cmake",
        "intel-oneapi-compilers",
        "intel-oneapi-mkl",
        "spack-public",
        "https://cache.spack.io",
    ]:
        assert expected in names


def test_nothing_the_site_names_is_in_the_plugins_or_the_role() -> None:
    files = collection_files()
    assert len(files) > 15
    found = [
        f"{path.relative_to(ROOT)}: {name}"
        for path in files
        for name in site_names()
        if name.lower() in path.read_text().lower()
    ]
    assert not found, found
