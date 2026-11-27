#!/usr/bin/python
# Copyright: Contributors to the infrastructurebuilder.csis_spack collection
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: spack_buildcache_push
short_description: Push a Spack environment's installed packages to a build cache
version_added: 0.0.1
description:
  - Runs C(spack buildcache push) for an environment, so that what it built
    can be installed elsewhere from the mirror instead of being built again.
  - Reports a change only when a package was pushed that the mirror did not
    have, or that I(force) overwrote. Rebuilding the mirror's index
    (I(update_index)) alone is not reported as a change.
  - What was pushed is learned from the mirror, not from what Spack prints.
    C(spack buildcache check) is asked before and after which of the
    environment's packages the mirror lacks.
  - In check mode the same question is asked once, and nothing is pushed.
  - Signing uses a key already in Spack's GPG keyring on the node. The module
    never handles a private key.
  - Needs Spack 1.0 or later.
author:
  - infrastructurebuilder (@infrastructurebuilder)
options:
  env:
    description:
      - The environment's directory, the one that holds C(spack.yaml).
    type: path
    required: true
  mirror:
    description:
      - The mirror to push to, as Spack knows it (C(spack mirror list)), or a
        path or URL.
    type: str
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
  key:
    description:
      - The GPG key to sign with, by name, email or fingerprint. Without it
        and without I(unsigned), Spack signs with its default key.
    type: str
  unsigned:
    description:
      - Push without signing.
    type: bool
    default: false
  update_index:
    description:
      - Rebuild the mirror's index after a push. Spack rebuilds it only after
        a push that sent something; when nothing was pushed it leaves the
        index as it is, so a repeat run changes nothing.
      - An index changed by other means (a mirror edited by hand, a push from
        elsewhere without this option) is therefore not put right by a run
        with nothing to push. Run C(spack buildcache update-index) for that,
        for example in a C(command) step of the C(setup) role.
    type: bool
    default: false
  only:
    description:
      - Push only the environment's root packages (C(package)) or only their
        dependencies (C(dependencies)). By default both.
    type: str
    choices: [package, dependencies]
  force:
    description:
      - C(false) pushes only what the mirror lacks.
      - C(true) overwrites every package on every run, and reports a change
        every time; the module warns when it is used.
      - C(once) overwrites each package one time. The module
        remembers which packages it has overwritten on which mirror in a file
        of its own, C(.spack-env/csis_spack.pushed.json) in the environment's
        directory, and overwrites only those it has not. A run with nothing
        new reports no change.
    type: raw
    default: false
notes:
  - Supports check mode.
"""

EXAMPLES = r"""
- name: Push the environment to the site mirror, signed
  infrastructurebuilder.csis_spack.spack_buildcache_push:
    env: /opt/spack-environments/base
    mirror: site-cache
    key: 0123456789ABCDEF0123456789ABCDEF01234567
    update_index: true

- name: Replace what the mirror holds, one time, after rebuilding with the same hashes
  infrastructurebuilder.csis_spack.spack_buildcache_push:
    env: /opt/spack-environments/base
    mirror: site-cache
    key: 0123456789ABCDEF0123456789ABCDEF01234567
    force: once

- name: See what the mirror lacks
  infrastructurebuilder.csis_spack.spack_buildcache_push:
    env: /opt/spack-environments/base
    mirror: s3://example-bucket/spack/mirror
    unsigned: true
  check_mode: true
"""

RETURN = r"""
pushed:
  description:
    - The packages the mirror gained, and those I(force) overwrote (in check
      mode, those that would be).
  returned: always
  type: list
  elements: dict
  contains:
    spec:
      description: The package's name.
      type: str
    hash:
      description: The package's full hash.
      type: str
mirror_url:
  description: The URL of the mirror.
  returned: always
  type: str
spack_version:
  description: The version of Spack that was run.
  returned: always
  type: str
