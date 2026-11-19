"""The stand-in ``spack``'s configuration, mirrors, keys and detection.

Written to what Spack v1.2.0 does, as tried by hand (see
ATTIC/COLL-INPROGRESS/COLL-STAGE-2.md):

- ``config add -f`` takes one section per file, replaces a scalar, and merges
  a list into the one that is there, new items in front and none twice;
- ``config remove`` succeeds for a path that is not there, and leaves a
  mapping it empties behind, empty, at every level;
- a mirror added with no flags is kept as a bare URL, with flags as a mapping;
- detection only ever adds, says nothing when it finds nothing, and writes the
  ``packages`` section back in another order each time;
- ``gpg trust`` of a file that holds no key prints an error and exits 0.

State keys used here:
  scopes       {scope: {section: data}}
  machine      {"compilers": [...], "externals": [...]}; each entry has
               "package", "spec", and optionally "needs" (an environment
               variable that must be set for it to be seen), "path" (seen only
               when that directory is searched) and, for externals, "default"
               (part of what ``external find`` looks for unasked)
  detections   how many times detection has run
  trusted      fingerprints Spack trusts
  mirror_keys  {mirror name: [fingerprints it publishes]}
  unmade_scopes  scopes whose directory does not exist until something is written
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

SCOPE_ORDER = ["defaults", "system", "site", "user"]
SECTIONS = {"config", "concretizer", "mirrors", "modules", "packages", "repos"}
KEY_LINE = "FAKE-PUBLIC-KEY "


def error(message: str, code: int = 1) -> int:
    print(f"==> Error: {message}", file=sys.stderr)
    return code


def take_scope(argv: list[str]) -> tuple[str | None, list[str]]:
    if "--scope" in argv:
        at = argv.index("--scope")
        return argv[at + 1], argv[:at] + argv[at + 2 :]
    return None, argv


def section(state: dict[str, Any], scope: str, name: str) -> dict[str, Any]:
    return state.setdefault("scopes", {}).setdefault(scope, {}).setdefault(name, {})


def add_into(current: dict[str, Any], new: dict[str, Any]) -> None:
    """Merge as ``spack config add`` does."""
    for key, value in new.items():
        if isinstance(value, dict) and isinstance(current.get(key), dict):
            add_into(current[key], value)
        elif isinstance(value, list) and isinstance(current.get(key), list):
            current[key] = [item for item in value if item not in current[key]] + current[key]
        else:
            current[key] = value


def overlay(low: Any, high: Any) -> Any:
    """Merge two scopes' values, the higher scope winning."""
    if isinstance(low, dict) and isinstance(high, dict):
        result = dict(low)
        for key, value in high.items():
            result[key] = overlay(low[key], value) if key in low else value
        return result
    if isinstance(low, list) and isinstance(high, list):
        return high + [item for item in low if item not in high]
    return high


