# Copyright: Contributors to the infrastructurebuilder.csis_spack collection
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Run Spack for the modules of this collection, and read what it answers.

Spack is always run as a list of arguments, never through a shell, and with
its machine-readable output where it has one (``find --json``,
``buildcache check -o``, ``spack.lock``). Spack's Python internals are not
imported: they change between releases, and the command line is what the
modules depend on.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import hashlib
import json
import os
import re

MINIMUM_VERSION = (1, 0)

# The default module roots, as Spack's etc/spack/defaults/base/modules.yaml
# gives them; "$spack" is Spack's own directory.
DEFAULT_MODULE_ROOTS = {
    "tcl": "$spack/share/spack/modules",
    "lmod": "$spack/share/spack/lmod",
}

# Spack stamps every module file with the time it was written ("## Module
# file created by spack (...) on 2026-11-13 11:00:30.218360"); the line
# changes on every refresh, so it is left out when module trees are compared.
CREATED_ON = re.compile(rb"Module file created by spack .* on \d{4}-\d{2}-\d{2}[^\n]*")

# What the modules remember between runs is kept in files of their own in the
# environment's .spack-env directory. That directory is Spack's; Spack leaves
# files it does not know there alone, and removes them with the environment.
STATE_DIRECTORY = ".spack-env"


class SpackError(Exception):
    """Spack failed; the message carries the command and the end of its output."""


def file_digest(path):
    """Give the SHA-256 of a file, or None when it does not exist."""
    if not os.path.isfile(path):
        return None
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_digest(root, ignore=None):
    """Give one SHA-256 for every file under ``root``: names and contents.

    Text that ``ignore`` (a compiled bytes pattern) matches is left out of the
    contents.
    """
    digest = hashlib.sha256()
    if not os.path.isdir(root):
        return None
    for directory, subdirectories, files in os.walk(root):
        subdirectories.sort()
        for name in sorted(files):
            path = os.path.join(directory, name)
            with open(path, "rb") as handle:
                content = handle.read()
            if ignore is not None:
                content = ignore.sub(b"", content)
            digest.update(os.path.relpath(path, root).encode("utf-8"))
            digest.update(b"\0")
            digest.update(hashlib.sha256(content).hexdigest().encode("ascii"))
            digest.update(b"\0")
    return digest.hexdigest()


def module_tree_digest(root):
    """Give the digest of a module tree, leaving out the time each file was written."""
    return tree_digest(root, ignore=CREATED_ON)


def parse_version(text):
    """Read the version from the first line of ``spack --version``."""
    match = re.match(r"\s*(\d+)\.(\d+)(?:\.(\d+))?", text)
    if not match:
        raise SpackError("cannot read a version from 'spack --version': %r" % text.strip()[:200])
    return tuple(int(part) for part in match.groups(default="0"))


def data_digest(data):
    """Give the SHA-256 of a JSON-able value, whatever the order of its keys."""
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()


def read_state(env_path, name):
    """Read what a module remembered about an environment; None when there is nothing usable."""
    path = os.path.join(env_path, STATE_DIRECTORY, name)
    try:
        with open(path) as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def write_state(env_path, name, data):
    """Remember ``data`` about an environment, replacing the file in one step."""
    directory = os.path.join(env_path, STATE_DIRECTORY)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    path = os.path.join(directory, name)
    with open(path + ".tmp", "w") as handle:
        json.dump(data, handle, indent=1, sort_keys=True)
        handle.write("\n")
    os.replace(path + ".tmp", path)


def lock_specs(path):
    """Read an environment's spack.lock: (each concrete spec by hash, the root specs)."""
    lock = os.path.join(path, "spack.lock")
    if not os.path.isfile(lock):
        return {}, []
    with open(lock) as handle:
        data = json.load(handle)
    concrete = dict(data.get("concrete_specs", {}))
    roots = [{"spec": root.get("spec"), "hash": root.get("hash")} for root in data.get("roots", [])]
    return concrete, roots


def mirror_url(name_or_url, mirrors):
    """Turn a mirror's name, path or URL into a URL; ``mirrors`` maps names to URLs."""
    if "://" in name_or_url:
        return name_or_url
    if name_or_url.startswith(("/", ".", "~")):
        return "file://" + os.path.abspath(os.path.expanduser(name_or_url))
    if name_or_url in mirrors:
        return mirrors[name_or_url]
    raise SpackError(
        "no mirror named %r; Spack knows %s" % (name_or_url, ", ".join(sorted(mirrors)) or "none")
    )


