# Feature Specification: The first modules: an environment, and a build cache

**Feature Branch**: `feature/spack-env-module`, until the history was reset on 2026-11-18

**Created**: 2026-11-13 (planned and built); written as a spec 2026-11-27

**Status**: Done 2026-11-13 (retrospective, written 2026-11-27 from
`ATTIC/PLAN.md`): `just test` (45 tests) and `just full-test` passed;
released the same day as the development version 0.1.0, withdrawn
2026-11-18; its work is in 0.0.1, the first release (see
[CHANGELOG.md](../../CHANGELOG.md)).

**Input**: The operator's "do the module plan", on 2026-11-13. The plan
was the section "The first modules: an environment, and a build cache" of
the repository's `PLAN.md`, retired to the ATTIC on 2026-11-17. This spec
carries what that section decided and what was built, so that it stands
without the ATTIC. It was written on the operator's word, which allowed the
ATTIC to be read for this one task.

**Context**: The Cloud Sandbox's `sandbox-provisioning` wrote its Spack
environment's `spack.yaml` from a template. What was left of its
`spack_environment` role was three shell tasks. Each called Spack and
worked out whether anything changed by hashing before and after:

| Task in `spack_environment` | Spack command | How it reported a change |
| --- | --- | --- |
| Work out what has to be built | `spack -e <env> concretize --force --fresh` | `spack.lock` hashed before and after |
| Build and install the environment | `spack -e <env> install <spack_opts>`, under `async`, for hours | the hashes `spack find` lists, before and after |
| Regenerate the module files | `spack -e <env> module tcl refresh --delete-tree -y` | every file under Spack's default module root hashed |

Each task loaded the Intel modules first (`module load ...`), because the
original script ran with them loaded. None supported `--check`. The
operator tools in `sandbox-ops` pushed to the S3 build cache with three
hand-written scripts around `spack buildcache push`. This work makes those
steps modules: Spack's own commands, called with their machine-readable
output where they have one, with Ansible's change reporting and check mode.

## Clarifications

### Session 2026-11-13

Asked one at a time, before any work depended on them. Each time the
operator took the default offered.

- Q: Should the environment be one module, `spack_env`, with a `state`, or
  three small modules (`spack_concretize`, `spack_install`,
  `spack_module_refresh`) that a role chains? → A: One module, `spack_env`,
  with `state`.
- Q: Should pushing to a build cache be a module of its own, an option of
  `spack_env`, or left out of this work? → A: A module of its own,
  `spack_buildcache_push`.
- Q: A module cannot run `module load`, which is a shell function. Should
  the role work out the environment once (a task that runs `module load`
  and prints the resulting environment as JSON) and hand it to the modules
  with Ansible's `environment:` keyword, or should the modules take a
  `shell_init` option (lines run in bash before Spack)? → A: The role works
  it out once and hands it over with `environment:`. The modules run no
  shell.
- Q: Where does the integration test run: on the local machine, with
  Spack's user configuration and caches kept in `.tmp/`, or in an
  AlmaLinux 10 container, like `sandbox-provisioning`'s test? → A: On the
  local machine, with Spack's configuration and caches in `.tmp/`.
- Q: Which Spack versions are accepted: Spack 1.0 or later, tested with
  v1.2.0 (the version the Cloud Sandbox pins), or only v1.2.x, failing on
  any other? → A: 1.0 or later, tested with v1.2.0.

"The role" in the third answer is the site's own role (in 2026-11-13, the
Cloud Sandbox's `spack_environment`). The collection had no role then. The
`setup` role and its `environment` step kind (the module
`shell_environment`), which do this work inside the collection, came on
2026-11-14 with the development version 0.3.0.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A site builds its environment with a module, and a repeat run says nothing changed (Priority: P1)

A site has written its environment's `spack.yaml` with Ansible's
`template`. It runs one task, `spack_env`, naming the environment's
directory. The environment is concretized, installed and its module files
regenerated. The result says which of those changed something: a new
`spack.lock`, the specs newly installed, the module systems whose files
changed. Run again with nothing new, it reports no change.

**Why this priority**: it replaces the three shell tasks that hashed files
before and after, and is the reason for the work.

**Independent Test**: against the real Spack, an environment of one small
package installed with `install_args: [--fake]`: the first run reports a
change, the second none.

**Acceptance Scenarios**:

