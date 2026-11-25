"""A stand-in for the ``spack`` command, for the unit tests.

It answers the commands the modules run, the way Spack v1.2.0 answers them
(see tests/integration, which runs the same modules against the real Spack),
from a JSON state file named by FAKE_SPACK_STATE, and records every call in
that file. ``<command> --help`` prints the text the real Spack printed for
it, kept in fake_spack_help.json.

State keys:
  version          what ``spack --version`` prints
  root             what ``spack location -r`` prints
  lock             the spack.lock that ``concretize`` writes
  installed        hashes installed so far
  mirrors          {name: url}, for ``mirror list``
  mirror_contents  hashes the mirror has
  module_text      the text written into each module file
  module_roots     {system: root}, for ``config get --json modules``; empty: Spack's defaults
  modules_config   more keys of modules:default; "suffix" is added to each module file's name
  push_format      "other": ``buildcache push`` words its messages as no Spack does today
  overwritten      hashes that a push with --force replaced on the mirror, in order
  fail             {"<subcommand>": true}: that subcommand fails
  version          also the version the stand-in plays: "1.0..." and "1.1..." make the
                   commands that differ behave as in those versions (fake_spack_setup.py)
  (and those of fake_spack_setup.py, for configuration, mirrors, keys and detection)
  calls            every argument list the fake was run with
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fake_spack_setup

PUSH_FLAGS_WITH_VALUES = {"--key", "-k", "--only"}


def load() -> tuple[Path, dict[str, Any]]:
    path = Path(os.environ["FAKE_SPACK_STATE"])
    return path, json.loads(path.read_text())


def save(path: Path, state: dict[str, Any]) -> None:
    path.write_text(json.dumps(state, indent=1, sort_keys=True))


def env_lock(env: str) -> dict[str, Any]:
    lock = Path(env) / "spack.lock"
    return json.loads(lock.read_text()) if lock.is_file() else {"roots": [], "concrete_specs": {}}


def built(lock: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """The lock's specs that Spack builds: everything but the externals."""
    return {digest: spec for digest, spec in lock["concrete_specs"].items() if "external" not in spec}


def fail(state: dict[str, Any], what: str) -> None:
    if state.get("fail", {}).get(what):
        print(f"==> Error: {what} failed on purpose", file=sys.stderr)
        sys.exit(1)


HELP = json.loads((Path(__file__).resolve().parent / "fake_spack_help.json").read_text())


def help_text(state: dict[str, Any], words: list[str]) -> int:
    """Print ``spack <words> --help`` as the real Spack printed it (fake_spack_help.json)."""
    text = HELP["v1.2.0"].get(" ".join(words))
    if text is None:
        print(
            f"==> Error: {words[0] if words else ''} is not a recognized Spack command or extension "
            "command; check with `spack commands`.",
            file=sys.stderr,
        )
        return 1
    print(text, end="")
    return 0


def config_get_for(code: str) -> list[str]:
    """The "config get --json" that the module's "spack python -c" stands for (spack.py's CONFIG_*)."""
    scoped = re.search(r"get_config\('([\w-]+)', scope='([^']+)'\)", code)
    if scoped:
        return ["config", "--scope", scoped.group(2), "get", "--json", scoped.group(1)]
    merged = re.search(r"spack\.config\.get\('([\w-]+)'\)", code)
    assert merged, f"the stand-in does not know this Python: {code!r}"
    return ["config", "get", "--json", merged.group(1)]