def parse_mirror_list(output):
    """Read ``spack mirror list``: lines of name, flags in brackets, URL."""
    mirrors = {}
    for line in output.splitlines():
        match = re.match(r"^(\S+)\s+\[[^\]]*\]\s+(\S+)", line.strip())
        if match:
            mirrors[match.group(1)] = match.group(2)
    return mirrors


# Answering Spack's confirmations. Under Ansible, Spack has no terminal: a
# command that asks "[y/N]" reads end of file and fails. Many of Spack's
# commands take -y, --yes-to-all to answer for it, but which ones changes
# between versions (Spack 1.2.0 added it to "gpg trust" and "buildcache keys",
# together with their question; 1.0 and 1.1 have neither, and refuse the
# option), so the help of the Spack that is installed is read, and the option
# given only where it is listed. See specs/003-mirror-keys-yes-to-all.
YES_TO_ALL = "--yes-to-all"
YES_OPTION = re.compile(r"^\s+(?:-y, )?--yes-to-all\b", re.MULTILINE)
# A subcommand in a help: four spaces in, under "positional arguments:",
# with an alias in brackets ("    push (create)   create a binary ...").
SUBCOMMAND = re.compile(r"^    ([a-z][\w-]*)(?: \(([a-z][\w-]*)\))?(?:\s|$)")


def read_help(text):
    """Read a help: (whether it lists --yes-to-all, the names of its subcommands)."""
    subcommands = set()
    inside = False
    for line in text.splitlines():
        if line.startswith("positional arguments:"):
            inside = True
        elif line and not line[0].isspace():
            inside = False
        elif inside:
            match = SUBCOMMAND.match(line)
            if match:
                subcommands.update(name for name in match.groups() if name)
    return bool(YES_OPTION.search(text)), subcommands


class Spack:
    """One Spack executable, run on behalf of an AnsibleModule."""

    def __init__(self, module, executable, yes_to_all=False):
        self.module = module
        if os.sep in executable:
            self.executable = executable
        else:
            self.executable = module.get_bin_path(executable, required=True)
        self.calls = []
        self.yes_to_all = yes_to_all
        self.helps = {}

    def help(self, words):
        """Read ``spack <words> --help`` once: (takes --yes-to-all, subcommands).

        A help that fails, as for a command Spack does not know, takes nothing.
        """
        words = tuple(words)
        if words not in self.helps:
            try:
                text = self.run([*words, "--help"])
            except SpackError:
                text = ""
            self.helps[words] = read_help(text)
        return self.helps[words]

    def command_words(self, args):
        """Count the leading arguments that name the command, by walking its help.

        The first argument, then each next one while the help so far lists it
        as a subcommand. --help is only ever asked for after words known to be
        commands: after anything else (a spec, a path, a script for
        "spack python") it could reach that command's own arguments, or run it.
        The walk stops at the first option, so a subcommand written after an
        option of its parent ("config --scope user add") is not seen.
        """
        if not args or args[0].startswith("-"):
            return 0
        count = 1
        while count < len(args) and args[count] in self.help(args[:count])[1]:
            count += 1
        return count

    def answered(self, args, words=None, consent=False):
        """Give ``args`` with --yes-to-all after the command's words, where it belongs.

        It is added when the module was asked to answer (``yes_to_all``) or
        answers in any case (``consent``), the arguments do not answer already
        (-y, --yes-to-all), and the help of the command lists the option.
        ``words`` is how many of ``args`` name the command; without it, they
        are found by walking the help (command_words). Nothing is ever written
        to Spack's input.
        """
        args = list(args)
        if not (consent or self.yes_to_all) or "-y" in args or YES_TO_ALL in args:
            return args
        if words is None:
            words = self.command_words(args)
        if not words or not self.help(args[:words])[0]:
            return args
        return [*args[:words], YES_TO_ALL, *args[words:]]

    def run(self, args, env_path=None, log_file=None, ok=(0,)):
        """Run Spack with ``args`` (in the environment ``env_path``); return its output.

        An exit code outside ``ok`` is a failure, reported with the end of the output.
        """
        command = [self.executable]
        if env_path is not None:
            command += ["-e", env_path]
        command += list(args)
        self.calls.append(command)
        rc, out, err = self.module.run_command(command)
        if log_file:
            with open(log_file, "w") as handle:
                handle.write(out)
                handle.write(err)
        if rc not in ok:
            tail = "\n".join((out + err).splitlines()[-50:])
            raise SpackError("%s failed (exit %d):\n%s" % (" ".join(command), rc, tail))
        return out

    def version(self):
        return parse_version(self.run(["--version"]))

    def require_version(self):
        found = self.version()
        if found[:2] < MINIMUM_VERSION:
            raise SpackError(
                "Spack %s is too old: this collection needs Spack %d.%d or later"
                % (".".join(str(part) for part in found), MINIMUM_VERSION[0], MINIMUM_VERSION[1])
            )
        return found

    def installed(self, env_path):
        """Map each installed spec of the environment to its record, from ``find --json``."""
        out = self.run(["find", "--json"], env_path=env_path)
        records = json.loads(out) if out.strip() else []
        return {record["hash"]: record for record in records}

    def mirrors(self, env_path=None):
        return parse_mirror_list(self.run(["mirror", "list"], env_path=env_path))

    def modules_config(self, env_path):
        """Give the environment's ``modules`` configuration, every scope merged."""
        text = self.run(["config", "get", "--json", "modules"], env_path=env_path)
        return (json.loads(text) if text.strip() else {}).get("modules") or {}

    def module_roots(self, env_path, systems, config=None):
        """Give the module root of each module system, as the environment configures it."""
        if config is None:
            config = self.modules_config(env_path)
        roots = ((config.get("default") or {}).get("roots")) or {}
        spack_root = self.run(["location", "-r"]).strip()
        result = {}
        for system in systems:
            root = roots.get(system) or DEFAULT_MODULE_ROOTS[system]
            result[system] = os.path.expanduser(
                root.replace("$spack", spack_root).replace("${spack}", spack_root)
            )
        return result