1. **Given** an environment that has never been concretized, **When**
   `spack_env` runs with `state: installed` and `modules: [tcl]`, **Then**
   it reports `concretized: true`, lists the package and its dependencies
   under `installed`, lists `tcl` under `modules_refreshed`, and reports a
   change.
2. **Given** the same environment and the same task, **When** it runs a
   second time, **Then** `concretized` is false, `installed` and
   `modules_refreshed` are empty, and it reports no change.
3. **Given** `state: concretized`, **When** the task runs, **Then** the
   environment is concretized and nothing is installed.
4. **Given** a build that fails, **When** the task runs, **Then** it fails
   with the end of Spack's output, and the install's output is kept in its
   log file.

---

### User Story 2 - A site previews what a build would do (Priority: P2)

Before a run that may build for hours, a site runs the same task in check
mode. It learns whether `spack.lock` would change and which specs would be
installed. Nothing is installed, and the environment is not touched.

**Why this priority**: the shell tasks had no check mode. A preview is what
makes a long build safe to run from a playbook, but the build itself comes
first.

**Independent Test**: check mode against the real Spack before the first
run: a change is reported, and the environment has no `spack.lock`
afterwards.

**Acceptance Scenarios**:

1. **Given** an environment never concretized, **When** `spack_env` runs in
   check mode, **Then** it reports `concretized: true` and the specs that
   would be installed, and the environment still has no `spack.lock`.
2. **Given** an environment already built by the same task, **When** it runs
   in check mode, **Then** it reports no change.

---

### User Story 3 - A site pushes what it built to a build cache (Priority: P3)

After a build, a site runs `spack_buildcache_push`, naming the environment
and a mirror. The environment's installed packages that the mirror lacked
are pushed to it, signed with a key already in the node's GPG keyring, or
unsigned. The result names what was pushed. A second push reports no
change. In check mode it says what would be pushed, and pushes nothing.

**Why this priority**: it replaces three hand-written scripts of the
operator's. It is used less often than the build, and needs the build
first.

**Independent Test**: against the real Spack, a push of the environment of
User Story 1 to a mirror in a local directory with `unsigned: true`: the
first push reports the package, the second reports no change.

**Acceptance Scenarios**:

1. **Given** a built environment and an empty mirror, **When**
   `spack_buildcache_push` runs, **Then** the packages are on the mirror,
   `pushed` lists them, and it reports a change.
2. **Given** the same mirror, **When** it runs again, **Then** it reports no
   change.
3. **Given** a mirror that lacks some packages, **When** it runs in check
   mode, **Then** `pushed` lists those it would push, and nothing is pushed.

---

### Edge Cases

- **A directory with no `spack.yaml`**: both modules refuse it, saying it is
  not a Spack environment.
- **Spack before 1.0**: both modules refuse it, naming the version found.
- **Externals** (packages the site has and Spack does not build) are never
  reported as installed, and never pushed.
- **A new `spack.lock` with nothing new to install** is a change
  (`concretized`).
- **The time Spack writes into each module file.** Spack stamps every module
  file with the time it wrote it, so every refresh changes every file. The
  time is left out when module trees are compared, so regenerating files
  that are otherwise the same is not reported as a change (research R7).
- **Module files were regenerated on every run** in 0.1.0, after the
  install, whether anything had changed or not; with `delete_tree: true`
  the tree was removed first. The result reported it correctly, but the run
  was not a no-op. *Changed later:* the development version 0.2.0
  (2026-11-14) added `refresh_modules`, whose default, `when_needed`,
  regenerates only when needed; this is in 0.0.1.
- **An unknown mirror name**: `spack_buildcache_push` fails, naming the
  mirrors Spack knows. A path or URL is taken as it is.
- **`key` and `unsigned` together**: refused.
- **`update_index: true`** rebuilds the mirror's index on every run. That
  alone is not reported as a change.
- **`force: true`** pushes every package again on every run, and so reports a
  change every time. In 0.1.0 `force` was a plain boolean, and nothing said
  so in the output. *Changed later:* 0.2.0 made it warn, and added
  `force: once`.
- **Check mode's copy of the environment** is made from the environment's
  directory alone, so a file that `spack.yaml` names by a relative path
  outside it (`include:`, `develop:`) is not found there. This was known and
  left as it is (recorded 2026-11-14).
- **The signing key** is never handled by the module. It is in the node's
  GPG keyring, put there by hand.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The collection MUST have a module, `spack_env`, that brings an
  existing Spack environment to a state: `concretized`, or `installed` (the
  default). The environment's `spack.yaml` is not its business; a site
  writes it with `template`.
