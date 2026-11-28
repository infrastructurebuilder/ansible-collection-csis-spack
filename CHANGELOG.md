# Changelog

## Unreleased

[specs/006-known-limits](specs/006-known-limits/spec.md) and
[specs/012-remove-attic](specs/012-remove-attic/spec.md). Nothing a
playbook passes changes.

### Fixed

- `spack_env` in check mode reads the paths that `spack.yaml` gives
  relatively, in `include:` and in `develop:`, where they are. Before, the
  preview's copy failed on an include above the environment's directory
  ("Required path ... does not exist"), and recorded the copy's own path for
  a develop package, so it said the environment would concretize when a real
  run would not. The copy's relative paths are now rewritten to the real
  environment's absolute paths, with Spack's own Python, before it is
  concretized; a `spack.yaml` with neither key is previewed as before.
- `spack_buildcache_push` with `force: once` and `update_index: true`
  rebuilds the mirror's index after the forced push too. Before, when the
  mirror lacked nothing else, the push that followed sent nothing, and the
  index was not rebuilt after the packages were overwritten.

### Removed

- The repository's retired plans, the directory `ATTIC/` of the plans made
  before it adopted Spec Kit. The specs 001 and 007 to 011 hold everything
  in it, and [specs/012-remove-attic/coverage/](specs/012-remove-attic/coverage/README.md)
  records where each part went. It was never in the collection's tarball,
  so nothing a user installs changes.

### Documented

- `spack_buildcache_push`'s `update_index`: Spack rebuilds the mirror's
  index only after a push that sent something, so a repeat run changes
  nothing. An index changed by other means is not put right by such a run;
  run `spack buildcache update-index` for that, in a `command` step. Tried
  against Spack 1.0.0, 1.1.0 and 1.2.0, and held by a test against each.

## 0.0.4 (2026-11-27)

[specs/004-install-spack](specs/004-install-spack/spec.md) and
[specs/005-move-spack-version](specs/005-move-spack-version/spec.md). A
playbook written for 0.0.3 runs unchanged: a list with no `spack` step
behaves as before.

### Added

