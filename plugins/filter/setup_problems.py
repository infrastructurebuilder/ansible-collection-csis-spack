# Copyright: Contributors to the infrastructurebuilder.csis_spack collection
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Check a ``spack_setup`` list before any of its steps is carried out."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
name: setup_problems
short_description: List what is wrong with a spack_setup list of steps
version_added: 0.0.1
description:
  - Takes the list of steps that the C(setup) role carries out and returns a
    list of sentences, one for each thing wrong with it. An empty list means
    the steps can be carried out.
  - It checks that each step is a mapping with a known C(kind), that every
    option belongs to that kind, that the options a kind needs are there, and
    that an environment named by a step was captured by an earlier step.
  - It does not check the values. The module of each kind does that when its
    step runs.
author:
  - infrastructurebuilder (@infrastructurebuilder)
options:
  _input:
    description: The list of steps.
    type: list
    elements: dict
    required: true
"""

EXAMPLES = r"""
- name: Refuse a list of steps that cannot be carried out
  ansible.builtin.assert:
    that: spack_setup | infrastructurebuilder.csis_spack.setup_problems | length == 0
"""

RETURN = r"""
_value:
  description: One sentence for each problem; empty when there is none.
  type: list
  elements: str
"""

# Each kind of step: the module that carries it out, and that module's options
# a step may give. The executable is the role's, not a step's.
KINDS = {
    "config": {
        "module": "spack_config",
        "required": ["settings"],
        "optional": ["scope", "state", "mode"],
    },
    "mirror": {
        "module": "spack_mirror",
        "required": ["name"],
        "optional": ["url", "type", "signed", "scope", "state"],
    },
    "gpg_key": {
        "module": "spack_gpg_key",
        "required": [],
        "optional": ["key", "fingerprint", "from_mirrors"],
    },
    "detect": {
        "module": "spack_detect",
        "required": [],
        "optional": ["compilers", "externals", "not_buildable", "exclude", "paths", "require", "scope"],
    },
    "command": {
        "module": "spack_command",
        "required": ["args", "changes"],
        "optional": ["creates", "sections", "scope", "env"],
    },
    # "name" here is the name later steps refer to the environment by.
    "environment": {
        "module": "shell_environment",
        "required": ["name", "shell"],
        "optional": ["executable"],
    },
}
# What any step may also have: its kind, a label for the output, and (except
# for an environment step) the environment to run in.
COMMON = ["kind", "label", "environment"]


def setup_problems(steps):
    """List what is wrong with ``steps``; see DOCUMENTATION."""
    if not isinstance(steps, list):
        return ["spack_setup must be a list of steps, not %s" % type(steps).__name__]
    problems = []
    environments = set()
    for number, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            problems.append("step %d is not a mapping" % number)
            continue
        kind = step.get("kind")
        if kind not in KINDS:
            problems.append(
                "step %d: kind is %r; it must be one of %s" % (number, kind, ", ".join(sorted(KINDS)))
            )
            continue
        where = "step %d (%s)" % (number, kind)
        spec = KINDS[kind]
        allowed = set(COMMON) | set(spec["required"]) | set(spec["optional"])
        if kind == "environment":
            allowed.discard("environment")
        for option in sorted(set(step) - allowed):
            problems.append("%s: %r is not an option of this kind" % (where, option))
        for option in spec["required"]:
            if option not in step:
                problems.append("%s: %r is required" % (where, option))
        wanted = step.get("environment")
        if kind != "environment" and isinstance(wanted, str) and wanted not in environments:
            problems.append("%s: no earlier step captures an environment named %r" % (where, wanted))
        elif kind != "environment" and wanted is not None and not isinstance(wanted, (str, dict)):
            problems.append("%s: environment must be a name or a mapping of variables" % where)
        if kind == "environment" and isinstance(step.get("name"), str):
            if step["name"] in environments:
                problems.append("%s: an earlier step already captures %r" % (where, step["name"]))
            environments.add(step["name"])
    return problems


def setup_label(step):
    """Give a short name for a step, for the output: its label, or its kind and main option."""
    if not isinstance(step, dict):
        return "?"
    if step.get("label"):
        return str(step["label"])
    kind = step.get("kind")
    if kind == "config":
        detail = ", ".join(sorted(step.get("settings") or {}))
        if step.get("state") == "absent":
            detail = "remove from " + detail
    elif kind == "mirror":
        detail = str(step.get("name"))
    elif kind == "gpg_key":
        detail = str(step.get("key") or "from the mirrors")
    elif kind == "detect":
        what = []
        if step.get("compilers"):
            what.append("compilers")
        externals = step.get("externals")
        if isinstance(externals, list):
            what.append(", ".join(str(name) for name in externals))
        elif externals:
            what.append("externals")
        detail = " and ".join(what)
    elif kind == "command":
        detail = " ".join(str(arg) for arg in step.get("args") or [])
    elif kind == "environment":
        detail = str(step.get("name"))
    else:
        detail = ""
    return ("%s: %s" % (kind, detail)) if detail else str(kind)


class FilterModule:
    """The collection's filters."""

    def filters(self):
        return {"setup_problems": setup_problems, "setup_label": setup_label}