- **FR-002**: `spack_env` MUST take `path` (the environment's directory;
  required), `spack` (the executable, as a path or a name looked up on
  `PATH`; default `spack`), `state`, `fresh` (concretize with `--fresh`;
  default true, as the Cloud Sandbox did), `install_args` (a list added to
  `spack install` as it is; default none), `modules` (the module systems to
  regenerate, `tcl` or `lmod`; default none), `delete_tree` (regenerate with
  `--delete-tree`; default true) and `log_file` (where the install's output
  is kept; default `log.install` in the environment's directory).
  *Changed later:* `refresh_modules` was added in 0.2.0 (2026-11-14), and
  `yes_to_all` in 0.0.3 ([spec 003](../003-mirror-keys-yes-to-all/spec.md)).
- **FR-003**: `spack_env` MUST concretize with `spack -e <path> concretize
  --force` (and `--fresh` when `fresh` is true), and for `state: installed`
  install with `spack -e <path> install <install_args>`, then regenerate the
  module files of each system in `modules` with `spack -e <path> module
  <system> refresh -y` (and `--delete-tree` when `delete_tree` is true).
- **FR-004**: `spack_env` MUST report each kind of change on its own:
  `concretized` when `spack.lock` changed; `installed`, the specs newly
  installed (their names and hashes, from `spack find --json` before and
  after, externals left out); `modules_refreshed`, the module systems whose
  files changed, compared without the time Spack writes into each file.
  `changed` MUST be true when any of the three is, and false otherwise.
- **FR-005**: `spack_env` MUST support check mode by concretizing a copy of
  the environment in a temporary directory, and reporting whether
  `spack.lock` would change and which specs of the new lock are not
  installed. Nothing is installed, and the environment itself is not
  touched. *Changed later:* since 0.2.0 check mode also says whether the
  module files would be regenerated, and reports them as changing only
  where that is certain.
- **FR-006**: `spack_env` MUST run under Ansible's `async` like any module,
  and its result MUST name the log file of the install (`log_file`).
  *Changed later:* the development version 0.3.1 (2026-11-14) documented
  that Ansible refuses `async` with check mode, and gave the form that
  previews; this is in 0.0.1.
- **FR-007**: `spack_env` MUST also return the environment's root specs and
  their hashes (`roots`, from `spack.lock`) and the version of Spack that
  was run (`spack_version`).
- **FR-008**: The collection MUST have a module, `spack_buildcache_push`,
  that pushes an environment's installed packages to a mirror. It MUST take
  `env` (the environment's directory; required), `mirror` (a mirror Spack
  knows by name, or a path or URL; required), `key` or `unsigned` (not
  both), `update_index`, `only` (`package` or `dependencies`), `force` and
  `spack`. *Changed later:* `force` became `true`, `false` or `once` in
  0.2.0; `yes_to_all` was added in 0.0.3 (spec 003).
- **FR-009**: `spack_buildcache_push` MUST report a change only when a
  package was pushed that the mirror did not have, and MUST name those
  packages (`pushed`: name and hash) and the mirror's URL (`mirror_url`).
  As built in 0.1.0, a real run learned what it pushed from Spack's own
  output: the `Pushed <spec>/<short hash>` line Spack v1.2.0 prints for each
  package, or its "All specs are already in the buildcache" (research R5). *Changed later:* 0.2.0 learns it from the mirror,
  asking `spack buildcache check` before and after the push, so that a Spack
  that words its output otherwise is still reported rightly.
- **FR-010**: In check mode `spack_buildcache_push` MUST list what would be
  pushed, by asking `spack buildcache check` which of the environment's
  packages the mirror lacks, with externals left out and `only` applied, and
  MUST push nothing.
- **FR-011**: `spack_buildcache_push` MUST NOT handle a key. Signing uses a
  key already in Spack's GPG keyring on the node.
- **FR-012**: Both modules MUST run Spack through one shared runner, in
  `plugins/module_utils/spack.py`, which runs Spack with `-e <environment>`,
  as a list of arguments and never through a shell, collects its output,
  and turns a failure into a module failure carrying the command and the end
  of the output.
- **FR-013**: Both modules MUST use Spack's machine-readable output where it
  has one (`spack.lock`, `find --json`, `buildcache check -o`), not Spack's
  Python internals.
- **FR-014**: What Spack needs around it, such as loaded environment
  modules, MUST be given to the modules with the task's `environment:`
  keyword. No module takes lines of shell to run first (Clarifications).
- **FR-015**: Both modules MUST refuse a Spack older than 1.0 and accept any
  later one. They are tested against v1.2.0. *Changed later:* spec 003 found
  that other modules' commands differ on 1.0 and 1.1, added the table of
  those differences (`BEHAVIOUR`, in the shared runner), and runs the
  integration tests against the real 1.0.0, 1.1.0 and 1.2.0.
- **FR-016**: Each module MUST have `DOCUMENTATION`, `EXAMPLES` and `RETURN`.
  The README's "What it holds" MUST describe both, and `CHANGELOG.md` MUST
  have an entry for the version. *Changed later:* the examples of 0.1.0
  named the Cloud Sandbox's paths and names; 0.3.0 made them neutral, and a
  test has held the collection to that since. 0.0.1's `CHANGELOG.md`
  replaced the 0.1.0 entry, and every `version_added` became 0.0.1
  ([spec 001](../001-galaxy-publish/tasks.md), T021).

### Key Entities

- **Environment**: a directory holding `spack.yaml`, and once concretized,
  `spack.lock`. Named by `path` (`spack_env`) or `env`
  (`spack_buildcache_push`).
- **Concrete spec**: a package with its hash, as `spack.lock` and
  `spack find --json` give it; an external is marked as one.
- **Module tree**: the module files under a module system's root, compared
  by a digest that leaves out the time Spack wrote each file.
- **Mirror**: a build cache, named as Spack knows it, or by a path or URL.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Against the real Spack v1.2.0, a second run of each module with
  the same input reports no change.
- **SC-002**: Against the real Spack v1.2.0, check mode run before the first
  run reports what would change, and touches nothing: no `spack.lock`, no
  install, no push.
- **SC-003**: A push to a mirror in a local directory is reported once: the
  first push names the package, the second reports no change.
- **SC-004**: Every option, the change reporting both ways, check mode and
  failure are held by unit tests against the stand-in `spack`, run through
  Ansible itself (45 tests on 2026-11-13).
- **SC-005**: `ansible-test sanity` passes for both modules, which also
  checks their documentation against their options.
- **SC-006**: `just build` makes the collection's tarball holding both
  modules, and it installs.

## Assumptions

- This spec is written after the fact, from the record in `ATTIC/PLAN.md`
  and the code as it stands. The commits of 0.1.0 are not in the repository
  any more: its history was reset to a single commit on 2026-11-18. Where
  the record does not say when an option or a return value of today's
  modules was added, and no later plan or spec records adding it, this spec
  takes it as 0.1.0's (`log_file`, `lmod`, `roots`, `mirror_url`, the
  refusal of an unknown mirror name).
