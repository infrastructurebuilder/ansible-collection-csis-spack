#!/usr/bin/python
# Copyright: Contributors to the infrastructurebuilder.csis_spack collection
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: spack_detect
short_description: Have Spack look for compilers and installed packages on the node
version_added: 0.0.1
description:
  - Runs C(spack compiler find) and C(spack external find), which record in a
    configuration scope what they find on the machine.
  - This is discovery, not declared state. What is found depends on the
    machine and on the environment the commands run in, such as which
    environment modules are loaded. Give that environment with the task's
    C(environment) keyword. To declare a package instead, use
    M(infrastructurebuilder.csis_spack.spack_config).
  - A change is told from the scope's C(packages) section before and after,
    compared as data, because Spack writes it back in another order each time.
  - I(require) names what must be registered afterwards, in any scope. Spack
    says nothing when it finds nothing; without I(require), a run in the wrong
    environment is a quiet success.
  - Discovery cannot be previewed. In check mode nothing is run and nothing
    is reported as changing.
  - Needs Spack 1.0 or later.
author:
  - infrastructurebuilder (@infrastructurebuilder)
options:
  compilers:
    description:
      - Run C(spack compiler find).
    type: bool
    default: false
  externals:
    description:
      - C(true) runs C(spack external find) for Spack's own default set of
        packages. A list of package names looks for those.
    type: raw
    default: false
  not_buildable:
    description:
      - Mark the packages C(spack external find) finds as never to be built
        (C(--not-buildable)).
    type: bool
    default: false
  exclude:
    description:
      - Package names C(spack external find) is to leave out.
    type: list
    elements: str
    default: []
  paths:
    description:
      - Directories to look in, instead of those on C(PATH).
    type: list
    elements: path
    default: []
  require:
    description:
      - Specs that must be registered as externals once detection has run,
        each a package name with an optional version, such as C(gcc@14). A
        version accepts anything more exact. The task fails naming those that
        are not.
    type: list
    elements: str
    default: []
  scope:
    description:
      - The configuration scope to record in.
    type: str
    default: site
  spack:
    description:
      - The Spack executable, as a path or a name looked up on C(PATH).
    type: str
    default: spack
notes:
  - Supports check mode only by doing nothing in it.
  - On Spack 1.1, a configuration scope whose directory does not exist yet
    (the user scope, C(~/.spack), or the system scope, C(/etc/spack)) cannot
    be written to; Spack 1.1 leaves it out. The module fails and says so;
    make the directory first. Spack 1.0 and 1.2 make it on the first write.
"""

EXAMPLES = r"""
- name: Record the compilers and tools the system has
  infrastructurebuilder.csis_spack.spack_detect:
    compilers: true
    externals: true

- name: Record a compiler that is only visible with its environment loaded
  infrastructurebuilder.csis_spack.spack_detect:
    compilers: true
    require: [mycompiler@12]
  environment: "{{ mycompiler_environment }}"

- name: Use the system's build tool and never build another
  infrastructurebuilder.csis_spack.spack_detect:
    externals: [mybuildtool]
    not_buildable: true
"""

RETURN = r"""
added:
  description: The external specs the scope gained.
  returned: always
  type: list
  elements: str
removed:
  description: The external specs the scope lost.
  returned: always
  type: list
  elements: str
previewed:
  description: False in check mode, where discovery is not run.
  returned: always
  type: bool
spack_version:
  description: The version of Spack that was run.
  returned: always
  type: str
"""

from typing import Any, cast

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.parsing.convert_bool import boolean
from ansible_collections.infrastructurebuilder.csis_spack.plugins.module_utils.spack import (
    Configuration,
    Spack,
    SpackError,
    external_specs,
    satisfies,
    scope_args,
)


def read_externals(module, value):
    """Give the externals option as (run it, names): true, false or a list of names."""
    if isinstance(value, (list, tuple)):
        return True, [str(name) for name in value]
    try:
        return bool(boolean(value)), []
    except TypeError:
        module.fail_json(msg="externals must be true, false or a list of package names; got %r" % (value,))
        return False, []  # not reached: fail_json exits


def main():
    module = AnsibleModule(
        argument_spec=dict(
            compilers=dict(type="bool", default=False),
            externals=dict(type="raw", default=False),
            not_buildable=dict(type="bool", default=False),
            exclude=dict(type="list", elements="str", default=[]),
            paths=dict(type="list", elements="path", default=[]),
            require=dict(type="list", elements="str", default=[]),
            scope=dict(type="str", default="site"),
            spack=dict(type="str", default="spack"),
        ),
        supports_check_mode=True,
    )
    params = cast("dict[str, Any]", module.params)
    result = dict(changed=False, added=[], removed=[], previewed=True)  # type: dict[str, Any]
    externals, names = read_externals(module, params["externals"])
    if not params["compilers"] and not externals:
        module.fail_json(msg="nothing to look for: set compilers, externals, or both", **result)
    try:
        spack = Spack(module, params["spack"])
        result["spack_version"] = ".".join(str(part) for part in spack.require_version())
        if module.check_mode:
            result["previewed"] = False
            module.exit_json(**result)
        config = Configuration(spack, params["scope"])
        before = config.get("packages")
        if params["compilers"]:
            spack.run(["compiler", "find", *scope_args(params["scope"]), *params["paths"]])
        if externals:
            args = ["external", "find", *scope_args(params["scope"])]
            if params["not_buildable"]:
                args.append("--not-buildable")
            for name in params["exclude"]:
                args += ["--exclude", name]
            for path in params["paths"]:
                args += ["-p", path]
            spack.run([*args, *names])
        after = config.get("packages")
        was, now = set(external_specs(before)), set(external_specs(after))
        result["added"], result["removed"] = sorted(now - was), sorted(was - now)
        result["changed"] = before != after
        registered = external_specs(config.get("packages", merged_scopes=True))
        missing = [
            spec for spec in params["require"] if not any(satisfies(found, spec) for found in registered)
        ]
        if missing:
            module.fail_json(
                msg="not registered after detection: %s. Spack looks on PATH and in the environment the "
                "task runs in; if these are only visible with something loaded, give the task that "
                "environment" % ", ".join(missing),
                **result,
            )
    except SpackError as error:
        module.fail_json(msg=str(error), **result)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
