# Changelog

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

Their plans are kept, as history only, in
[ATTIC/COLL-INPROGRESS/](ATTIC/COLL-INPROGRESS/).
