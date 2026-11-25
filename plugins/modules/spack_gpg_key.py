#!/usr/bin/python
# Copyright: Contributors to the infrastructurebuilder.csis_spack collection
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: spack_gpg_key
short_description: Have Spack trust public keys for build caches
version_added: 0.0.1
description:
  - Trusts a public key from a file or a URL (C(spack gpg trust)), or the keys
    that the configured binary mirrors publish
    (C(spack buildcache keys --install --trust)).
  - A change is a key that Spack trusts afterwards and did not before, told
    from C(spack gpg list --trusted). What Spack prints, and how it exits,
    are not relied on to tell.
  - Public keys only. The module never handles a private key.
  - In check mode a key file whose fingerprint is known, from I(fingerprint)
    or by reading the file with C(gpg), is reported exactly. What the mirrors
    would give cannot be known without fetching it, and is not previewed.
  - Spack 1.2 asks whether to trust each key, C([y/N]), before it trusts
    it, even a key it trusts already. Ansible gives Spack no terminal to answer
    from, so the question would fail the task. Both trusts are therefore run
    with C(--yes-to-all) where the help of the Spack on the node lists it
    (Spack 1.2 and later; C(spack gpg trust --help) and
    C(spack buildcache keys --help) are read once each, before the trust).
    Spack 1.0 and 1.1 do not ask, and refuse the option, so it is left out
    there. Nothing is ever answered on Spack's input.
  - Needs Spack 1.0 or later.
author:
  - infrastructurebuilder (@infrastructurebuilder)
options:
  key:
    description:
      - A public key, as a file on the node or a URL to fetch it from.
    type: str
  fingerprint:
    description:
      - The fingerprint the key in I(key) must have, 40 hexadecimal digits.
        Given, a key that is trusted already is not fetched or read again, and
        a file holding another key is refused.
    type: str
  from_mirrors:
    description:
      - Trust the keys published by the binary mirrors Spack is configured
        with.
      - Every key the mirrors publish is trusted, without confirmation and
        with no fingerprint to check it against; that is what this option
        asks for. To trust one known key, give I(key) with I(fingerprint)
        instead.
    type: bool
    default: false
  spack:
    description:
      - The Spack executable, as a path or a name looked up on C(PATH).
    type: str
    default: spack
  yes_to_all:
    description:
      - Answer "yes" to every confirmation Spack asks of a command this module
        runs to change something, by giving that command C(--yes-to-all) where
        the installed Spack's help for it lists the option. That includes
        confirmations before removing or overwriting something. Without it,
        such a confirmation fails the task, since Ansible gives Spack no
        terminal to answer from.
      - Changes nothing in this module, which answers Spack's confirmation for
        the keys it is asked to trust in any case. It is here so that every
        module of the collection that runs Spack takes it.
    type: bool
    default: false
    version_added: 0.0.3
notes:
  - Supports check mode, within the limits described above.
"""

EXAMPLES = r"""
- name: Trust the key a site signs its build cache with
  infrastructurebuilder.csis_spack.spack_gpg_key:
    key: https://example.org/spack/mirror.pub
    fingerprint: 0123456789ABCDEF0123456789ABCDEF01234567

- name: Trust what the configured mirrors publish
  infrastructurebuilder.csis_spack.spack_gpg_key:
    from_mirrors: true
"""

RETURN = r"""
trusted:
  description: The fingerprints newly trusted (in check mode, those known to be missing).
  returned: always
  type: list
  elements: str
previewed:
  description: False when check mode could not tell what would happen.
  returned: always
  type: bool
spack_version:
  description: The version of Spack that was run.
  returned: always
  type: str
"""

import os
import re
import tempfile
from typing import Any, cast

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url
from ansible_collections.infrastructurebuilder.csis_spack.plugins.module_utils.spack import (
    Spack,
    SpackError,
    fingerprints,
)


def trusted(spack):
    return set(fingerprints(spack.run(["gpg", "list", "--trusted", "--fmt", "colons"])))


def key_file(module, key, scratch):
    """Give the key as a local file, fetching it when it is a URL."""
    if "://" not in key:
        if not os.path.isfile(key):
            module.fail_json(msg="there is no key file %s" % key)
        return key
    path = os.path.join(scratch, "key.pub")
    with open(path, "wb") as handle:
        handle.write(open_url(key).read())
    return path


def file_fingerprints(module, path):
    """Read the fingerprints of the keys in a file with gpg; None when there is no gpg to ask."""
    gpg = module.get_bin_path("gpg") or module.get_bin_path("gpg2")
    if not gpg:
        return None
    _rc, out, _err = module.run_command([gpg, "--show-keys", "--with-colons", path])
    return fingerprints(out)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            key=dict(type="str", no_log=False),
            fingerprint=dict(type="str"),
            from_mirrors=dict(type="bool", default=False),
            spack=dict(type="str", default="spack"),
            yes_to_all=dict(type="bool", default=False),
        ),
        required_by=dict(fingerprint=["key"]),
        supports_check_mode=True,
    )
    params = cast("dict[str, Any]", module.params)
    result = dict(changed=False, trusted=[], previewed=True)  # type: dict[str, Any]
    if not params["key"] and not params["from_mirrors"]:
        module.fail_json(msg="give key, or from_mirrors=true, or both", **result)
    wanted = None
    if params["fingerprint"]:
        wanted = re.sub(r"\s", "", params["fingerprint"]).upper()
        if not re.fullmatch(r"[0-9A-F]{40}", wanted):
            module.fail_json(msg="fingerprint must be 40 hexadecimal digits", **result)
    scratch = tempfile.mkdtemp(prefix="spack-gpg-key-")
    try:
        # Both trusts answer Spack's question in any case (consent=True):
        # asking for a key, or for the mirrors' keys, is the consent.
        spack = Spack(module, params["spack"], yes_to_all=params["yes_to_all"])
        result["spack_version"] = ".".join(str(part) for part in spack.require_version())
        before = trusted(spack)
        expected = set()  # type: set[str]
        if params["key"] and not (wanted and wanted in before):
            path = key_file(module, params["key"], scratch)
            found = file_fingerprints(module, path)
            if found is not None:
                if not found:
                    module.fail_json(msg="%s holds no OpenPGP public key" % params["key"], **result)
                if wanted and wanted not in found:
                    module.fail_json(
                        msg="%s holds the key %s, not %s" % (params["key"], ", ".join(found), wanted),
                        **result,
                    )
                expected = set(found) - before
            elif wanted:
                expected = {wanted}
            else:
                result["previewed"] = False
            if not module.check_mode and (found is None or expected):
                spack.run(spack.answered(["gpg", "trust", path], words=2, consent=True))
        if params["from_mirrors"]:
            if module.check_mode:
                result["previewed"] = False
            else:
                keys = ["buildcache", "keys", "--install", "--trust"]
                spack.run(spack.answered(keys, words=2, consent=True))
        if module.check_mode:
            result["trusted"] = sorted(expected)
        else:
            after = trusted(spack)
            result["trusted"] = sorted(after - before)
            missing = (expected | ({wanted} if wanted else set())) - after
            if missing:
                module.fail_json(
                    msg="Spack does not trust %s afterwards" % ", ".join(sorted(missing)), **result
                )
    except SpackError as error:
        module.fail_json(msg=str(error), **result)
    finally:
        import shutil

        shutil.rmtree(scratch, ignore_errors=True)
    result["changed"] = bool(result["trusted"])
    module.exit_json(**result)


if __name__ == "__main__":
    main()