def merged_section(state: dict[str, Any], name: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for scope in SCOPE_ORDER:
        result = overlay(result, state.get("scopes", {}).get(scope, {}).get(name, {}))
    return result


def valid(name: str, data: dict[str, Any]) -> str | None:
    """Stand in for Spack's schema: enough of it to refuse something."""
    if name not in SECTIONS:
        return f"Additional properties are not allowed ('{name}' was unexpected)"
    if name == "packages":
        for package, entry in data.items():
            if isinstance(entry, dict) and "buildable" in entry and not isinstance(entry["buildable"], bool):
                return f"{entry['buildable']!r} is not of type 'boolean' (packages:{package}:buildable)"
    return None


def remove_path(data: dict[str, Any], keys: list[str]) -> None:
    """Remove as Spack v1.2.0 does: the mappings the removal empties stay, empty."""
    if keys[0] not in data:
        return
    if len(keys) == 1:
        del data[keys[0]]
        return
    if isinstance(data[keys[0]], dict):
        remove_path(data[keys[0]], keys[1:])


def literal(text: str) -> Any:
    """Read the value at the end of a ``config add`` path."""
    if text.startswith("[") and text.endswith("]"):
        return [literal(item.strip()) for item in text[1:-1].split(",") if item.strip()]
    if text in ("true", "false"):
        return text == "true"
    return int(text) if text.isdigit() else text.strip("'\"")


def all_externals(state: dict[str, Any]) -> set[str]:
    return {
        external["spec"]
        for entry in merged_section(state, "packages").values()
        if isinstance(entry, dict)
        for external in entry.get("externals", [])
    }


def seen(entry: dict[str, Any], paths: list[str]) -> bool:
    """Say whether detection, searching ``paths`` or PATH, sees this thing of the machine."""
    if entry.get("needs") and not os.environ.get(entry["needs"]):
        return False
    return entry.get("path") in paths if paths else not entry.get("path")


def record(
    state: dict[str, Any], scope: str, found: list[dict[str, Any]], not_buildable: bool = False
) -> int:
    packages = section(state, scope, "packages")
    known = all_externals(state)
    added = 0
    for entry in found:
        if entry["spec"] not in known:
            package = packages.setdefault(entry["package"], {})
            package.setdefault("externals", []).append({"spec": entry["spec"], "prefix": "/usr"})
            added += 1
        if not_buildable:
            packages.setdefault(entry["package"], {})["buildable"] = False
    state["detections"] = state.get("detections", 0) + 1
    return added


def mirror_table(state: dict[str, Any]) -> dict[str, Any]:
    return merged_section(state, "mirrors") | state.get("mirrors", {})


def handle(state: dict[str, Any], argv: list[str]) -> int | None:
    """Answer a configuration, mirror, key or detection command; None when it is not one."""
    scope, args = take_scope(argv)
    if args[:1] == ["config"] and state.get("fail", {}).get("config"):
        return error("config failed on purpose", 2)

    if args[:3] == ["config", "get", "--json"] and len(args) == 4:
        name = args[3]
        if scope in state.get("unmade_scopes", []) and scope not in state.get("scopes", {}):
            # As Spack v1.2.0, for a scope whose directory does not exist yet.
            return error(f"the argument --scope={scope} must refer to an existing scope", 2)
        data = (
            merged_section(state, name)
            if scope is None
            else state.get("scopes", {}).get(scope, {}).get(name, {})
        )
        if name == "packages" and state.get("detections", 0) % 2:
            # Spack writes this section back in another order after detecting.
            data = dict(reversed(list(data.items())))
        print(json.dumps({name: data}))
        return 0
    if args[:3] == ["config", "add", "-f"] and scope:
        new = json.loads(Path(args[3]).read_text())
        if len(new) != 1:
            return error(f"{args[3]}:1: Additional properties are not allowed")
        ((name, data),) = new.items()
        problem = valid(name, data)
        if problem:
            return error(f"{args[3]}:1: {problem}")
        add_into(section(state, scope, name), data)
        return 0
    if args[:2] == ["config", "add"] and len(args) == 3:
        # Without --scope, Spack writes to the user scope.
        scope = scope or "user"
        *keys, value = args[2].split(":")
        data: Any = literal(value)
        for key in reversed(keys[1:]):
            data = {key: data}
        add_into(section(state, scope, keys[0]), data)
        return 0
    if args[:2] == ["config", "remove"] and scope:
        name, *keys = args[2].split(":")
        if keys:
            remove_path(section(state, scope, name), keys)
        return 0

    if args[:2] == ["compiler", "find"] and scope:
        paths = args[2:]
        found = [entry for entry in state.get("machine", {}).get("compilers", []) if seen(entry, paths)]
        added = record(state, scope, found)
        print(f"==> Added {added} new compilers" if added else "==> Found no new compilers")
        return 0
    if args[:2] == ["external", "find"] and scope:
        rest, names, exclude, paths, not_buildable = args[2:], [], [], [], False
        while rest:
            arg = rest.pop(0)
            if arg == "--not-buildable":
                not_buildable = True
            elif arg == "--exclude":
                exclude.append(rest.pop(0))
            elif arg == "-p":
                paths.append(rest.pop(0))
            else:
                names.append(arg)
        found = [
            entry
            for entry in state.get("machine", {}).get("externals", [])
            if seen(entry, paths)
            and (entry["package"] in names if names else entry.get("default", True))
            and entry["package"] not in exclude
        ]
        added = record(state, scope, found, not_buildable)
        print(
            f"==> The following specs have been detected ({added})"
            if added
            else "==> No new external packages detected"
        )
        return 0

    if args[:2] == ["mirror", "add"] and scope:
        rest, kinds, signed = args[2:], [], None
        while rest and rest[0].startswith("--"):
            flag = rest.pop(0)
            if flag == "--type":
                kinds.append(rest.pop(0))
            else:
                signed = flag == "--signed"
        name, url = rest
        mirrors = section(state, scope, "mirrors")
        if name in mirrors:
            return error(f"Mirror with name {name} already exists.")
        entry: Any = {"url": url}
        if kinds:
            entry |= {"binary": "binary" in kinds, "source": "source" in kinds}
        if signed is not None:
            entry["signed"] = signed
        mirrors[name] = url if entry == {"url": url} else entry
        return 0
    if args[:2] == ["mirror", "remove"] and scope:
        mirrors = section(state, scope, "mirrors")
        if args[2] not in mirrors:
            return error(f"No mirror with name {args[2]} in {scope} scope")
        del mirrors[args[2]]
        return 0
    if args == ["mirror", "list"]:
        for name, entry in mirror_table(state).items():
            print(f"{name:<12} [sb] {entry if isinstance(entry, str) else entry['url']}")
        return 0

    if args == ["gpg", "list", "--trusted", "--fmt", "colons"]:
        print("==> Trusted keys")
        for fingerprint in state.get("trusted", []):
            print(f"pub:-:2048:1:{fingerprint[-16:]}:1794662619:::-:::cs::::::23::0:")
            print(f"fpr:::::::::{fingerprint}:")
        return 0
    if args[:3] == ["gpg", "trust", "-y"]:
        if state.get("fail", {}).get("trust"):
            return error("trust failed on purpose")
        text = Path(args[3]).read_text() if Path(args[3]).is_file() else ""
        keys = [line[len(KEY_LINE) :].strip() for line in text.splitlines() if line.startswith(KEY_LINE)]
        if not keys:
            # As Spack v1.2.0: an error is printed, and the exit code is 0.
            print("gpg: no valid OpenPGP data found.", file=sys.stderr)
        trusted = state.setdefault("trusted", [])
        trusted += [key for key in keys if key not in trusted]
        return 0
    if args == ["buildcache", "keys", "--install", "--trust"]:
        binary = [
            name
            for name, entry in mirror_table(state).items()
            if isinstance(entry, str) or entry.get("binary", True)
        ]
        if not binary:
            return error("Please add a spack mirror to allow download of build caches.")
        trusted = state.setdefault("trusted", [])
        for name in binary:
            trusted += [key for key in state.get("mirror_keys", {}).get(name, []) if key not in trusted]
        return 0

    if args in (["gpg", "init"], ["gpg", "list"]) or args[:2] in (
        ["buildcache", "update-index"],
        ["buildcache", "list"],
    ):
        if state.get("fail", {}).get(args[0]):
            return error(f"{' '.join(args)} failed on purpose")
        print(f"ran: {' '.join(args)}")
        return 0
    return None
