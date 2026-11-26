#!/usr/bin/python
# Copyright: Contributors to the infrastructurebuilder.csis_spack collection
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: spack_checkout
short_description: Install Spack at a path, at a version, by a shallow git clone
version_added: 0.0.4
description:
  - Puts Spack at O(path), at the O(version) named, the way Spack's own
    documentation installs it, a shallow C(git clone). There is no build
    step; the checkout is the installation, and C(<path>/bin/spack) is the
    executable.
  - What it does depends on what is at O(path). Nothing there, or an empty
    directory, and Spack is installed and a change is reported. A Spack
    already at the version named is left alone and no change is reported,
    whether this module installed it or a person did. A Spack at another
    version fails the task with nothing changed; this module does not move
    a Spack to another version. Anything else (a file, a directory that is
    not a Spack) fails the task with nothing changed.
  - A Spack at the version named whose own files have been edited is left
    alone too, and a warning names the edited files.
  - Whether a Spack is at the version named is decided without the network, so a repeat run
    needs none. For a tag, its commit is checked out; for a branch, that
    branch is checked out, however far the source's branch has moved since;
    for a commit, it is checked out.
  - After an install, and on every run, C(<path>/bin/spack --version) must
    report Spack 1.0 or later, or the task fails. An install that reports an
    older version is not left at O(path).
  - When O(path) does not exist, Spack is cloned into a hidden directory
    beside it, C(.<name>.install-*), and moved into place only once it is
    complete, so a stopped run never leaves something that looks like a
    Spack. A run killed during an install can leave that hidden directory
    behind; later runs ignore it, and it may be deleted. When O(path) is an
    empty directory, Spack is cloned into it in place, which keeps the
    directory's ownership and mode; if that is stopped part-way, the next
    run finds a directory that is not a Spack and fails, saying so.
  - Missing directories above O(path) are made, owned by the user the task
    runs as, with that user's umask. A symbolic link at O(path) is followed,
    and what it points to is judged as if it were O(path).
  - Spack's package recipes, which Spack 1.0 and later keep in a repository
    of their own, are not fetched or configured. Spack fetches them the first
    time it needs them; a site without the network sets a recipe repository
    of its own with a C(config) step of the C(setup) role (or the
    M(infrastructurebuilder.csis_spack.spack_config) module).
  - Needs C(git) 2.18 or later on the node. Spack's other prerequisites are
    not installed.
  - Two tasks installing to the same O(path) at the same time are not
    supported. A fetch that hangs is bounded only by the task's own
    C(timeout) or C(async).
  - Supports check mode, in which nothing is fetched or written. Every
    command is run as a list of arguments, never through a shell.
author:
  - infrastructurebuilder (@infrastructurebuilder)
