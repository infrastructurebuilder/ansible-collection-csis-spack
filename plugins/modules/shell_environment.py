#!/usr/bin/python
# Copyright: Contributors to the infrastructurebuilder.csis_spack collection
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: shell_environment
short_description: Capture the environment that some shell lines produce
version_added: 0.0.1
description:
  - Runs the given lines in a shell and returns the environment variables
    they set or changed, as a mapping to hand to later tasks with the
    C(environment) keyword.
  - It is for what only a shell can do, such as loading environment modules
    or enabling a software collection, before commands that must see the
    result. The collection's other modules run no shell.
  - Nothing is changed by capturing, so the module never reports a change and
    also runs in check mode. Lines that change the node are the caller's
    business.
  - The lines run as they are. A line that fails does not stop the ones after
    it unless the lines themselves say so, for example with C(set -e); the
    task fails only when the shell as a whole does.
author:
  - infrastructurebuilder (@infrastructurebuilder)
options:
  shell:
    description:
      - The lines to run.
    type: str
    required: true
  executable:
    description:
      - The shell to run them with.
    type: path
    default: /bin/bash
notes:
  - Supports check mode, by running in it.
"""

EXAMPLES = r"""
- name: Capture what a compiler's own setup script does
  infrastructurebuilder.csis_spack.shell_environment:
    shell: |
      . /opt/mycompiler/12/setvars.sh
  register: mycompiler

- name: Have Spack look for compilers with it loaded
  infrastructurebuilder.csis_spack.spack_detect:
    compilers: true
  environment: "{{ mycompiler.environment }}"
"""

RETURN = r"""
environment:
  description: The variables the lines set or changed, with their values.
  returned: always
  type: dict
unset:
  description: The variables the lines removed. The C(environment) keyword cannot express these.
  returned: always
  type: list
  elements: str
"""

import json
import os
import sys
from typing import cast

from ansible.module_utils.basic import AnsibleModule

# What a shell changes by merely running.
IGNORED = ("_", "SHLVL", "PWD", "OLDPWD")
MARKER = "---csis_spack-environment-follows---"


def main():
    module = AnsibleModule(
        argument_spec=dict(
            shell=dict(type="str", required=True),
            executable=dict(type="path", default="/bin/bash"),
        ),
        supports_check_mode=True,
    )
    params = cast("dict", module.params)
    before = dict(os.environ)
    dump = "%s -c 'import json, os; print(json.dumps(dict(os.environ)))'" % sys.executable
    script = "%s\necho %s\n%s\n" % (params["shell"], MARKER, dump)
    rc, out, err = module.run_command([params["executable"], "-c", script])
    _lines, found, tail = out.rpartition(MARKER)
    if rc != 0 or not found:
        module.fail_json(msg="the shell lines failed (exit %d)" % rc, stdout=out, stderr=err)
    try:
        after = json.loads(tail)
    except ValueError:
        module.fail_json(msg="could not read the environment the shell lines left", stdout=out, stderr=err)
    environment = {
        name: value
        for name, value in after.items()
        if before.get(name) != value and name not in IGNORED and not name.startswith("BASH_FUNC_")
    }
    unset = sorted(name for name in before if name not in after and name not in IGNORED)
    module.exit_json(changed=False, environment=environment, unset=unset)


if __name__ == "__main__":
    main()
