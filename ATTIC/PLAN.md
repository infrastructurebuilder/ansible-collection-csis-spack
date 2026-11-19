# Plans

**This file is closed, and was retired to the ATTIC on 2026-11-17.** Since
then this repository plans its work with Spec Kit: the rules are in
[.specify/memory/constitution.md](../.specify/memory/constitution.md), and each
piece of work is a spec under [specs/](../specs/). What follows is the record of
the plans made before then. No new plan is written here.

## Collection stages (2026-11-14 to 2026-11-17)

*Status:* closed 2026-11-17. Stage 1 executed and released as 0.2.0 on
2026-11-14; stage 2 executed and released as 0.3.0 the same day; stages 3 and
4 executed 2026-11-14, 4 released as 0.3.1; stage 5 begun 2026-11-16 and
carried on as the spec
[specs/001-galaxy-publish/](../specs/001-galaxy-publish/spec.md).

Larger changes to the collection were planned one file per stage, each
executed on the operator's `do coll <n>` after its decisions had been asked
one at a time. The stage files were retired to
[COLL-INPROGRESS/](COLL-INPROGRESS/), beside this file, on 2026-11-17, and
are history only.

- [COLL-STAGE-1.md](COLL-INPROGRESS/COLL-STAGE-1.md): repeat runs that do
  nothing and say so (module files regenerated only when needed,
  `force` left on, what was pushed known from the mirror). Released as
  0.2.0.
- [COLL-STAGE-2.md](COLL-INPROGRESS/COLL-STAGE-2.md): setting Spack up
  from one piece of configuration: an ordered list of steps (settings,
  discovery, mirrors, trusted keys, plain commands), each a module,
  carried out by a `setup` role that knows nothing about any site.
  Released as 0.3.0.
- [COLL-STAGE-3.md](COLL-INPROGRESS/COLL-STAGE-3.md): the Cloud Sandbox
  moves to 0.3.0: its pin, its `refresh_modules`, and its Spack set-up
  shell replaced by the `setup` role with two lists, validated in its
  container test with the real oneAPI. The work is in Cloud-Sandbox.
  Executed 2026-11-14; 0.3.0 needed no change.
- [COLL-STAGE-4.md](COLL-INPROGRESS/COLL-STAGE-4.md): say how to preview
  a long build (`async` and check mode). Executed 2026-11-14; on
  `develop`; released as 0.3.1 with a fix, and the sandbox pins it.
- [COLL-STAGE-5.md](COLL-INPROGRESS/COLL-STAGE-5.md): Ansible Galaxy.
  Decided 2026-11-16: publish, from the operator's machine and from a
  GitHub Actions workflow on a tag. The publishing is ready; the first
  upload, the next release, waits for the namespace. Carried on as
  [specs/001-galaxy-publish/](../specs/001-galaxy-publish/spec.md).

The order of these among the Cloud Sandbox's remaining stages is in that
repository's `PLAN.md`.

## The first modules: an environment, and a build cache (2026-11-13)

