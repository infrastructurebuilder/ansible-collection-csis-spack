#!/usr/bin/python
# Copyright: Contributors to the infrastructurebuilder.csis_spack collection
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: spack_config
short_description: Declare settings in one scope of Spack's configuration
version_added: 0.0.1
description:
  - Makes the given settings true in one configuration scope of Spack, through
    C(spack config), and changes nothing when they already are.
  - The settings are a mapping in the shape of Spack's configuration, with a
    section (C(config), C(packages), C(modules), C(concretizer)...) at the top.
    The module knows no setting itself, and Spack checks them against its own
    schema.
  - A value that is a list or a scalar is set to exactly what is given.
    C(spack config add) alone merges a list into the one that is there; the
    module removes the path first, so that a changed list is corrected.
  - Supports check mode and diff mode.
  - Needs Spack 1.0 or later.
author:
  - infrastructurebuilder (@infrastructurebuilder)
options:
  settings:
    description:
      - The settings, with a section at the top of each. Every section must be
        a mapping.
      - With I(state=absent) the values are not read. Each path that ends in
        something other than a non-empty mapping is removed.
    type: dict
    required: true
  scope:
    description:
      - The configuration scope, as C(spack config --scope) takes it.
    type: str
    default: site
  state:
    description:
      - C(present) makes the settings true. C(absent) removes the paths named.
    type: str
    choices: [present, absent]
    default: present
  mode:
    description:
      - With I(state=present), C(merge) leaves every key of the scope that is
        not named alone. C(replace) makes each section named exactly what is
        given, removing its other keys.
    type: str
    choices: [merge, replace]
    default: merge
  spack:
    description:
      - The Spack executable, as a path or a name looked up on C(PATH).
    type: str
    default: spack
notes:
  - Supports check mode.
  - On Spack 1.1, a configuration scope whose directory does not exist yet
    (the user scope, C(~/.spack), or the system scope, C(/etc/spack)) cannot
    be written to; Spack 1.1 leaves it out. The module fails and says so;
    make the directory first. Spack 1.0 and 1.2 make it on the first write.
"""

EXAMPLES = r"""
- name: Set how targets are chosen, and declare a library installed outside Spack
  infrastructurebuilder.csis_spack.spack_config:
    spack: /opt/spack/bin/spack
    settings:
      concretizer:
        targets:
          granularity: generic
      packages:
        all:
          providers:
            mpi: [mympi]
        mympi:
          externals:
            - spec: mympi@4.1
              prefix: /opt/mympi
          buildable: false

- name: Stop using a compiler that detection registered
  infrastructurebuilder.csis_spack.spack_config:
    state: absent
    settings:
      packages:
        oldcompiler:
"""

RETURN = r"""
paths:
  description: The configuration paths that were set or removed (in check mode, that would be).
  returned: always
  type: list
  elements: str
  sample: ["packages:all:providers:mpi"]
scope:
  description: The scope that was read and written.
  returned: always
  type: str
spack_version:
  description: The version of Spack that was run.
  returned: always
  type: str
"""

import json
from typing import Any, cast

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.infrastructurebuilder.csis_spack.plugins.module_utils.spack import (
    Configuration,
    Spack,
    SpackError,
    merged,
    nest,
    path_text,
    plan_absent,
    plan_merge,
    plan_replace,
    without,
)


def plan(section, current, wanted, state, mode):
    """Give (removes, adds, expected) for one section; paths start with the section."""
    if state == "absent":
        removes, adds = plan_absent(current, wanted, [section]), []
        expected = current
        for path in removes:
            expected = without(expected, path[1:])
    elif mode == "replace":
        removes, adds = plan_replace(current, wanted, [section])
        expected = wanted
    else:
        removes, adds = plan_merge(current, wanted, [section])
        expected = merged(current, wanted)
    return removes, adds, expected


def apply(config, section, current, removes, adds):
    """Remove, then add, through Spack; put back what was removed if Spack refuses the rest."""
    for path in removes:
        config.remove(path)
    if not adds:
        return
    data = {}  # type: dict[str, Any]
    for path, value in adds:
        data = merged(data, nest(path[1:], value))
    try:
        config.add(section, data)
    except SpackError:
        # Spack checks what is added against its schema. What was removed to
        # make room is put back, so that a refused value leaves the scope as
        # it was.
        after = config.get(section)
        restore = {}  # type: dict[str, Any]
        for path in removes:
            value = current
            for key in path[1:]:
                value = value[key]
            restore = merged(restore, nest(path[1:], value))
        if restore and after != current:
            config.add(section, restore)
        raise


def main():
    module = AnsibleModule(
        argument_spec=dict(
            settings=dict(type="dict", required=True),
            scope=dict(type="str", default="site"),
            state=dict(type="str", choices=["present", "absent"], default="present"),
            mode=dict(type="str", choices=["merge", "replace"], default="merge"),
            spack=dict(type="str", default="spack"),
        ),
        supports_check_mode=True,
    )
    params = cast("dict[str, Any]", module.params)
    result = dict(changed=False, paths=[], scope=params["scope"])  # type: dict[str, Any]
    for section, wanted in params["settings"].items():
        if wanted is None and params["state"] == "absent":
            module.fail_json(msg="to remove a whole section, name its keys: %s has none" % section, **result)
        if not isinstance(wanted, dict):
            module.fail_json(msg="the section %s must be a mapping, not %r" % (section, wanted), **result)
    try:
        spack = Spack(module, params["spack"])
        result["spack_version"] = ".".join(str(part) for part in spack.require_version())
        config = Configuration(spack, params["scope"])
        before, after = {}, {}
        for section, wanted in sorted(params["settings"].items()):
            current = config.get(section)
            removes, adds, expected = plan(section, current, wanted, params["state"], params["mode"])
            before[section], after[section] = current, expected
            touched = removes + [path for path, _value in adds]
            result["paths"] += sorted({path_text(path) for path in touched})
            if not touched or module.check_mode:
                continue
            apply(config, section, current, removes, adds)
            found = config.get(section)
            if found != expected:
                module.fail_json(
                    msg="Spack did not take the settings of %s as given; the scope now holds %s, not %s"
                    % (section, json.dumps(found, sort_keys=True), json.dumps(expected, sort_keys=True)),
                    **result,
                )
    except SpackError as error:
        module.fail_json(msg=str(error), **result)
    result["changed"] = bool(result["paths"])
    if result["changed"]:
        result["diff"] = dict(
            before=json.dumps(before, indent=2, sort_keys=True) + "\n",
            after=json.dumps(after, indent=2, sort_keys=True) + "\n",
        )
    module.exit_json(**result)


if __name__ == "__main__":
    main()
