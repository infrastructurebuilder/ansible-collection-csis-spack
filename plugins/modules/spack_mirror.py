#!/usr/bin/python
# Copyright: Contributors to the infrastructurebuilder.csis_spack collection
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: spack_mirror
short_description: Declare one mirror in a scope of Spack's configuration
version_added: 0.0.1
description:
  - Makes a mirror exist in one configuration scope with the URL and the
    properties given, or not exist, and changes nothing when that is so.
  - A mirror that is there but different is removed and added again, so that
    a changed URL is corrected. Only the properties given are compared.
  - Supports check mode.
  - Needs Spack 1.0 or later.
author:
  - infrastructurebuilder (@infrastructurebuilder)
options:
  name:
    description:
      - The mirror's name.
    type: str
    required: true
  url:
    description:
      - The mirror's URL or path. Required with I(state=present).
    type: str
  type:
    description:
      - What the mirror holds, as C(spack mirror add --type) takes it. Left
        out, Spack's own default applies and the property is not compared.
    type: list
    elements: str
    choices: [binary, source]
  signed:
    description:
      - Whether packages from the mirror must be signed (C(--signed)) or need
        not be (C(--unsigned)). Left out, Spack's own default applies and the
        property is not compared.
    type: bool
  scope:
    description:
      - The configuration scope, as C(spack mirror add --scope) takes it.
    type: str
    default: site
  state:
    description:
      - Whether the mirror is to be there.
    type: str
    choices: [present, absent]
    default: present
  spack:
    description:
      - The Spack executable, as a path or a name looked up on C(PATH).
    type: str
    default: spack
notes:
  - Supports check mode.
"""

EXAMPLES = r"""
- name: Use a binary mirror
  infrastructurebuilder.csis_spack.spack_mirror:
    name: site-cache
    url: s3://example-bucket/spack/mirror
    type: [binary]
    signed: true

- name: Stop using one
  infrastructurebuilder.csis_spack.spack_mirror:
    name: old-cache
    state: absent
"""

RETURN = r"""
action:
  description:
    - What was done (in check mode, would be). C(added), C(replaced),
      C(removed), or C(none).
  returned: always
  type: str
mirror:
  description: The mirror as the scope holds it afterwards; empty when it is not there.
  returned: always
  type: dict
spack_version:
  description: The version of Spack that was run.
  returned: always
  type: str
"""

from typing import Any, cast

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.infrastructurebuilder.csis_spack.plugins.module_utils.spack import (
    Configuration,
    Spack,
    SpackError,
    mirror_record,
    scope_args,
)


def wanted_record(params):
    """Give the properties the options state; only these are compared."""
    wanted = {"url": params["url"]}
    if params["type"] is not None:
        wanted["binary"] = "binary" in params["type"]
        wanted["source"] = "source" in params["type"]
    if params["signed"] is not None:
        wanted["signed"] = params["signed"]
    return wanted


def differs(current, wanted):
    # A property Spack does not record has its default: a mirror holds both
    # kinds, and whether it must be signed is not said.
    defaults = {"binary": True, "source": True}
    return any(current.get(key, defaults.get(key)) != value for key, value in wanted.items())


def add_args(params):
    args = ["mirror", "add", *scope_args(params["scope"])]
    for kind in params["type"] or []:
        args += ["--type", kind]
    if params["signed"] is not None:
        args.append("--signed" if params["signed"] else "--unsigned")
    return [*args, params["name"], params["url"]]


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type="str", required=True),
            url=dict(type="str"),
            type=dict(type="list", elements="str", choices=["binary", "source"]),
            signed=dict(type="bool"),
            scope=dict(type="str", default="site"),
            state=dict(type="str", choices=["present", "absent"], default="present"),
            spack=dict(type="str", default="spack"),
        ),
        required_if=[("state", "present", ["url"])],
        supports_check_mode=True,
    )
    params = cast("dict[str, Any]", module.params)
    result = dict(changed=False, action="none", mirror={})  # type: dict[str, Any]
    try:
        spack = Spack(module, params["spack"])
        result["spack_version"] = ".".join(str(part) for part in spack.require_version())
        config = Configuration(spack, params["scope"])
        mirrors = config.get("mirrors")
        present = params["name"] in mirrors
        current = mirror_record(mirrors.get(params["name"]))
        remove = ["mirror", "remove", *scope_args(params["scope"]), params["name"]]
        if params["state"] == "absent":
            if present:
                result["action"] = "removed"
                if not module.check_mode:
                    spack.run(remove)
        elif not present:
            result["action"] = "added"
            if not module.check_mode:
                spack.run(add_args(params))
        elif differs(current, wanted_record(params)):
            result["action"] = "replaced"
            if not module.check_mode:
                spack.run(remove)
                spack.run(add_args(params))
        if module.check_mode:
            result["mirror"] = current if params["state"] == "present" and result["action"] == "none" else {}
        else:
            result["mirror"] = mirror_record(config.get("mirrors").get(params["name"]))
            if result["action"] in ("added", "replaced") and differs(result["mirror"], wanted_record(params)):
                module.fail_json(
                    msg="Spack did not record the mirror as given: %r" % (result["mirror"],), **result
                )
    except SpackError as error:
        module.fail_json(msg=str(error), **result)
    result["changed"] = result["action"] != "none"
    module.exit_json(**result)


if __name__ == "__main__":
    main()