"""

import json
import os
import shutil
import tempfile
from typing import Any, cast

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.parsing.convert_bool import boolean
from ansible_collections.infrastructurebuilder.csis_spack.plugins.module_utils.spack import (
    Spack,
    SpackError,
    lock_specs,
    mirror_url,
    read_state,
    write_state,
)

# What the module remembers about the packages it overwrote with force=once.
PUSHED_STATE = "csis_spack.pushed.json"
PUSHED_STATE_VERSION = 1


def read_force(module, value):
    """Give the force option as False, True or "once"."""
    if isinstance(value, str) and value.strip().lower() == "once":
        return "once"
    try:
        return bool(boolean(value))
    except TypeError:
        module.fail_json(msg="force must be true, false or once; got %r" % (value,))


def selection(spack, params):
    """Map the hash of each package the options select to its name.

    They are the environment's installed packages, the externals left out, and
    cut down to the roots or to their dependencies when ``only`` says so.
    """
    path = params["env"]
    concrete, roots = lock_specs(path)
    installed = spack.installed(path)
    selected = {
        digest: (concrete.get(digest) or record).get("name")
        for digest, record in installed.items()
        if not record.get("external")
    }
    root_hashes = {root["hash"] for root in roots}
    if params["only"] == "package":
        selected = {digest: name for digest, name in selected.items() if digest in root_hashes}
    elif params["only"] == "dependencies":
        selected = {digest: name for digest, name in selected.items() if digest not in root_hashes}
    return selected


def lacking(spack, path, url, selected):
    """Give the hashes among ``selected`` that the mirror does not have."""
    scratch = tempfile.mkdtemp(prefix="spack-buildcache-check-")
    try:
        report = os.path.join(scratch, "check.json")
        # Exit 1 means "the mirror lacks something": not a failure here.
        spack.run(["buildcache", "check", "-m", url, "-o", report], env_path=path, ok=(0, 1))
        needed = set()
        if os.path.isfile(report):
            with open(report) as handle:
                for entry in json.load(handle).values():
                    needed.update(spec["hash"] for spec in entry.get("rebuildSpecs", []))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    return needed & set(selected)


def overwritten_before(path, url):
    """Give the hashes that force=once has already overwritten on this mirror."""
    state = read_state(path, PUSHED_STATE)
    if state is None or state.get("version") != PUSHED_STATE_VERSION:
        return set()
    return set((state.get("mirrors") or {}).get(url) or [])


def remember_overwritten(path, url, hashes):
    state = read_state(path, PUSHED_STATE)
    if state is None or state.get("version") != PUSHED_STATE_VERSION:
        state = {"version": PUSHED_STATE_VERSION, "mirrors": {}}
    state.setdefault("mirrors", {})[url] = sorted(hashes)
    write_state(path, PUSHED_STATE, state)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            env=dict(type="path", required=True),
            mirror=dict(type="str", required=True),
            spack=dict(type="str", default="spack"),
            yes_to_all=dict(type="bool", default=False),
            key=dict(type="str", no_log=False),
            unsigned=dict(type="bool", default=False),
            update_index=dict(type="bool", default=False),
            only=dict(type="str", choices=["package", "dependencies"]),
            force=dict(type="raw", default=False),
        ),
        mutually_exclusive=[("key", "unsigned")],
        supports_check_mode=True,
    )
    params = cast("dict[str, Any]", module.params)
    result = dict(changed=False, pushed=[], mirror_url="")  # type: dict[str, Any]
    path = params["env"]
    force = read_force(module, params["force"])
    if not os.path.isfile(os.path.join(path, "spack.yaml")):
        module.fail_json(msg="%s is not a Spack environment: it has no spack.yaml" % path, **result)
    try:
        spack = Spack(module, params["spack"], yes_to_all=params["yes_to_all"])
        result["spack_version"] = ".".join(str(part) for part in spack.require_version())
        url = result["mirror_url"] = mirror_url(params["mirror"], spack.mirrors(path))
        selected = selection(spack, params)
        missing = lacking(spack, path, url, selected)
        if force == "once":
            done_before = overwritten_before(path, url)
            overwrite = set(selected) - done_before
        else:
            done_before = set()
            overwrite = set(selected) if force else set()

        if module.check_mode:
            pushed = missing | overwrite
        else:
            push = ["buildcache", "push"]
            if params["unsigned"]:
                push.append("--unsigned")
            elif params["key"]:
                push += ["--key", params["key"]]
            if force == "once" and overwrite:
                # Exactly these, by hash, and not their dependencies again.
                chosen = ["/" + digest for digest in sorted(overwrite)]
                again = [*push, "--only", "package", "--force", params["mirror"], *chosen]
                spack.run(spack.answered(again, words=2), env_path=path)
            args = list(push)
            if params["update_index"]:
                args.append("--update-index")
            if params["only"]:
                args += ["--only", params["only"]]
            if force is True:
                module.warn(
                    "force=true overwrites every package on the mirror and reports a change on every "
                    "run; use force=once to overwrite each package one time"
                )
                args.append("--force")
            spack.run(spack.answered([*args, params["mirror"]], words=2), env_path=path)
            pushed = (missing - lacking(spack, path, url, selected)) | overwrite
            if force == "once" and overwrite:
                remember_overwritten(path, url, done_before | overwrite)
        result["pushed"] = [{"spec": selected[digest], "hash": digest} for digest in sorted(pushed)]
    except SpackError as error:
        module.fail_json(msg=str(error), **result)
    result["changed"] = bool(result["pushed"])
    module.exit_json(**result)


if __name__ == "__main__":
    main()