*Status:* planned and executed 2026-11-13 on `feature/spack-env-module`,
on the operator's "do the module plan"; released as 0.1.0 and pushed
2026-11-13.
The decisions are under [Decisions taken](#decisions-taken), the result
under [Outcome](#outcome).

### Why

The Cloud Sandbox's `sandbox-provisioning` writes its Spack
environment's `spack.yaml` from a template (its stage 9). What is left
of its `spack_environment` role is three shell tasks that call Spack and
work out whether anything changed by hashing before and after:

| Task in `spack_environment` | Spack command | How it reports a change today |
| --- | --- | --- |
| Work out what has to be built | `spack -e <env> concretize --force --fresh` | `spack.lock` hashed before and after |
| Build and install the environment | `spack -e <env> install <spack_opts>`, under `async`, for hours | the hashes `spack find` lists, before and after |
| Regenerate the module files | `spack -e <env> module tcl refresh --delete-tree -y` | every file under Spack's default module root hashed |

Each loads the Intel modules first (`module load ...`), because the
original script ran with them loaded. None supports `--check`. And the
operator tools in `sandbox-ops` push to the S3 build cache with three
hand-written scripts around `spack buildcache push`.

This plan makes those steps modules: Spack's own commands, called with
their machine-readable output where they have one, with Ansible's
change reporting and check mode.

### What Spack v1.2.0 offers (read from its `--help`)

- `spack -e <env> concretize [-f] [-U|--fresh] [--reuse] [-q]`:
  writes `spack.lock`.
- `spack -e <env> install [--fake] [--cache-only]
  [--use-buildcache ...] [-j N] [--only-concrete]`. `--fake` installs
  without building, which is what lets a test install in seconds.
- `spack -e <env> find --json`: the installed specs, with their hashes.
- `spack -e <env> module tcl refresh --delete-tree -y`.
- `spack buildcache push [--unsigned|--signed|--key KEY]
  [--update-index] [--only package|dependencies] [-f] <mirror> [specs]`;
  in an environment, with no specs, it pushes the environment's.

### Items

1. **`infrastructurebuilder.csis_spack.spack_env`**: bring an
   environment to a state.
   - Options: `path` (the environment directory; required), `spack`
     (the executable; default `spack` on `PATH`), `state`
     (`concretized` or `installed`, default `installed`), `fresh`
     (`--fresh` when concretizing; default true, as the sandbox does),
     `install_args` (a list passed to `spack install` as it is, for what
     the sandbox keeps in `spack_opts`), `modules` (the module systems
     to regenerate, for example `[tcl]`; default none), `delete_tree`
     (default true).
   - Changes reported separately in the result: `concretized` (when
     `spack.lock` changed), `installed` (the hashes newly installed),
     `modules_refreshed`; `changed` is any of them.
   - **Check mode:** concretize a copy of the environment in a
     temporary directory, and report what would change in `spack.lock`
     and which specs of the new lock are not installed. Nothing is
     installed and the environment itself is not touched.
   - Long builds: runs under Ansible's `async` like any module; the
     result names the log file of the install.

   **YOUR DECISION (one module or two for the environment):** one
   module, `spack_env`, with `state` (default); or three small ones
   (`spack_concretize`, `spack_install`, `spack_module_refresh`) that a
   role chains.

2. **`infrastructurebuilder.csis_spack.spack_buildcache_push`**:
   push an environment's packages to a mirror. Options: `env`, `mirror`,
   `key` or `unsigned`, `update_index`, `only`, `force`, `spack`.
   Reports `changed` when a package was pushed that the mirror did not
   have (from Spack's output and `spack buildcache list` against the
   mirror before and after). Check mode lists what would be pushed. The
   key itself is never handled by the module: it is in the node's GPG
   keyring, put there by hand, as today.

   **YOUR DECISION (pushing to a cache):** a module of its own, as
   above (default); or an option of `spack_env`; or left out of this
   plan.

3. **What surrounds Spack.** The sandbox loads the Intel modules before
   every Spack call. A module cannot run `module load`: that is a shell
   function. **YOUR DECISION (Spack's surroundings):** the role works
   out the environment once (a task that runs `module load` and prints
   the resulting environment as JSON) and hands it to the modules with
   Ansible's `environment:` keyword, so the modules stay plain
   (default); or the modules take a `shell_init` option (lines run in
   bash before Spack, as the shell tasks do now).

4. **A shared runner** in `plugins/module_utils/spack.py`: runs Spack
   with `-e`, never through a shell, collects its output, and turns a
   failure into a module failure with the last lines of the log.

5. **Tests.**
   - Unit tests (`just test`) with a fake `spack`: a small program put
     first on `PATH` that answers `concretize`, `install`, `find
     --json`, `module ... refresh` and `buildcache push` from fixture
     files and records how it was called. They cover every option, the
     change reporting both ways, check mode, and failures.
   - `ansible-test sanity` (`just full-test`) on both modules, which
     also checks their documentation against their options.
   - Integration (`just full-test`): the real Spack v1.2.0, cloned once
     into `.tmp/`, an environment holding one small package, installed
     with `install_args: [--fake]`; each module run twice, the second
     run changing nothing, check mode run before and changing nothing;
     a push to a mirror in a local directory with `unsigned: true`.

   **YOUR DECISION (where the integration test runs):** on the local
   machine, with Spack's user configuration kept in `.tmp/` (default;
   the stage 9 comparison ran this way); or in an AlmaLinux 10
   container, like `sandbox-provisioning`'s test.

6. **Which Spack.** **YOUR DECISION (Spack versions):** require Spack
   1.0 or later, and test with v1.2.0, the version the sandbox pins
   (default); or accept only v1.2.x, failing on any other.

7. **Documentation:** each module's `DOCUMENTATION`, `EXAMPLES` and
   `RETURN`; the README's "What it holds"; a `CHANGELOG.md` with 0.1.0.

### Decisions taken

Asked one at a time on 2026-11-13; each default was taken.

1. **One module for the environment:** `spack_env`, with `state`.
2. **Pushing to a cache:** a module of its own, `spack_buildcache_push`.
3. **Spack's surroundings:** the role works out the environment once and
   hands it to the modules with `environment:`; the modules run no shell.
4. **Integration test:** on the local machine, Spack's configuration and
   caches in `.tmp/`.
5. **Spack versions:** 1.0 or later, tested with v1.2.0.

### Out of scope

- Using the modules in `sandbox-provisioning`. That follows a release:
  `requirements.yml` pins the collection's tag, `just init` installs it
  into `.collections/`, the three shell tasks become module calls with
  their traceability comments, and `units.toml` gains the collection. It
  is a stage of Cloud-Sandbox's own.
- Publishing: no tag, no push, no upload to Galaxy until the operator
  says so.
- The site and user Spack configuration (`spack compiler find`,
  `external find`, mirrors, keys): the `spack` role's, and discovery
  rather than state.

### Acceptance

- `just test` and `just full-test` pass.
- `just build` makes `infrastructurebuilder-csis_spack-0.1.0.tar.gz`
  holding both modules, and it installs.

### Outcome

- `plugins/modules/spack_env.py` and `plugins/modules/spack_buildcache_push.py`,
  with `plugins/module_utils/spack.py` shared between them.
- Before writing them, Spack v1.2.0's behaviour was tried by hand on the
  local machine: concretize, `install --fake`, `find --json`, `module tcl
  refresh`, `buildcache push` twice, `buildcache check -o`. The modules
  and the stand-in `spack` (`tests/unit/fake_spack.py`) follow what it
  showed: `find --json` lists the environment's installed specs with
  externals marked; `spack.lock` and `find` agree on hashes; a push
  prints `Pushed <spec>/<short hash>` per package, or "All specs are
  already in the buildcache"; `buildcache check` lists what a mirror
  lacks, externals included, and exits 1 when anything is missing.
- **Found by the integration test:** Spack stamps every module file with
  the time it wrote it, so every refresh changes every file. Module trees
  are compared without that line (`module_tree_digest`). The same flaw is
  in the Cloud Sandbox's `spack_environment` role, and is recorded in its
  MAP.md.
- `just test`: ruff, pyright (0 errors), 45 tests against the stand-in
  run through `ansible` itself, and a build that installs.
- `just full-test`: the same; then both modules against the real Spack
  v1.2.0, where check mode reports and touches nothing, the first run
  concretizes, installs and writes module files, the second changes
  nothing, and a push to a mirror in a directory is reported once; then
  `ansible-test sanity`, which passes for both modules.