# --- Configuration, as data -------------------------------------------------
#
# What follows plans changes to one section of one configuration scope. It was
# written to what Spack v1.2.0 does (tried by hand; see this repository's
# ATTIC/COLL-INPROGRESS/COLL-STAGE-2.md):
# "spack config add" replaces a scalar, but merges a list into the one that
# is there (new items in front, none twice), so a list can only be set
# exactly by removing its path first; "spack config remove" of a path that is
# not there succeeds; and removing the last key of a mapping leaves that
# mapping behind, empty ("install_tree: {}"), at every level (found by the
# Cloud Sandbox's stage 12; this code first assumed the opposite). So a
# removal that would empty a mapping removes the mapping itself, from the
# highest level it empties.


def is_branch(value):
    """Say whether a settings value is a mapping to walk into, not a value to set."""
    return isinstance(value, dict) and bool(value)


def path_text(keys):
    """Write a list of keys as the path "spack config" takes."""
    for key in keys:
        if ":" in str(key):
            raise SpackError("a configuration key cannot contain a colon: %r" % (key,))
    return ":".join(str(key) for key in keys)


def merged(current, desired):
    """Give ``current`` with ``desired`` laid over it: mappings merge, anything else is replaced."""
    result = dict(current)
    for key, value in desired.items():
        if is_branch(value) and isinstance(result.get(key), dict):
            result[key] = merged(result[key], value)
        else:
            result[key] = value
    return result


def nest(keys, value):
    """Give ``value`` wrapped in one mapping per key: nest(["a", "b"], 1) is {"a": {"b": 1}}."""
    for key in reversed(keys):
        value = {key: value}
    return value


def plan_merge(current, desired, prefix=()):
    """Plan making ``desired`` true inside ``current``, leaving every other key alone.

    Gives (removes, adds): the paths (as lists of keys) to remove first, and
    the (path, value) pairs to add afterwards.
    """
    removes, adds = [], []
    for key, value in desired.items():
        path = [*prefix, key]
        if key not in current:
            adds.append((path, value))
        elif is_branch(value) and isinstance(current[key], dict):
            more_removes, more_adds = plan_merge(current[key], value, path)
            removes += more_removes
            adds += more_adds
        elif current[key] != value:
            removes.append(path)
            adds.append((path, value))
    return removes, adds


def plan_replace(current, desired, prefix=()):
    """Plan making a section exactly ``desired``: (removes, adds) as for plan_merge."""
    removes = [[*prefix, key] for key in current if key not in desired or current[key] != desired[key]]
    adds = [([*prefix, key], value) for key, value in desired.items() if current.get(key) != value]
    return removes, adds


def plan_absent(current, unwanted, prefix=()):
    """List the paths to remove: every leaf of ``unwanted`` that ``current`` has.

    A removal that would leave a mapping empty removes that mapping instead,
    from the highest level it would empty, since Spack leaves emptied
    mappings behind. ``prefix`` is put in front of each path given back,
    and is not itself a candidate (it is the section).
    """
    leaves = plan_leaves(current, unwanted)
    return [[*prefix, *path] for path in highest_emptied(current, leaves)]