- The versions 0.1.0, 0.2.0, 0.3.0 and 0.3.1 named here were development
  versions, tagged 2026-11-13 to 2026-11-14 and withdrawn on 2026-11-18,
  when the first release became 0.0.1. None was published to Galaxy.
  0.1.0's tag message was "spack_env and spack_buildcache_push"
  ([spec 001](../001-galaxy-publish/spec.md), Assumptions).
- A site writes its environment's `spack.yaml` itself, with `template`.
- The signing key is put into the node's GPG keyring by the site, by hand or
  by a task of its own.
- The constitution was ratified on 2026-11-17, after this work.
  [plan.md](plan.md) checks the work against it all the same.

## Out of Scope

- **Using the modules in the Cloud Sandbox's `sandbox-provisioning`.** That
  followed a release, as a stage of the Cloud Sandbox's own: its
  `requirements.yml` pins the collection's version, `just init` installs it
  into `.collections/`, the three shell tasks become module calls with
  their traceability comments, and its `units.toml` gains the collection.
  The work is in that repository.
- **Publishing.** No tag, no push and no upload to Ansible Galaxy until the
  operator says so. The tag 0.1.0 was made and pushed to the repository on
  2026-11-13; nothing went to Galaxy. The first version there was 0.0.1,
  uploaded on 2026-11-19 (spec 001).
- **The site and user Spack configuration** (`spack compiler find`,
  `external find`, mirrors, keys). At the time this was the Cloud Sandbox's
  `spack` role's, and discovery rather than state. *Changed later:* 0.3.0
  brought it into the collection as the `setup` role and its modules.
