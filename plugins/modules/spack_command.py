#!/usr/bin/python
# Copyright: Contributors to the infrastructurebuilder.csis_spack collection
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: spack_command
short_description: Run any Spack command, saying how to tell whether it changed something
version_added: 0.0.1
description:
  - Runs one Spack command, given as a list of arguments, without a shell.
  - It is for what the collection's other modules do not cover. Prefer them
    where they apply, because they compare with what is there before changing
    anything, and this module cannot.
  - I(changes) says how a change is told, since the module does not know what
    the command does.
  - In check mode the command is not run.
  - Needs Spack 1.0 or later.
author:
  - infrastructurebuilder (@infrastructurebuilder)
options:
  args:
    description:
      - The command and its arguments, as Spack takes them after its own name.
    type: list
    elements: str
    required: true
  changes:
    description:
      - C(config) reports a change when the I(sections) of I(scope) differ
        after the command, compared as data.
      - C(creates) does not run the command when the path in I(creates)
        exists, and reports a change when it ran.
      - C(always) reports a change whenever the command ran.
      - C(never) reports none; for commands that only read.
    type: str
    choices: [config, creates, always, never]
    required: true
  creates:
    description:
      - The path that the command makes. Required with I(changes=creates).
    type: path
  sections:
    description:
      - The configuration sections compared with I(changes=config).
    type: list
    elements: str
    default: [config, concretizer, mirrors, modules, packages, repos]
  scope:
    description:
      - The configuration scope compared with I(changes=config).
    type: str
    default: site
  env:
    description:
      - A Spack environment's directory to run the command in (C(spack -e)).
    type: path
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
      - The command is read from the leading words of I(args), up to the first
        option. A subcommand written after an option of its parent, as in
        C(config --scope user add), is not seen, and the parent's help decides;
        no such subcommand has C(--yes-to-all) in Spack 1.0 to 1.2.
    type: bool
    default: false
    version_added: 0.0.3
notes:
  - In check mode the command is not run. A change is reported as possible
    unless I(changes=never), or I(changes=creates) and the path exists.
  - On Spack 1.1, a configuration scope whose directory does not exist yet
    (the user scope, C(~/.spack), or the system scope, C(/etc/spack)) cannot
    be written to; Spack 1.1 leaves it out. The module fails and says so;
    make the directory first. Spack 1.0 and 1.2 make it on the first write.
"""

EXAMPLES = r"""
- name: Rebuild a mirror's index
  infrastructurebuilder.csis_spack.spack_command:
    args: [buildcache, update-index, site-cache]
    changes: always

- name: Add a package repository, once
  infrastructurebuilder.csis_spack.spack_command:
    args: [repo, add, --scope, site, /opt/spack-repos/ours]
    changes: config
    sections: [repos]

# Spack asks before removing anything; under Ansible, with no terminal to
# answer from, the question would fail the task. yes_to_all answers "yes" to
# every confirmation gc asks: here, to removing every unused package.
- name: Remove the packages nothing needs any more
  infrastructurebuilder.csis_spack.spack_command:
    args: [gc]
    changes: always
    yes_to_all: true
"""

RETURN = r"""
ran:
  description: Whether the command was run.
  returned: always
  type: bool
stdout:
  description: What the command printed.
  returned: when it ran
  type: str
spack_version:
  description: The version of Spack that was run.
  returned: always
  type: str
"""

import os
from typing import Any, cast

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.infrastructurebuilder.csis_spack.plugins.module_utils.spack import (
    Configuration,
    Spack,
    SpackError,
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            args=dict(type="list", elements="str", required=True),
            changes=dict(type="str", choices=["config", "creates", "always", "never"], required=True),
            creates=dict(type="path"),
            sections=dict(
                type="list",
                elements="str",
                default=["config", "concretizer", "mirrors", "modules", "packages", "repos"],
            ),
            scope=dict(type="str", default="site"),
            env=dict(type="path"),
            spack=dict(type="str", default="spack"),
            yes_to_all=dict(type="bool", default=False),
        ),
        required_if=[("changes", "creates", ["creates"])],
        supports_check_mode=True,
    )
    params = cast("dict[str, Any]", module.params)
    result = dict(changed=False, ran=False)  # type: dict[str, Any]
    how = params["changes"]
    if not params["args"]:
        module.fail_json(msg="args is empty: there is no command to run", **result)
    try:
        spack = Spack(module, params["spack"], yes_to_all=params["yes_to_all"])
        result["spack_version"] = ".".join(str(part) for part in spack.require_version())
        if how == "creates" and os.path.exists(params["creates"]):
            module.exit_json(**result)
        if module.check_mode:
            result["changed"] = how != "never"
            module.exit_json(**result)
        config = Configuration(spack, params["scope"])
        before = {section: config.get(section) for section in params["sections"]} if how == "config" else {}
        result["stdout"] = spack.run(spack.answered(params["args"]), env_path=params["env"])
        result["ran"] = True
        if how == "config":
            result["changed"] = before != {section: config.get(section) for section in params["sections"]}
        else:
            result["changed"] = how in ("always", "creates")
    except SpackError as error:
        module.fail_json(msg=str(error), **result)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
