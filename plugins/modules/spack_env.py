#!/usr/bin/python
# Copyright: Contributors to the infrastructurebuilder.csis_spack collection
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: spack_env
short_description: Concretize and install a Spack environment, and regenerate its module files
version_added: 0.0.1
description:
  - Brings an existing Spack environment to a state. The environment's
    C(spack.yaml) is not this module's business; write it with
    M(ansible.builtin.template).
  - Concretizes the environment (C(spack concretize --force)), then, for
    I(state=installed), installs it (C(spack install)), then regenerates the
    module files of each system in I(modules).
  - Reports each kind of change on its own. C(spack.lock) changing is
    I(concretized); a spec being installed is I(installed); module files
    changing is I(modules_refreshed).
  - Module files are regenerated only when they need to be, unless
    I(refresh_modules=always). The module remembers what it regenerated them
    from in a file of its own, C(.spack-env/csis_spack.modules.json) in the
    environment's directory.
  - In check mode a copy of the environment is concretized in a temporary
    directory. The result says whether C(spack.lock) would change and which
    of its specs are not installed. Nothing is installed, and the environment
    itself is not touched. Module files are reported as changing only when
    that is certain, when a root is missing or a file was changed by hand.
  - In check mode, paths that C(spack.yaml) gives relatively, in C(include:)
    and in C(develop:), are read where they are, also above the environment's
    directory; the preview records the same develop paths a real run would.
    A develop source above the environment is not copied (one inside it is
    copied with the directory), and the preview records its real path either
    way.
  - Spack is run without a shell. What it needs around it, such as loaded
    environment modules, is given with the task's C(environment) keyword.
  - Needs Spack 1.0 or later.
author:
  - infrastructurebuilder (@infrastructurebuilder)
options:
  path:
    description:
      - The environment's directory, the one that holds C(spack.yaml).
    type: path
    required: true
  spack:
    description:
      - The Spack executable, as a path or a name looked up on C(PATH).
    type: str
    default: spack
  yes_to_all:
    description:
      - Answer "yes" to every confirmation Spack asks of a command this module
        runs to change something, by giving that command C(--yes-to-all) where
        the installed Spack's help for it lists the option. The help is read
        only when this is true, once for each command.
      - That includes confirmations before removing or overwriting something.
        Without it, such a confirmation fails the task, since Ansible gives
        Spack no terminal to answer from.
      - A command that already has C(-y) or C(--yes-to-all) is left as it is.
    type: bool
    default: false
    version_added: 0.0.3
  state:
    description:
      - C(concretized) concretizes only; C(installed) also installs.
    type: str
    choices: [concretized, installed]
    default: installed
  fresh:
    description:
      - Concretize with C(--fresh), choosing the newest configuration rather
        than reusing what is installed.
    type: bool
    default: true
  install_args:
    description:
      - Arguments added to C(spack install) as they are, for example
        C([--cache-only]) or C([-j, "8"]).
    type: list
    elements: str
    default: []
  modules:
    description:
      - The module systems whose files are regenerated after installing.
    type: list
    elements: str
    choices: [tcl, lmod]
    default: []
  refresh_modules:
    description:
      - When the module files of I(modules) are regenerated.
      - C(when_needed) regenerates them when this run concretized or installed
        something, when a module root is missing, or when C(spack.lock), the
        environment's C(modules) configuration, or the module files
        themselves have changed since the module last regenerated them. A
        module file deleted or edited by hand is therefore put back. A run
        with nothing to do touches no module file.
      - C(always) regenerates them on every run.
      - The time Spack writes into each module file is never counted as a
        change.
    type: str
    choices: [when_needed, always]
    default: when_needed
  delete_tree:
    description:
      - Regenerate the module files with C(--delete-tree), removing the
        module tree first.
      - Spack's default module root is shared by every environment of that
        Spack. With I(delete_tree=true), regenerating for one environment
        removes the module files of the others; give each environment a root
        of its own (C(modules:default:roots) in its C(spack.yaml)), or set
        this to C(false).
    type: bool
    default: true
  log_file:
    description:
      - Where the output of C(spack install) is kept. Defaults to
        C(log.install) in the environment's directory.
    type: path
notes:
  - A build can take hours. Run the task with C(async) and C(poll).
  - 'Ansible refuses a task that is both asynchronous and in check mode
    ("check mode and async cannot be used on same task"). A preview builds
    nothing and is over in a minute, so it does not need C(async). Write
    the two keywords so that they fall away in check mode, as in the
    example below -
    C(async: "{{ 0 if ansible_check_mode else 86400 }}") and
    C(poll: "{{ 0 if ansible_check_mode else 60 }}").'
  - Supports check mode.
"""

EXAMPLES = r"""
- name: Write the environment
  ansible.builtin.template:
    src: spack.yaml.j2
    dest: /opt/spack-environments/base/spack.yaml
    mode: "0644"