def plan_leaves(current, unwanted, prefix=()):
    """List every leaf of ``unwanted`` that ``current`` has, as paths of keys."""
    removes = []
    for key, value in unwanted.items():
        if key not in current:
            continue
        if is_branch(value) and isinstance(current[key], dict):
            removes += plan_leaves(current[key], value, [*prefix, key])
        else:
            removes.append([*prefix, key])
    return removes


def value_at(data, path):
    for key in path:
        if not isinstance(data, dict) or key not in data:
            return None
        data = data[key]
    return data


def highest_emptied(current, leaves):
    """Replace each leaf by the highest mapping above it that removing the leaves would empty.

    A mapping is emptied when everything in it is removed or emptied in turn,
    so the leaves are taken away with ``without``, which drops each mapping
    it empties, and each leaf is replaced by its shortest prefix that is gone.
    """
    after = current
    for path in leaves:
        after = without(after, path)
    chosen = []
    for path in leaves:
        target = path
        for length in range(1, len(path)):
            if value_at(after, path[:length]) is None:
                target = path[:length]
                break
        if target not in chosen:
            chosen.append(target)
    # A path under another chosen one goes with it.
    return [
        path for path in chosen if not any(path[: len(other)] == other and path != other for other in chosen)
    ]


def without(current, path):
    """Give ``current`` with ``path`` removed, and any mapping that leaves empty."""
    if not path or not isinstance(current, dict) or path[0] not in current:
        return current
    result = dict(current)
    if len(path) == 1:
        del result[path[0]]
    else:
        inner = without(result[path[0]], path[1:])
        if inner == {}:
            del result[path[0]]
        else:
            result[path[0]] = inner
    return result


def external_specs(packages):
    """List every external spec recorded in a ``packages`` section, sorted."""
    specs = []
    for entry in (packages or {}).values():
        if isinstance(entry, dict):
            specs += [external.get("spec") for external in entry.get("externals") or []]
    return sorted(spec for spec in specs if spec)


def spec_name_version(spec):
    """Split the front of a spec into its name and version: "gcc@14.3.1 languages:=c" is ("gcc", "14.3.1")."""
    front = re.split(r"[\s+~%^]", spec.strip(), maxsplit=1)[0]
    name, _at, version = front.partition("@")
    return name, version


def satisfies(recorded, required):
    """Say whether a recorded external spec is the package, and the version, that ``required`` names.

    A required version matches itself and anything more exact: "gcc@14"
    accepts gcc@14.3.1, and "gcc" accepts any gcc.
    """
    name, version = spec_name_version(recorded)
    wanted_name, wanted_version = spec_name_version(required)
    if name != wanted_name:
        return False
    return not wanted_version or version == wanted_version or version.startswith(wanted_version + ".")


FINGERPRINT = re.compile(r"fpr:+([0-9A-Fa-f]{40}):")


def fingerprints(colons):
    """Read the key fingerprints out of gpg's --with-colons output."""
    return sorted({match.upper() for match in FINGERPRINT.findall(colons)})


def mirror_record(entry):
    """Give a mirror's configuration as a mapping; Spack keeps a bare URL as a string."""
    return {"url": entry} if isinstance(entry, str) else dict(entry or {})


def scope_args(scope):
    return ["--scope", scope] if scope else []


class Configuration:
    """One configuration scope of one Spack, read and changed through ``spack config``."""

    def __init__(self, spack, scope):
        self.spack = spack
        self.scope = scope

    def get(self, section, merged_scopes=False):
        """Give one section: of this scope, or with every scope merged."""
        args = ["config", *([] if merged_scopes else scope_args(self.scope)), "get", "--json", section]
        try:
            text = self.spack.run(args)
        except SpackError as error:
            # A scope whose directory has not been made yet, such as the user
            # scope on a fresh machine, cannot be read; it holds nothing.
            # Writing to it makes it. (Spack v1.2.0's wording; a scope that
            # is not one at all is refused differently, and still fails.)
            if "must refer to an existing scope" in str(error):
                return {}
            raise
        return (json.loads(text) if text.strip() else {}).get(section) or {}

    def remove(self, path):
        self.spack.run(["config", *scope_args(self.scope), "remove", path_text(path)])

    def add(self, section, data):
        """Add ``data`` to a section, through a file: one section per file is what Spack takes."""
        import tempfile

        handle, name = tempfile.mkstemp(prefix="spack-config-", suffix=".json")
        try:
            with os.fdopen(handle, "w") as stream:
                json.dump({section: data}, stream)
            self.spack.run(["config", *scope_args(self.scope), "add", "-f", name])
        finally:
            os.unlink(name)