options:
  version:
    description:
      - A tag or a branch of O(source), such as C(v1.2.0) or C(releases/v1.2),
        or a commit, given by its full 40-digit hash.
      - Any 7 to 39 hexadecimal digits are taken for a short commit hash and
        refused, since git cannot fetch a commit by a short hash; a tag or a
        branch so named is refused too.
    type: str
    required: true
  path:
    description:
      - The directory Spack is installed in. It must be absolute.
    type: path
    required: true
  source:
    description:
      - The git repository to fetch Spack from. Any address C(git) accepts
        may be given (C(https://), C(ssh://), C(user@host:path), C(file://),
        or a path on the node); whatever access it needs (a key, an agent, a
        certificate) is the node's.
      - The source is trusted as given; nothing fetched is verified.
      - An C(http://) or C(https://) address that holds a user name or a
        password is refused before anything runs, so that the credential is
        not shown in the task's output, returned, or written into the Spack's
        own git configuration. Use a git credential helper or an SSH key.
    type: str
    default: https://github.com/spack/spack.git
notes:
  - The C(setup) role carries this module out as its C(spack) step.
seealso:
  - module: infrastructurebuilder.csis_spack.spack_config
"""

EXAMPLES = r"""
- name: Install Spack v1.2.0 at /opt/spack
  infrastructurebuilder.csis_spack.spack_checkout:
    version: v1.2.0
    path: /opt/spack
  register: spack_installed

- name: Use the Spack it installed
  infrastructurebuilder.csis_spack.spack_config:
    spack: "{{ spack_installed.spack }}"
    settings:
      config:
        build_jobs: 8

- name: Install it from a site's own mirror of Spack's repository, through a proxy
  infrastructurebuilder.csis_spack.spack_checkout:
    version: v1.2.0
    path: /opt/spack
    source: https://git.example.org/mirrors/spack.git
  environment:
    HTTPS_PROXY: http://proxy.example.org:3128
"""

RETURN = r"""
path:
  description: The O(path) given.
  returned: always
  type: str
spack:
  description: The executable, C(<path>/bin/spack).
  returned: always
  type: str
version:
  description: The O(version) given.
  returned: always
  type: str
source:
  description: The source used, the default when none was given.
  returned: always
  type: str
found:
  description:
    - What was at O(path) before, C(nothing), C(empty), or C(spack).
  returned: when O(path) was one of those
  type: str
spack_version:
  description:
    - What C(spack --version) printed, as C(1.2.0 (63962ed9...)). Not
      returned in check mode when Spack is not installed yet.
  returned: when Spack was run
  type: str
edited:
  description: Spack's own files at O(path) that differ from the version checked out.
  returned: always
  type: list
  elements: str
"""

import os
import re
import shutil
import tempfile
from typing import Any, cast
from urllib.parse import urlsplit

from ansible.module_utils.basic import AnsibleModule

MINIMUM_GIT = (2, 18)
FULL_HASH = re.compile(r"^[0-9a-fA-F]{40}$")
SHORT_HASH = re.compile(r"^[0-9a-fA-F]{7,39}$")
# git must never wait for someone to type a user name or password.
GIT_ENVIRONMENT = {"GIT_TERMINAL_PROMPT": "0"}


class CheckoutError(Exception):
    """A reason to fail the task with nothing changed."""


class Git:
    """The node's git, run as lists of arguments."""

    def __init__(self, module):
        self.module = module
        self.executable = module.get_bin_path("git", required=True)

    def run(self, *args, **kwargs):
        """Run git; give its return code and what it printed."""
        rc, out, err = self.module.run_command(
            [self.executable, *args], environ_update=GIT_ENVIRONMENT, **kwargs
        )
        return rc, out.strip(), err.strip()

    def must(self, *args):
        rc, out, err = self.run(*args)
        if rc != 0:
            raise CheckoutError("git %s failed: %s" % (" ".join(args), err or out))
        return out

    def version(self):
        out = self.must("--version")
        found = re.search(r"(\d+)\.(\d+)(\.\d+)?", out)
        if found is None:
            raise CheckoutError("could not read git's version from %r" % out)
        return (int(found.group(1)), int(found.group(2))), found.group(0)


def holds_credential(source):
    """Whether an http(s) address has a user name or password in it."""
    try:
        parts = urlsplit(source)
    except ValueError:
        return False
    return parts.scheme in ("http", "https") and bool(parts.username or parts.password)


def describe(git, real):
    """Say what is at ``real`` when it is not a Spack, or give None when it is one."""
    if not os.path.isdir(real):
        return "%s is a file, not a directory" % real
    rc, top, _ = git.run("-C", real, "rev-parse", "--show-toplevel")
    if rc != 0:
        return "%s is a directory that is not a git repository" % real
    if os.path.realpath(top) != real:
        return "%s is a directory inside the git repository at %s" % (real, top)
    if not os.path.isfile(os.path.join(real, "bin", "spack")):
        return "%s is a git repository with no bin/spack" % real
    return None


def checked_out(git, real):
    """Say what HEAD is at: its branch, its tags, or its commit."""
    head = git.must("-C", real, "rev-parse", "HEAD")
    rc, branch, _ = git.run("-C", real, "symbolic-ref", "-q", "--short", "HEAD")
    if rc == 0 and branch:
        return head, branch, "branch %s" % branch
    rc, tags, _ = git.run("-C", real, "tag", "--points-at", "HEAD")
    if rc == 0 and tags:
        return head, None, "tag %s" % ", ".join(tags.split())
    return head, None, "commit %s" % head


def at_version(git, real, version):
    """Whether the Spack at ``real`` is at ``version``, decided without the network."""
    head = git.must("-C", real, "rev-parse", "HEAD")
    if FULL_HASH.match(version):
        return head.lower() == version.lower()
    rc, branch, _ = git.run("-C", real, "symbolic-ref", "-q", "--short", "HEAD")
    if rc == 0 and branch == version:
        return True
    rc, tagged, _ = git.run("-C", real, "rev-parse", "-q", "--verify", "refs/tags/%s^{commit}" % version)
    return rc == 0 and tagged == head


def edited_files(git, real):
    """Spack's own files that differ from the version checked out."""
    # Each line is two status letters, a space and the name; the letters may
    # begin with a space, so the output is read as git printed it.
    rc, out, err = git.module.run_command(
        [git.executable, "-C", real, "status", "--porcelain", "--untracked-files=no"],
        environ_update=GIT_ENVIRONMENT,
    )
    if rc != 0:
        raise CheckoutError("git status failed at %s: %s" % (real, err.strip()))
    return [line[3:] for line in out.splitlines() if len(line) > 3]


def clone(git, source, version, target):
    """Fetch ``version`` of ``source`` into the empty directory ``target``."""
    if FULL_HASH.match(version):
        git.must("init", "--quiet", target)
        git.must("-C", target, "fetch", "--quiet", "--depth", "1", source, version)
        git.must("-C", target, "checkout", "--quiet", "--detach", "FETCH_HEAD")
        git.must("-C", target, "remote", "add", "origin", source)
    else:
        git.must("clone", "--quiet", "--depth", "1", "--branch", version, source, target)


def empty(directory):
    """Remove what is in ``directory``, which was empty before this module wrote to it."""
    for entry in os.listdir(directory):
        full = os.path.join(directory, entry)
        if os.path.isdir(full) and not os.path.islink(full):
            shutil.rmtree(full, ignore_errors=True)
        else:
            os.unlink(full)


class Installer:
    """Installs Spack, and checks the Spack it finds or installs."""

    def __init__(self, module, git):
        self.module = module
        self.git = git

    def check(self, target):
        """Run ``<target>/bin/spack --version``; require 1.0 or later; give what it printed."""
        program = os.path.join(target, "bin", "spack")
        rc, out, err = self.module.run_command([program, "--version"])
        if rc != 0:
            raise CheckoutError("%s --version failed: %s" % (program, (err or out).strip()))
        printed = out.strip()
        found = re.match(r"(\d+)\.(\d+)", printed.split()[0]) if printed else None
        if found is None:
            raise CheckoutError("%s --version did not print a version: %r" % (program, printed))
        if (int(found.group(1)), int(found.group(2))) < (1, 0):
            raise CheckoutError(
                "%s is Spack %s; this collection needs Spack 1.0 or later" % (program, printed.split()[0])
            )
        return printed

    def into_new(self, source, version, real):
        """Install where nothing is: beside ``real``, then moved into place."""
        parent, name = os.path.split(real)
        try:
            os.makedirs(parent, exist_ok=True)
            target = tempfile.mkdtemp(dir=parent, prefix=".%s.install-" % name)
        except OSError as error:
            raise CheckoutError(
                "could not make a directory for Spack beside %s: %s" % (real, error)
            ) from error
        try:
            # mkdtemp makes it 0700; what is installed has the user's umask, as git would give it.
            mask = os.umask(0)
            os.umask(mask)
            os.chmod(target, 0o777 & ~mask)
            clone(self.git, source, version, target)
            printed = self.check(target)
            os.rename(target, real)
        except (CheckoutError, OSError) as error:
            shutil.rmtree(target, ignore_errors=True)
            if isinstance(error, OSError):
                raise CheckoutError("could not move Spack into place at %s: %s" % (real, error)) from error
            raise
        return printed

    def into_empty(self, source, version, real):
        """Install into the empty directory ``real``, in place."""
        try:
            clone(self.git, source, version, real)
            return self.check(real)
        except CheckoutError:
            empty(real)
            raise


def main():
    module = AnsibleModule(
        argument_spec=dict(
            version=dict(type="str", required=True),
            path=dict(type="path", required=True),
            source=dict(type="str", default="https://github.com/spack/spack.git"),
        ),
        supports_check_mode=True,
    )
    params = cast("dict[str, Any]", module.params)
    version, path, source = params["version"], params["path"], params["source"]
    result = dict(
        changed=False,
        path=path,
        spack=os.path.join(path, "bin", "spack"),
        version=version,
        source=source,
        edited=[],
    )  # type: dict[str, Any]
    if holds_credential(source):
        result["source"] = "(refused: it holds a credential)"
        module.fail_json(
            msg="the source holds a credential (a user name or password in its address), which would be "
            "shown and kept in the Spack's own git configuration; nothing was run. Use a git "
            "credential helper or an SSH key instead",
            **result,
        )
    if SHORT_HASH.match(version) and not FULL_HASH.match(version):
        module.fail_json(
            msg="version %r looks like a short commit hash; give the commit's full hash (40 hexadecimal "
            "digits), since git cannot fetch a commit by a short one. A tag or branch so named is "
            "refused too; nothing was run" % version,
            **result,
        )
    if not os.path.isabs(path):
        module.fail_json(msg="path must be an absolute path, not %r" % path, **result)
    try:
        git = Git(module)
        have, shown = git.version()
        if have < MINIMUM_GIT:
            raise CheckoutError("git %s is older than 2.18, the oldest this module needs" % shown)
        installer = Installer(module, git)
        real = os.path.realpath(path)
        if not os.path.exists(real):
            result["found"] = "nothing"
            if not module.check_mode:
                result["spack_version"] = installer.into_new(source, version, real)
            result["changed"] = True
        elif os.path.isdir(real) and not os.listdir(real):
            result["found"] = "empty"
            if not module.check_mode:
                result["spack_version"] = installer.into_empty(source, version, real)
            result["changed"] = True
        else:
            what = describe(git, real)
            if what is not None:
                raise CheckoutError("%s: it is not a Spack. Nothing was changed" % what)
            result["found"] = "spack"
            if not at_version(git, real, version):
                _, _, where = checked_out(git, real)
                try:
                    printed = installer.check(real)
                except CheckoutError as error:
                    printed = "(it did not run: %s)" % error
                raise CheckoutError(
                    "%s holds Spack at another version: it is at %s, and spack --version prints %s; "
                    "%s was asked for. Nothing was changed: this module does not move a Spack to "
                    "another version" % (path, where, printed, version)
                )
            result["spack_version"] = installer.check(real)
            result["edited"] = edited_files(git, real)
            if result["edited"]:
                module.warn(
                    "the Spack at %s is at %s, but these of its own files have been edited: %s. "
                    "Nothing was changed" % (path, version, ", ".join(result["edited"]))
                )
    except CheckoutError as error:
        module.fail_json(msg=str(error), **result)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