- name: Build the environment and regenerate its Tcl module files
  infrastructurebuilder.csis_spack.spack_env:
    path: /opt/spack-environments/base
    spack: /opt/spack/bin/spack
    install_args: ["-j", "8"]
    modules: [tcl]
  environment: "{{ mycompiler_environment }}"
  # Asynchronous for the build, and not when previewing: Ansible refuses
  # async in check mode.
  async: "{{ 0 if ansible_check_mode else 86400 }}"
  poll: "{{ 0 if ansible_check_mode else 60 }}"

- name: Only see whether the environment would change
  infrastructurebuilder.csis_spack.spack_env:
    path: /opt/spack-environments/base
    state: concretized
  check_mode: true
"""

RETURN = r"""
concretized:
  description: Whether C(spack.lock) changed (in check mode, would change).
  returned: always
  type: bool
installed:
  description:
    - The specs newly installed (in check mode, those that would be).
    - Empty for I(state=concretized).
  returned: always
  type: list
  elements: dict
  contains:
    spec:
      description: The spec's name.
      type: str
    hash:
      description: The spec's hash.
      type: str
modules_refreshed:
  description: The module systems whose files changed.
  returned: always
  type: list
  elements: str
modules_reason:
  description:
    - Why the module files were regenerated, or why not.
    - C(always) for I(refresh_modules=always); C(concretized) or C(installed)
      when this run did that; C(missing_root) when a module root does not
      exist; C(no_stamp) when the module has no record of regenerating them;
      C(lock_changed), C(config_changed) or C(files_changed) when
      C(spack.lock), the C(modules) configuration or the module files differ
      from that record; C(not_needed) when nothing of that holds and they
      were left alone; C(not_requested) when I(modules) is empty or
      I(state=concretized).
  returned: always
  type: str
roots:
  description: The environment's root specs and their hashes, from C(spack.lock).
  returned: always
  type: list
  elements: dict
spack_version:
  description: The version of Spack that was run.
  returned: always
  type: str
log_file:
  description: Where the output of C(spack install) was written.
  returned: when the environment was installed
  type: str
"""

import os
import shutil
import tempfile
from typing import Any, cast

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.infrastructurebuilder.csis_spack.plugins.module_utils.spack import (
    Spack,
    SpackError,
    data_digest,
    file_digest,
    lock_specs,
    module_tree_digest,
    read_state,
    write_state,
)

# What the module remembers about the module files it regenerated.
MODULES_STATE = "csis_spack.modules.json"
MODULES_STATE_VERSION = 1
# Reasons after which regenerating is certain to change files.
CERTAIN = ("missing_root", "files_changed")

# Run by "spack python <this> <copy's spack.yaml> <real directory>" in check
# mode: the copy's relative include: and develop: paths become the absolute
# paths they name from the real environment, so that the preview reads and
# records what a real run would (spec 006). Absolute paths, paths with a $
# (Spack's own variables) and an include with no path (a git include) are
# left as they are. In Spack's Python, with Spack's YAML: the node may lack
# PyYAML, and "spack python -c" takes no arguments.
REWRITE = """\
import os
import sys

import spack.util.spack_yaml as syaml

manifest, origin = sys.argv[1], sys.argv[2]


def absolute(path):
    if os.path.isabs(path) or "$" in path:
        return path
    return os.path.normpath(os.path.join(origin, path))


with open(manifest) as handle:
    data = syaml.load(handle)
env = data.get("spack") or {}
includes = []
for entry in env.get("include") or []:
    if isinstance(entry, str):
        entry = absolute(entry)
    elif isinstance(entry, dict) and isinstance(entry.get("path"), str):
        entry["path"] = absolute(entry["path"])
    includes.append(entry)
if "include" in env:
    env["include"] = includes
for entry in (env.get("develop") or {}).values():
    if isinstance(entry, dict) and isinstance(entry.get("path"), str):
        entry["path"] = absolute(entry["path"])
with open(manifest, "w") as handle:
    syaml.dump(data, handle)