def main(argv: list[str]) -> int:
    path, state = load()
    state.setdefault("calls", []).append(argv)
    save(path, state)
    if argv[-1:] == ["--help"]:
        return help_text(state, argv[:-1])
    if argv[:1] == ["-e"]:
        env_args, rest = argv[:2], argv[2:]
    else:
        env_args, rest = [], argv
    if rest[:2] == ["python", "-c"]:
        # Spack 1.0's way to configuration as JSON, read as the "config get --json" it stands for.
        argv = env_args + config_get_for(rest[2])
    elif "--json" in rest and rest[:1] == ["config"] and fake_spack_setup.playing(state) < (1, 1):
        print("==> Error: unrecognized arguments: --json", file=sys.stderr)
        return 1
    env = None
    if argv[:1] == ["-e"]:
        env, argv = argv[1], argv[2:]

    if env is None:
        # Configuration, mirrors, keys and detection: fake_spack_setup.py.
        answered = fake_spack_setup.handle(state, argv)
        if answered is not None:
            save(path, state)
            return answered

    if argv == ["--version"]:
        print(state.get("version", "1.2.0 (63962ed90680d339004305075da272ae93c04a41)"))
    elif argv == ["location", "-r"]:
        print(state["root"])
    elif argv[:1] == ["gc"]:
        # Spack asks before removing anything, unless given --yes-to-all.
        print("==> There are no unused specs. Spack's store is clean.")
    elif argv[:1] == ["concretize"] and env:
        fail(state, "concretize")
        (Path(env) / "spack.lock").write_text(json.dumps(state["lock"], indent=1, sort_keys=True))
    elif argv[:2] == ["find", "--json"] and env:
        lock = env_lock(env)
        installed = set(state.get("installed", []))
        records = [
            {
                "name": spec["name"],
                "hash": digest,
                **({"external": spec["external"]} if "external" in spec else {}),
            }
            for digest, spec in lock["concrete_specs"].items()
            if digest in installed or "external" in spec
        ]
        print(json.dumps(records))
    elif argv[:1] == ["install"] and env:
        fail(state, "install")
        installed = state.setdefault("installed", [])
        for digest, spec in built(env_lock(env)).items():
            if digest not in installed:
                print(f"[+] {digest[:7]} {spec['name']}")
                installed.append(digest)
        save(path, state)
    elif argv[:1] == ["module"] and argv[2:3] == ["refresh"] and env:
        fail(state, "module")
        system = argv[1]
        default_root = f"{state['root']}/share/spack/{'modules' if system == 'tcl' else system}"
        root = Path(state.get("module_roots", {}).get(system) or default_root)
        if "--delete-tree" in argv:
            shutil.rmtree(root, ignore_errors=True)
        root.mkdir(parents=True, exist_ok=True)
        installed = set(state.get("installed", []))
        for digest, spec in built(env_lock(env)).items():
            if digest in installed:
                # Spack stamps each file with the time it was written.
                stamp = (
                    f"## Module file created by spack (https://github.com/spack/spack) on {datetime.now()}\n"
                )
                text = state.get("module_text", "#%Module1.0\n")
                suffix = state.get("modules_config", {}).get("suffix", "")
                (root / f"{spec['name']}-{digest[:7]}{suffix}").write_text(text + stamp)
    elif argv == ["config", "get", "--json", "modules"]:
        # Every scope merged, as Spack prints it: its own default roots unless configured.
        roots = {"tcl": "$spack/share/spack/modules", "lmod": "$spack/share/spack/lmod"}
        roots |= state.get("module_roots", {})
        default = {"enable": ["tcl"], "roots": roots} | state.get("modules_config", {})
        print(json.dumps({"modules": {"default": default}}))
    elif argv == ["mirror", "list"]:
        for name, url in state.get("mirrors", {}).items():
            print(f"{name:<12} [sb] {url}")
    elif argv[:2] == ["buildcache", "push"] and env:
        fail(state, "push")
        options, positional = argv[2:], []
        skip = False
        flags = set()
        only = None
        for index, arg in enumerate(options):
            if skip:
                skip = False
                continue
            if arg in PUSH_FLAGS_WITH_VALUES:
                if arg == "--only":
                    only = options[index + 1]
                skip = True
            elif arg.startswith("-"):
                flags.add(arg)
            else:
                positional.append(arg)
        lock = env_lock(env)
        roots = {root["hash"] for root in lock["roots"]}
        installed = set(state.get("installed", []))
        candidates = {d: s for d, s in built(lock).items() if d in installed}
        # The mirror comes first. Specs given after it, as /<hash>, are what is
        # pushed, and "--only package" then means those and not their
        # dependencies (tried with Spack v1.2.0, for a root and for a dependency).
        mirror, chosen = positional[0], [spec.lstrip("/") for spec in positional[1:]]
        if chosen:
            assert only == "package", "the stand-in knows chosen specs only with --only package"
            candidates = {d: s for d, s in candidates.items() if any(d.startswith(c) for c in chosen)}
        elif only == "package":
            candidates = {d: s for d, s in candidates.items() if d in roots}
        elif only == "dependencies":
            candidates = {d: s for d, s in candidates.items() if d not in roots}
        contents = state.setdefault("mirror_contents", [])
        todo = sorted(d for d in candidates if "--force" in flags or d not in contents)
        state["last_push"] = {"mirror": mirror, "flags": sorted(flags), "only": only}
        # A later Spack may word its messages differently; "other" stands for that.
        other = state.get("push_format") == "other"
        if not todo and not other:
            print(f"==> Selected {len(candidates)} specs to push to {mirror}")
            print("==> All specs are already in the buildcache. Use --force to overwrite them.")
        for number, digest in enumerate(todo, start=1):
            if other:
                print(f"uploaded {candidates[digest]['name']} ({number} of {len(todo)})")
            else:
                print(f"==> [{number}/{len(todo)}] Pushed {candidates[digest]['name']}@1.0/{digest[:7]}")
            if digest in contents:
                state.setdefault("overwritten", []).append(digest)
            else:
                contents.append(digest)
        save(path, state)
    elif argv[:2] == ["buildcache", "check"] and env:
        url = argv[argv.index("-m") + 1]
        out = argv[argv.index("-o") + 1]
        contents = set(state.get("mirror_contents", []))
        lock = env_lock(env)
        rebuild = [
            {"short_spec": spec["name"], "hash": digest}
            for digest, spec in lock["concrete_specs"].items()
            if digest not in contents
        ]
        Path(out).write_text(json.dumps({url: {"mirrorUrl": url, "rebuildSpecs": rebuild}}))
        return 1 if rebuild else 0
    else:
        print(f"fake spack: not understood: {argv}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