- A new module, `spack_checkout`, and the `setup` role's `spack` step that
  carries it out: Spack installed at a path, at a version (a tag, a branch,
  or a commit's full hash), by the shallow `git clone` Spack's own
  documentation uses. Nothing at the path, or an empty directory: Spack is
  installed (beside the path and moved into place, or into the empty
  directory in place). A Spack already at the version, however it got there:
  left alone, with no network needed, and a warning if its own files have
  been edited. A Spack at another version, or anything that is not a Spack:
  the step fails with nothing changed, unless `move: true` is given (below).
  The installed Spack must report 1.0 or later. The node needs
  `git` 2.18 or later; a source holding a credential is refused. Spack's
  package recipes are left to Spack, which fetches them when it first needs
  them.
- `move` (off by default), on `spack_checkout` and the `spack` step
  ([specs/005-move-spack-version](specs/005-move-spack-version/spec.md)): a
  Spack at the path at another version is moved to the version named, in
  place, forward or back, keeping everything the site added. The new version
  is cloned beside the path and checked first; the move is refused, with
  nothing changed, over Spack's own edited files or over a site's file the
  new version would replace (which git itself would overwrite without a word
  for an ignored file). `moved_from` names what was there. Nothing the old
  version built is rebuilt. Check mode contacts no source.
- In check mode the role's not-previewed message now reads "Spack is not
  installed or moved yet: check mode does not change it, so this step cannot
  be previewed".
- The `spack` step can only be the list's first. The steps after it run the
  Spack it installed, `<path>/bin/spack`, so `spack_setup_executable` is not
  needed; set to another Spack, the role refuses the list. In check mode on
  a node with no Spack, the steps after it are recorded as not previewed.
- The filter `setup_problems` takes the role's executable as an optional
  argument, and a new filter, `setup_executable`, gives the Spack a list's
  steps run.
- `docs/examples/spack-installed-by-the-role.yml`.

## 0.0.3 (2026-11-25)

[specs/003-mirror-keys-yes-to-all](specs/003-mirror-keys-yes-to-all/spec.md).
A playbook written for 0.0.2 runs unchanged.

### Fixed

- `spack_gpg_key` with `from_mirrors: true` failed against a mirror that
  publishes a key, on Spack 1.2, as it did on a RHEL 10 head node:
  `spack buildcache keys --install --trust failed (exit 3): ==> Trust key:
  <fingerprint> [y/N] ... Error: EOF when reading a line`. Spack 1.2 asks
  before trusting each key, even one it trusts already, and under Ansible
  there is no terminal to answer from. Both of the module's trusts now pass
  `--yes-to-all` on Spack 1.2 and later. The `setup` role's `gpg_key` steps
  of `from_mirrors: true` work again; the Cloud Sandbox can go back to them
  from its `command` steps.
- The collection did not work with Spack 1.0 or 1.1, which it says it
  supports; only 1.2.0 had been tested. `spack_gpg_key` with `key` failed
  there with `unrecognized arguments: -y`, and every module that read the
  configuration (`config get --json`, not in 1.0) or the trusted keys
  (`gpg list --fmt colons`, not in 1.0 or 1.1) failed too. The modules now
  follow the version they find, from a table in the shared code
  (`BEHAVIOUR`): on 1.0 the configuration is read through Spack's own
  `spack python -c`, and on 1.0 and 1.1 the trusted keys from gpg's own
  listing.
- A configuration scope whose directory does not exist yet is read as empty
  on Spack 1.1 too. Spack 1.1 cannot write to it, as it has no such scope;
  a module then fails, saying which directory to make (the modules do not
  make it).

### Added

- `yes_to_all`, on every module that runs Spack, and
  `spack_setup_yes_to_all` (with a `yes_to_all` of a step's own, which
  overrides it) on the `setup` role; off by default. On, each Spack command
  run to change something is given `--yes-to-all` where the help of the
  Spack on the node lists it, which answers "yes" to every confirmation it
  asks, removals and overwrites included. Off, nothing is run differently.

### Tests

- The integration tests run against the real Spack 1.0.0, 1.1.0 and 1.2.0,
  each cloned once into `.tmp/`; two new ones trust the keys a mirror made
  in the test publishes, through the module and through the role. The
  stand-in `spack` asks before trusting a key, as Spack 1.2 does, and plays
  1.0 and 1.1 by its `--version`.
- `just integration` runs the integration tests alone; `just format` runs
  ruff's formatter.

## 0.0.2 (2026-11-19)

Documentation only; nothing in the modules, the role or the filters
changes, and a playbook written for 0.0.1 runs as it is.

- The README says that the collection is on Ansible Galaxy, and links to
  it there. 0.0.1's README, the one Galaxy shows for that version, still
  said it was not.

## 0.0.1 (2026-11-18)

The first release, and the first version on Ansible Galaxy
([specs/001-galaxy-publish](specs/001-galaxy-publish/spec.md)).

### Building an environment

- `spack_env`: concretize and install a Spack environment, and regenerate
  its module files, with each change reported on its own and check mode.
  - `refresh_modules`: with the default, `when_needed`, module files are
    regenerated only when the run concretized or installed something, a
    module root is missing, or `spack.lock`, the modules configuration or
    the module files have changed since the module last regenerated them.
    `always` regenerates on every run. The return value `modules_reason`
    says why they were regenerated.
  - Its notes say that Ansible refuses a task that is both asynchronous
    and in check mode, and give the form that lets a build be previewed:
    `async: "{{ 0 if ansible_check_mode else 86400 }}"`, and the same for
    `poll`. Its example and the README's use it.
- `spack_buildcache_push`: push an environment's packages to a build
  cache, with check mode. What was pushed is learned from the mirror
  (`spack buildcache check` before and after), so only what the mirror
  lacked is reported. `force: once` overwrites each package on a mirror
  one time; `force: true` overwrites everything, reports a change on every
  run, and warns that it does.
- Both modules keep a small file each in the environment's `.spack-env/`
  directory.

### Setting a Spack up

- The role `setup` carries out `spack_setup`, an ordered list of steps.
  The role and the modules name no package, compiler, mirror or path; a
  test fails if one of a real site's names appears in them.
  - `spack_setup_executable` names the Spack executable (default: `spack`
    on `PATH`); `spack_setup_scope` the configuration scope of a step that
    names none (default: `site`)
    ([specs/002-setup-executable-rename](specs/002-setup-executable-rename/spec.md)).
  - `spack_setup_spack`, the executable's name in the development versions
    below, still works: a playbook that sets only that name runs what it
    names, and one that sets both runs `spack_setup_executable`.
- One module per kind of step, each usable alone: `spack_config`,
  `spack_mirror`, `spack_gpg_key`, `spack_detect`, `spack_command`,
  `shell_environment`.
  - `spack_config` with `state: absent` removes the highest mapping a
    removal would empty, so nothing empty is left behind. Spack v1.2.0
    itself leaves an emptied mapping (`install_tree: {}`) at every level.
- The filters `setup_problems` and `setup_label`, used by the role.
- Examples under `docs/examples/`, each applied by the tests. No example
  uses one site's paths and names.

### Releasing it

- `galaxy.yml` names the homepage and the documentation.
- `just import-check` runs galaxy-importer, Galaxy's own checks, on the
  tarball; `just full-test` includes it.
- `just publish` uploads a release from its tag, from the operator's
  machine or from the workflow `.github/workflows/publish.yml` on a pushed
  tag. It refuses without `GALAXY_API_KEY`, off the tag, or with changes,
  and leaves a version Galaxy already has alone.
- The README says how to install it, from Galaxy and from a tag.

Tested with ansible-core 2.16 on Python 3.12, against a stand-in for Spack
and against the real Spack v1.2.0.

## Before 0.0.1: development versions, withdrawn

From 2026-11-13 to 2026-11-14 this repository tagged four development
versions, 0.1.0, 0.2.0, 0.3.0 and 0.3.1. None was published to Galaxy. On
2026-11-18 they were withdrawn so that the first release would be 0.0.1:
their tags and their `release/*` branches were deleted from the
repository. Later the same day the repository's history was reset to a
single commit, so their commits are no longer in it either. Everything they
held is in 0.0.1, above. A `requirements.yml` that names one of those tags no
longer installs; name 0.0.1 instead.

Their plans are recorded in the specs 007 to 011 and 001; see
[specs/README.md](specs/README.md).