"""


def concretize(spack, path, fresh):
    args = ["concretize", "--force", "-q"]
    if fresh:
        args.append("--fresh")
    spack.run(spack.answered(args, words=1), env_path=path)


def not_installed(spack, path):
    """List the concrete specs of the environment that are not installed (externals aside)."""
    concrete, _roots = lock_specs(path)
    installed = spack.installed(path)
    return [
        {"spec": concrete[digest].get("name"), "hash": digest}
        for digest in sorted(set(concrete) - set(installed))
        if not concrete[digest].get("external")
    ]


def tree_record(root):
    return {"root": root, "digest": module_tree_digest(root)}


def refresh_reason(params, path, result, config, roots):
    """Say why the module files have to be regenerated, or that they do not."""
    if params["refresh_modules"] == "always":
        return "always"
    if result["concretized"]:
        return "concretized"
    if result["installed"]:
        return "installed"
    if not all(os.path.isdir(roots[system]) for system in params["modules"]):
        return "missing_root"
    stamp = read_state(path, MODULES_STATE)
    if stamp is None or stamp.get("version") != MODULES_STATE_VERSION:
        return "no_stamp"
    trees = stamp.get("trees") or {}
    if not all(system in trees for system in params["modules"]):
        return "no_stamp"
    if stamp.get("lock") != file_digest(os.path.join(path, "spack.lock")):
        return "lock_changed"
    if stamp.get("config") != data_digest(config):
        return "config_changed"
    if not all(trees[system] == tree_record(roots[system]) for system in params["modules"]):
        return "files_changed"
    return "not_needed"


def rewrite_paths(spack, scratch, copy, path):
    """Make the copy's relative include: and develop: paths name the real environment's files."""
    manifest = os.path.join(copy, "spack.yaml")
    with open(manifest) as handle:
        text = handle.read()
    if "include:" not in text and "develop:" not in text:
        return
    script = os.path.join(scratch, "rewrite.py")
    with open(script, "w") as handle:
        handle.write(REWRITE)
    spack.run(["python", script, manifest, path])


def check(module, spack, params, result):
    """Concretize a copy of the environment and say what would change."""
    path = params["path"]
    scratch = tempfile.mkdtemp(prefix="spack-env-check-")
    try:
        copy = os.path.join(scratch, "env")
        shutil.copytree(path, copy, ignore=shutil.ignore_patterns(".spack-env", "log.*"))
        rewrite_paths(spack, scratch, copy, path)
        concretize(spack, copy, params["fresh"])
        result["concretized"] = file_digest(os.path.join(copy, "spack.lock")) != file_digest(
            os.path.join(path, "spack.lock")
        )
        if params["state"] == "installed":
            result["installed"] = not_installed(spack, copy)
        _concrete, result["roots"] = lock_specs(copy)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    if params["state"] == "installed" and params["modules"]:
        config = spack.modules_config(path)
        roots = spack.module_roots(path, params["modules"], config)
        result["modules_reason"] = refresh_reason(params, path, result, config, roots)
        if result["modules_reason"] in CERTAIN:
            result["modules_refreshed"] = list(params["modules"])


def apply(module, spack, params, result):
    path = params["path"]
    lock = os.path.join(path, "spack.lock")
    before = file_digest(lock)
    concretize(spack, path, params["fresh"])
    result["concretized"] = file_digest(lock) != before

    if params["state"] == "installed":
        installed_before = set(spack.installed(path))
        log_file = params["log_file"] or os.path.join(path, "log.install")
        install = spack.answered(["install", *params["install_args"]], words=1)
        spack.run(install, env_path=path, log_file=log_file)
        result["log_file"] = log_file
        after = spack.installed(path)
        result["installed"] = [
            {"spec": after[digest].get("name"), "hash": digest}
            for digest in sorted(set(after) - installed_before)
            if not after[digest].get("external")
        ]

        if params["modules"]:
            config = spack.modules_config(path)
            roots = spack.module_roots(path, params["modules"], config)
            result["modules_reason"] = refresh_reason(params, path, result, config, roots)
            if result["modules_reason"] != "not_needed":
                for system in params["modules"]:
                    tree_before = module_tree_digest(roots[system])
                    args = ["module", system, "refresh", "-y"]
                    if params["delete_tree"]:
                        args.append("--delete-tree")
                    spack.run(spack.answered(args, words=3), env_path=path)
                    if module_tree_digest(roots[system]) != tree_before:
                        result["modules_refreshed"].append(system)
                write_state(
                    path,
                    MODULES_STATE,
                    {
                        "version": MODULES_STATE_VERSION,
                        "lock": file_digest(lock),
                        "config": data_digest(config),
                        "trees": {system: tree_record(roots[system]) for system in params["modules"]},
                    },
                )

    _concrete, result["roots"] = lock_specs(path)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type="path", required=True),
            spack=dict(type="str", default="spack"),
            yes_to_all=dict(type="bool", default=False),
            state=dict(type="str", choices=["concretized", "installed"], default="installed"),
            fresh=dict(type="bool", default=True),
            install_args=dict(type="list", elements="str", default=[]),
            modules=dict(type="list", elements="str", choices=["tcl", "lmod"], default=[]),
            refresh_modules=dict(type="str", choices=["when_needed", "always"], default="when_needed"),
            delete_tree=dict(type="bool", default=True),
            log_file=dict(type="path"),
        ),
        supports_check_mode=True,
    )
    params = cast("dict[str, Any]", module.params)
    result = dict(
        changed=False,
        concretized=False,
        installed=[],
        modules_refreshed=[],
        modules_reason="not_requested",
        roots=[],
    )  # type: dict[str, Any]
    if not os.path.isfile(os.path.join(params["path"], "spack.yaml")):
        module.fail_json(msg="%s is not a Spack environment: it has no spack.yaml" % params["path"], **result)
    try:
        spack = Spack(module, params["spack"], yes_to_all=params["yes_to_all"])
        result["spack_version"] = ".".join(str(part) for part in spack.require_version())
        if module.check_mode:
            check(module, spack, params, result)
        else:
            apply(module, spack, params, result)
    except SpackError as error:
        module.fail_json(msg=str(error), **result)
    result["changed"] = bool(result["concretized"] or result["installed"] or result["modules_refreshed"])
    module.exit_json(**result)


if __name__ == "__main__":
    main()
