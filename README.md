# infrastructurebuilder.csis_spack

An Ansible collection for [Spack](https://spack.io): set a Spack up
(settings, compilers, mirrors, keys), then concretize and install its
environments, regenerate their module files and push what they built to
a build cache, with Ansible's own change reporting and check mode,
instead of shell tasks that compare checksums before and after.

**The collection knows how to do each kind of thing to Spack, and nothing
about what any site wants done.** No package, compiler, mirror or path is
built into its modules or its role; a test holds it to that. What a site
wants is configuration it gives.

It was begun for the IOOS Cloud Sandbox, whose own configuration is one
of the examples, kept apart from the code.

## Status

0.0.3 (2026-11-25): eight modules, a role and a filter, tested against a
stand-in for Spack and against the real Spack 1.0.0, 1.1.0 and 1.2.0. It is on
[Ansible Galaxy](https://galaxy.ansible.com/ui/repo/published/infrastructurebuilder/csis_spack/)
as `infrastructurebuilder.csis_spack`; the first release there was 0.0.1
(2026-11-18).
[CHANGELOG.md](CHANGELOG.md) says what each version holds. (The
development versions this repository tagged before, 0.1.0 to 0.3.1, were
withdrawn on 2026-11-18; the changelog says what became of them.)

## Installing it

From Ansible Galaxy, in a `requirements.yml`:

```yaml
collections:
  - name: infrastructurebuilder.csis_spack
    version: ">=0.0.1,<0.1.0"
```

From this repository at a release tag:

```yaml
collections:
  - name: https://github.com/infrastructurebuilder/ansible-collection-csis-spack.git
    type: git
    version: "0.0.3"
```

Then `ansible-galaxy collection install -r requirements.yml`.

## What it holds

### Setting a Spack up

The **`setup` role** carries out one variable, `spack_setup`: a list of
steps, in the order written, which is a site's shell script as data.
[Its README](roles/setup/README.md) describes the list; complete ones are
under [docs/examples/](docs/examples/). Each kind of step is a module that
can also be used alone:

| Module | What it does |
| --- | --- |
| `spack_config` | Declares settings in one configuration scope: compared with what is there, changed only where different, a list set exactly, previewed in check mode |
| `spack_mirror` | Declares one mirror; a different one of the same name is replaced |
| `spack_gpg_key` | Trusts a public key from a file or URL (optionally only with a given fingerprint), or the keys the mirrors publish |
| `spack_detect` | Has Spack look for compilers and installed packages, and fails when what `require` names is not registered afterwards |
| `spack_command` | Runs any Spack command, for what the others do not cover, with a stated way to tell whether it changed something |
| `shell_environment` | Captures the environment some shell lines produce (loading environment modules, say), to give to the tasks that need it |
| `spack_checkout` | Installs Spack itself at a path, at a version, by the shallow git clone Spack's documentation uses, and leaves a Spack already there at that version alone. The role's `spack` step, which can only be its first, so that the later steps run the Spack it installed |

Every module that runs Spack, and every step of the role but `environment`,
takes `yes_to_all` (off unless asked for): Spack's confirmations, which
would fail under Ansible, are then answered "yes" for each command that
offers `--yes-to-all`, removals and overwrites included.
[The role's README](roles/setup/README.md#answering-spacks-confirmations-yes_to_all)
says how, and when not to.

Declaring and discovering are kept apart on purpose. A setting, a mirror
or a key is a state that can be compared and previewed. Detection depends
on the machine and on the environment it runs in, cannot be previewed, and
says nothing when it finds nothing; `require` is how a playbook says what
it must find.

### Building an environment

- **`spack_env`** brings an existing environment to a state:
  `concretized`, or `installed` (the default), and regenerates the
  module files of the systems named in `modules`. Each kind of change is
  reported on its own: `concretized` when `spack.lock` changed,
  `installed` with the specs newly installed, `modules_refreshed` with
  the module systems whose files changed. Module files are regenerated
  only when they need to be (`refresh_modules: when_needed`, the
  default): when the run concretized or installed something, or when
  `spack.lock`, the modules configuration or the module files themselves
  have changed since it last regenerated them, so a file deleted or
  edited by hand is put back, and a run with nothing to do touches
  nothing. In check mode it concretizes a copy of the environment in a
  temporary directory and says what would change and what would be
  installed, building nothing.
- **`spack_buildcache_push`** pushes an environment's installed packages
  to a mirror (by name, path or URL), signed with a key already in
  Spack's keyring, or unsigned. It reports a change only for packages
  the mirror gained, which it learns by asking the mirror
  (`spack buildcache check`) before and after, not from what Spack
  prints; in check mode it asks once and pushes nothing. `force: once`
  overwrites each package on a mirror one time; `force: true` overwrites
  everything on every run, and says so in a warning.

Both call the `spack` command, without a shell, and read its
machine-readable output (`find --json`, `spack.lock`,
`buildcache check -o`), not Spack's Python internals, which change
between releases. Both refuse Spack before 1.0.

### What the modules keep in the environment's directory

Two small files in the environment's `.spack-env/` directory, so that a
repeat run can tell there is nothing to do:
`csis_spack.modules.json` (what the module files were last regenerated
from) and `csis_spack.pushed.json` (which packages `force: once` has
overwritten on which mirror). `.spack-env/` is Spack's own directory;
Spack leaves files it does not know there alone, and removes them with
the environment. Deleting either file is safe: the next run regenerates,
or overwrites once more.

### One module tree, several environments

Spack's default module root is shared by every environment of that
Spack, and `delete_tree: true` (the default, as `spack module refresh
--delete-tree`) removes the whole tree before regenerating one
environment's files. With more than one environment, give each its own
root (`modules:default:roots` in its `spack.yaml`) or set
`delete_tree: false`; otherwise each environment's run undoes the
other's, and neither is ever "not needed".

The environment's `spack.yaml` itself is not this collection's business:
it is a file, and Ansible's `template` writes it. What Spack needs around
it, such as loaded environment modules, is given with the task's
`environment:` keyword.

```yaml
- name: Build the environment and regenerate its Tcl module files
  infrastructurebuilder.csis_spack.spack_env:
    path: /opt/spack-environments/base
    spack: /opt/spack/bin/spack
    modules: [tcl]
  environment: "{{ mycompiler_environment }}"
  # Asynchronous for the build, and not when previewing: Ansible refuses
  # async in check mode.
  async: "{{ 0 if ansible_check_mode else 86400 }}"
  poll: "{{ 0 if ansible_check_mode else 60 }}"

- name: Push what it built to the mirror
  infrastructurebuilder.csis_spack.spack_buildcache_push:
    env: /opt/spack-environments/base
    spack: /opt/spack/bin/spack
    mirror: site-cache
    key: <the key's fingerprint>
    update_index: true
```

`ansible-doc infrastructurebuilder.csis_spack.spack_env` gives every
option.

## Requirements

- ansible-core 2.16 or later; it is tested with the 2.16 series, which
  RHEL 10 ships.
- Spack 1.0 or later on the managed node, unless the role's list starts
  with a `spack` step, which installs it; that step, and `spack_checkout`,
  need `git` 2.18 or later on the node. The collection is tested against
  the real Spack 1.0.0, 1.1.0 and 1.2.0 (the version the Cloud Sandbox pins,
  which the tests are written to). Where they differ in the commands the
  collection runs, the collection follows the version it finds; the
  differences are listed in `plugins/module_utils/spack.py` (`BEHAVIOUR`).
  On Spack 1.1, a configuration scope whose directory does not exist yet
  (`~/.spack`, `/etc/spack`) cannot be written to until it is made. A Spack
  newer than 1.2 is taken to behave as 1.2; pin yours.

## Working on it

You need `just` and `uv`.

```sh
just init        # the tool environment: ansible-core 2.16, ruff, pyright, pytest
just build       # dist/infrastructurebuilder-csis_spack-<version>.tar.gz
just test        # ruff, pyright, the unit tests against a stand-in spack (a few minutes), and a build that installs
just full-test   # the same, then the modules and the role against the real Spack 1.0.0, 1.1.0 and 1.2.0, then ansible-test sanity
just integration # only the modules and the role against the real Spacks: for seeing a new integration test fail first
just format      # rewrite the code in ruff's format, which lint checks
just import-check  # the tarball through galaxy-importer, the checks Galaxy runs on an upload
just release     # full-test and the tarball; then tag it with the bare version, as 0.0.1
just publish     # from the tag: upload to Galaxy (needs GALAXY_API_KEY)
```

### Publishing a release

A release is published to Galaxy from its tag, in either of two ways,
which both run `just publish`:

- **From your machine:** check the tag out, set `GALAXY_API_KEY` in your
  environment (from Galaxy's API token page; never in a file in this
  repository), and run `just publish`.
- **From GitHub:** push the tag. The workflow
  [publish.yml](.github/workflows/publish.yml) runs `just test`, then
  `just publish`, with the repository secret `GALAXY_API_KEY` (or the same
  secret in the `galaxy` environment, which can be made to wait for a
  reviewer's approval).

`just publish` refuses without the key, unless HEAD is the tag of
`galaxy.yml`'s version, and with changes in the working tree. A version
Galaxy already has is left alone, with a message, so publishing one both
ways uploads it once. Galaxy keeps every version for good: a version
number is never used twice. `GALAXY_SERVER` names another server with
Galaxy's API, such as a private Automation Hub.

## Licence

GNU General Public License v3.0 or later; see [LICENSE](LICENSE). It is
the licence of Ansible and of the community collections.
