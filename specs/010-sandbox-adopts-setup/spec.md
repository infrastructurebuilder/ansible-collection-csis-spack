# Feature Specification: The Cloud Sandbox replaces its Spack set-up shell with the `setup` role

**Feature Branch**: `feature/coll-stage-3` in this repository, for the plan
only, until the history was reset on 2026-11-18; the work itself was on
Cloud-Sandbox's `feature/stage-11-csis-spack-0.3.0`

**Created**: 2026-11-27, as a retrospective. The work was planned and done
on 2026-11-14.

**Status**: Done 2026-11-14 (retrospective, written 2026-11-27 from
`ATTIC/COLL-INPROGRESS/COLL-STAGE-3.md`): the Cloud Sandbox adopted the
development version 0.3.0 in its stage 11; the collection did not change.
At the time the work was committed locally in both repositories, and
nothing was merged or pushed. 0.3.0 was later withdrawn, and the first
release was 0.0.1 (see Assumptions); the Cloud Sandbox has installed the
collection from Ansible Galaxy since 2026-11-19
([specs/001-galaxy-publish/](../001-galaxy-publish/spec.md), Outcome).

**Input**: Collection stage 3, "the Cloud Sandbox moves to 0.3.0", planned
on 2026-11-14 and executed the same day on the operator's "do coll 3".
Written as a spec on 2026-11-27, on the operator's instruction, so that
the stage file in the ATTIC adds nothing this spec does not hold. The
operator permitted reading that one stage file, and its line in
`ATTIC/PLAN.md`, for this task.

## Why

Collection stages 1 and 2 changed this collection: [stage 1](../008-repeat-runs-say-so/spec.md) (0.2.0) made
repeat runs do nothing and say so, and [stage 2](../009-setup-role/spec.md) (0.3.0) added the `setup`
role, which sets a Spack up from one ordered list of steps. This stage
changed the collection's first user instead: the Cloud Sandbox's
`sandbox-provisioning`, under `exportit/` in the Cloud-Sandbox repository.
It still pinned the collection at 0.1.0 and still set Spack up in bash.

- `sandbox-provisioning` used `spack_env` from 0.1.0 for its Spack
  environment (the sandbox's stage 10). 0.2.0 changed a default:
  `spack_env` regenerates module files only when needed, where 0.1.0 and
  the sandbox's script regenerate them on every run. The sandbox passed
  `modules: [tcl]` and nothing else, so moving the pin would change what
  its role did without a line changing there.
- 0.3.0 could replace the shell that still set Spack up: one task in the
  sandbox's `spack` role and three in its `intel_oneapi` role. Each told a
  change by hashing Spack's whole configuration through `spack python -c`.
- Trying things for stage 2 had shown three things about Spack on the
  sandbox that the sandbox's own records did not say, or said wrongly
  ([research.md](research.md), R6 to R8).

The plan was kept in this repository, with the other collection stages,
because it was where 0.2.0 and 0.3.0 were proved on the machine they were
written for.

## Clarifications

### Session 2026-11-14

Asked one at a time, before the work was done.

- Q: Which `refresh_modules` should the sandbox's `spack_env` task give:
  `when_needed`, the default (a second run of `site.yml` touches no module
  file, and a file deleted or edited by hand is still put back; this
  differs from the script, which regenerates every time, and the
  difference is noted beside the task), or `always`, as the script does?
  → A: `when_needed`.
- Q: Where do the lists of steps live: as `vars:` of the `include_role`
  task, in the role's tasks file, where the shell sat, with each step
  carrying its own `# Replaces funcs-setup-instance.sh L<n>` comment
  (proposed); or in the role's `defaults/main.yml`, where a site can
  override a whole list? → A: In the tasks files, as `vars:` of the
  `include_role` task, each step with its own `# Replaces` comment.
- Q: The script's two settings, the install tree's padding and the Tcl
  modules, are in the login user's scope, because `spack config add`
  without `--scope` writes there. Keep them in the user scope with
  `scope: user`, as the script has them (proposed: the stage moves what
  exists and proves it the same, and the finding is recorded in
  Cloud-Sandbox's `MAP.md` for a decision of its own); or move them to the
  site scope now, where every user and every node gets them, as a
  deliberate difference from the script? → A: The site scope, not the
  proposal.
  - Q: (The operator's own question, first.) Can 0.3.0 set a step's scope?
    → A: Yes: `scope` on the step, or the role's `spack_setup_scope`. No
    change to the collection is needed (FR-002).
- Q: Add to the sandbox's container test a one-time comparison with the
  shell (proposed: before the change, dump what the shell roles leave in
  the site and user scopes into `tests/container/expected-spack-config.json`,
  and afterwards hold the new roles' result to that file, as data), or rely
  on `verify.yml`'s comparison with the sandbox's variables alone? → A:
  Yes, a recorded comparison with what the shell roles leave.
- Q: The site mirror's key is set by hand with `sandbox-ops/bin/spack-pubkey.sh`,
  whose steps the sandbox's setup has commented out. Leave it (proposed: it
  is a tool run by hand, and moving it changes what the sandbox does, not
  how), or make it a third list, `spack_setup_site_mirror`, applied when a
  variable says so, so that `spack-pubkey.sh` is superseded? → A: A third
  list, off by default.
- Q: How does Cloud-Sandbox record the work? → A: As its stage 11, with a
  short `INPROGRESS/STAGE-11.md` that points to this stage and carries the
  decisions and the outcome, and a row in its `INPROGRESS/TODO.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A site's Spack set-up shell becomes the `setup` role (Priority: P1)

A site that sets Spack up with shell tasks (settings, compiler and package
discovery, a mirror, the mirrors' keys) replaces each with one inclusion of
the `setup` role and a list of steps, and the collection as released carries
the lists out. The site changes its own playbooks; the collection does not
change. What Spack is told afterwards is what the shell told it, as data,
but for the differences the site decides on.

**Why this priority**: it is what the `setup` role was written for. Until a
real site's shell was replaced and compared, 0.3.0 was proved only against
its own tests.

**Independent Test**: in the Cloud Sandbox's container test, with the real
oneAPI, apply the roles that use the collection to a fresh Spack twice and
then in check mode, and compare what Spack holds with what the shell left.

**Acceptance Scenarios**:

1. **Given** a fresh Spack and the sandbox's two lists, **When** the
   sandbox's `site.yml` is applied, **Then** every step is carried out by
   the `setup` role as released, and no task of the sandbox's `spack` and
   `intel_oneapi` roles runs Spack through a shell.
2. **Given** the same node, **When** `site.yml` is applied a second time,
   **Then** nothing changes and no change is reported.
3. **Given** the same node, **When** the roles that use the collection are
   applied once more in check mode, **Then** no change is reported.
4. **Given** what the shell roles left, recorded before the change, **When**
   it is compared with what the `setup` role leaves, **Then** the two are
   the same, as data, but for the one difference the operator decided: the
   padding and the Tcl modules are in the site scope.

---

### User Story 2 - A site states how often module files are regenerated (Priority: P2)

A site moving from 0.1.0 to a version with `refresh_modules` names the value
it wants on its `spack_env` task, so that the change of default in 0.2.0
does not change what its play does without a line saying so.

**Why this priority**: the move of the pin changes behaviour on its own;
naming the value makes the change visible. It is small beside User Story 1.

**Independent Test**: apply the sandbox's `spack_environment` role twice;
the second run touches no module file.

**Acceptance Scenarios**:

1. **Given** `refresh_modules: when_needed`, **When** the environment is
   applied a second time with nothing to do, **Then** no module file is
   touched.
2. **Given** a module file deleted or edited by hand, **When** the
   environment is applied, **Then** the file is put back.

---

### User Story 3 - The role works the way a site's play includes it (Priority: P3)

A site includes the `setup` role from a role of its own, which is tagged,
and runs its play with `--tags`; and it applies the role as another user
than the play's, with `apply: {become: true, become_user: ...}`. Every step
of the list runs, and runs as that user.

**Why this priority**: a site's play is not the role's tests. If the role's
own includes fell outside a tag, or kept the play's user, a site's list
would be carried out in part, or into the wrong user's scope, without an
error.

**Independent Test**: run the sandbox's play with `--tags` for the
including role, and with `apply` naming the sandbox's login user; see every
step run, as that user.

**Acceptance Scenarios**:

1. **Given** the role included from a tagged role, **When** the play is run
   with that role's tag, **Then** every step of the list runs.
2. **Given** the role included with `apply: {become: true, become_user:
   "{{ sandbox_user }}"}`, **When** it is applied, **Then** every step runs
   as that user.

---

### User Story 4 - The Cloud Sandbox moves to 0.3.0 (Priority: P4)

The Cloud Sandbox's `sandbox-provisioning` moves its pin, its
`refresh_modules`, its Spack set-up shell, its fingerprint, its tests and
its records, under Cloud-Sandbox's own rules.

**Why this priority**: it is the proof of User Stories 1 to 3 on the
machine the collection was written for, but it is work in another
repository. Here it is a hand-off, and its full record is Cloud-Sandbox's
`INPROGRESS/STAGE-11.md` and `exportit/MAP.md`.

**Independent Test**: in Cloud-Sandbox, its root `just test` and
`just full-test` pass, and its container test proves User Story 1.

**Acceptance Scenarios**:

1. **Given** Cloud-Sandbox's branch `feature/stage-11-csis-spack-0.3.0`,
   **When** its root `just test` and `just full-test` run, **Then** they
   pass.
2. **Given** `spack_site_mirror` false, the default, **When** the sandbox is
   built, **Then** the site mirror's list is not applied, and
   `spack-pubkey.sh` is superseded.

---

### Edge Cases

- **A head node built before the change** still has the two settings in
  the login user's `~/.spack/config.yaml` and `modules.yaml`. They have the
  same values as the site scope's and do no harm. The list does not remove
  them: that would be a step of state `absent` in the user scope, and the
  operator did not ask for it. Cloud-Sandbox's `MAP.md` says so.
- **An external whose version or prefix changes** is now corrected. The
  shell's here-document skipped any package whose name was already in
  `packages.yaml`; a `config` step compares what is declared with what is
  there ([research.md](research.md), R9).
- **The Intel modules are not loaded** when the first list's `compiler find`
  runs: it finds no Intel compiler and leaves the registered ones alone.
  The two detections do not undo each other (R6), so the first list needs
  no environment step.
- **The second list without its environment**: the `detect` step that
  requires `intel-oneapi-compilers@<oneapi_version>` fails, rather than
  finishing with no Intel compiler registered.
- **`buildcache keys` needs the network**, as it did in the shell.
- **A build under `async`, previewed in check mode**: Ansible refuses a
  task that is both asynchronous and in check mode. A playbook that wants
  both writes `async` and `poll` so that they fall to 0 in check mode
  (R10). 0.3.0's documentation did not say so.
- **The site mirror's list** needs the site's real S3 bucket and its
  published key to be applied. It was not applied here (Out of scope).

## Requirements *(mandatory)*

Each requirement says whose it was. **Collection**: met by 0.3.0 as
released, with no change. **Cloud-Sandbox**: handed off, done in that
repository, and recorded there.

### Functional Requirements

- **FR-001** *(Collection)*: The `setup` role MUST carry out a real site's
  lists of steps of the kinds `config`, `detect`, `mirror`, `gpg_key` and
  `environment` as released: the sandbox's two lists, and its third.
- **FR-002** *(Collection)*: A step MUST be able to name its configuration
  scope with `scope`; a step that names none takes the role's
  `spack_setup_scope`, whose default is `site`.
- **FR-003** *(Collection)*: A `detect` step with `require` MUST fail when
  what it requires is not registered after detection, so that a list run
  without its environment fails loudly.
- **FR-004** *(Collection)*: `spack_env`'s `refresh_modules` MUST offer
  `when_needed`, the default, and `always`.
- **FR-005** *(Collection)*: When the role is included from a tagged role
  and the play runs with that tag, every step MUST run; when it is included
  with `apply: {become: true, become_user: ...}`, every step MUST run as
  that user. The role needs nothing of its own for either (R3, R4).
- **FR-006** *(Collection)*: A second application of the same lists MUST
  change nothing and report no change, and an application in check mode
  afterwards MUST report no change.
- **FR-007** *(Collection)*: The collection changes only if the move finds a
  defect in it. Such a defect is fixed in this repository and released as a
  patch version (then planned as 0.3.1), which the sandbox pins. None was
  found.
- **FR-008** *(Collection, a finding handed to the next stage)*: `spack_env`'s
  documentation SHOULD say how to write `async` and `poll` so that a build
  can be previewed in check mode. 0.3.0 said only to use `async`. This was
  not part of this stage's work; it became collection [stage 4](../011-preview-long-builds/spec.md) (R10).
- **FR-009** *(Cloud-Sandbox)*: The pin MUST move to 0.3.0 in
  `requirements.yml` and in `exportit/cloud-sandbox/units.toml`, which a
  test in `exportit/tools` holds together; `just init` installs it.
- **FR-010** *(Cloud-Sandbox)*: The `spack_environment` role's `spack_env`
  task MUST give `refresh_modules: when_needed`, with a comment saying
  where that differs from the script.
- **FR-011** *(Cloud-Sandbox)*: The `spack` role's shell task MUST become one
  `include_role` of `infrastructurebuilder.csis_spack.setup`, applied as
  the login user, under the same `when: spack_save.stat.exists`. Its list
  is `docs/examples/cloud-sandbox.yml`'s `spack_setup_base` with the
  sandbox's variables in place of its literals, as `vars:` of the task,
  each step with a `# Replaces funcs-setup-instance.sh L<n>` comment. The
  conditional loading of the Intel modules goes, and its comment is
  replaced by what was found (R6).
- **FR-012** *(Cloud-Sandbox)*: The padding and the Tcl modules MUST be in
  the site scope: the list's first step names no scope and takes the
  role's `site`. The step's comment (`# Replaces funcs-setup-instance.sh
  L672-L673`) says that the script's `config add` has no `--scope`, and
  `MAP.md` records it as a deliberate difference. Settings already in a
  user scope are not removed.
- **FR-013** *(Cloud-Sandbox)*: The `intel_oneapi` role's three Spack tasks
  MUST become a second inclusion of the role, with the list
  `spack_setup_intel` built from `sandbox_modules_init`,
  `sandbox_load_intel_modules`, `intel_oneapi_spack_externals` and
  `intel_oneapi_spack_providers`, so that those variables stay the one
  place the values are. The `environment` step runs the two shell
  variables; the `detect` step requires
  `intel-oneapi-compilers@{{ oneapi_version }}`.
  `intel_oneapi_spack_packages_file` goes.
- **FR-014** *(Cloud-Sandbox)*: `spack_config_json` and `spack_fingerprint`
  MUST leave `group_vars/all.yml`; `tests/container/verify.yml` reads
  Spack's configuration with `spack config get --json` instead.
- **FR-015** *(Cloud-Sandbox)*: Traceability and parity MUST be kept.
  `tests/test_traceability.py` reads a `# Replaces` or `# New:` comment on
  each step of a list, as on each task. `tests/test_parity.py` holds the
  lists to the script's Spack commands (L661-L700, L919-L959), command for
  step and in the script's order, with each setting in the scope decided;
  the externals and providers are held to the script as before.
- **FR-016** *(Cloud-Sandbox)*: The container test MUST start from a fresh
  Spack clone, apply the lists twice with the real oneAPI, and then run
  check mode. `verify.yml` compares data, not text: each scope's `config`,
  `modules`, `mirrors` and the declared part of `packages` must equal what
  the variables say, and `spack compiler list` must hold the system's GCC
  and the Intel compilers at `oneapi_version`. It also compares the result
  with `tests/container/expected-spack-config.json`, dumped from the shell
  roles before the change and committed unedited, expecting exactly one
  difference, stated in the test: the user scope's `config` and `modules`
  are empty and the site scope's hold what they held.
- **FR-017** *(Cloud-Sandbox)*: A third list, `spack_setup_site_mirror`, in
  the `spack` role, MUST be applied by a second `include_role` only when
  `spack_site_mirror` is true, false by default. Its steps, in
  `spack-pubkey.sh`'s order: a `gpg_key` step with `spack_key_url` and the
  key's fingerprint (`spack_key_fingerprint`); a `mirror` step named
  `s3-mirror` with `spack_mirror`; a `gpg_key` step with `from_mirrors`.
  Each carries `# Replaces scripts/spack-pubkey.sh L<n>`. `spack-pubkey.sh`
  is then superseded.
- **FR-018** *(Cloud-Sandbox)*: Cloud-Sandbox MUST record the work: its
  `exportit/MAP.md`, `INPROGRESS/STAGE-11.md` and `INPROGRESS/TODO.md`, and
  `sandbox-provisioning/README.md`; its copies stay byte-identical, and
  nothing is pushed to IOOS.

### Key Entities

- **The sandbox's lists**: `spack_setup_base` (settings, discovery, the
  public mirror, its keys), `spack_setup_intel` (the Intel modules'
  environment, the Intel compilers, MKL and MPI declared, the providers),
  and `spack_setup_site_mirror` (the site mirror's key, the mirror, its
  keys). Each is a `setup` list in a Cloud-Sandbox tasks file.
- **The collection's copy**: `docs/examples/cloud-sandbox.yml`, the first
  two lists with the sandbox's literals, written in stage 2 to reproduce
  the shell. It is the example the collection's tests run, and the source
  of the names `tests/unit/test_no_site_knowledge.py` keeps out of the
  plugins and the role.
- **The side-by-side record**: `tests/container/expected-spack-config.json`
  in Cloud-Sandbox, what the shell roles left, as data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** *(Collection)*: The collection needed no change: every list was
  carried out by 0.3.0 as released.
- **SC-002**: In the sandbox's container test with the real oneAPI, the
  first application of `site.yml` made 55 changes, the second 0, and the
  three roles that use the collection, once more in check mode, 0.
- **SC-003**: What Spack was told is the same, as data, as what the shell
  left, but for the one difference decided.
- **SC-004** *(Cloud-Sandbox)*: No task of the `spack` and `intel_oneapi`
  roles runs Spack through a shell, and `spack_fingerprint` and
  `spack_config_json` are gone.
- **SC-005** *(Cloud-Sandbox)*: Every line of `install_spack`,
  `install_intel_oneapi_dnf` and `add_spack_site_external` that does
  something is still replaced by a task or a step that names it, or listed
  in `tests/not_carried.yml`.
- **SC-006** *(Cloud-Sandbox)*: With `spack_site_mirror` false, the site
  mirror's list is not applied, and `spack-pubkey.sh` is out of use,
  superseded.
- **SC-007** *(Cloud-Sandbox)*: Cloud-Sandbox's root `just test` and
  `just full-test` pass.

## Assumptions

- **The versions named here are history.** 0.1.0, 0.2.0, 0.3.0 and 0.3.1
  were development versions, tagged 2026-11-13 to 2026-11-14 and withdrawn
  on 2026-11-18. The first release, and the first version on Ansible
  Galaxy, is 0.0.1, which holds everything 0.3.0 and 0.3.1 held
  ([specs/001-galaxy-publish/](../001-galaxy-publish/spec.md),
  Assumptions). The pin to the tag 0.3.0 was replaced by `0.0.1` from git
  on 2026-11-18, and then by the range `">=0.0.1,<0.1.0"` from Galaxy on
  2026-11-19 (spec 001, Outcome).
- **A name that changed since.** At 0.3.0 the role's executable was named
  `spack_setup_spack`. It is `spack_setup_executable` since 0.0.1, and the
  old name still works
  ([specs/002-setup-executable-rename/](../002-setup-executable-rename/spec.md)).
- **The collection's example still reproduces the script.**
  `docs/examples/cloud-sandbox.yml` keeps the two settings in the user
  scope, as the script has them, and `tests/unit/test_examples.py` holds it
  to the script's commands. The sandbox's choice of the site scope is the
  sandbox's, in its own lists; the example was not meant to follow it.
- **"0.3.0 needed no change" holds for what was run.** Later, on
  2026-11-24, a `gpg_key` step with `from_mirrors` stopped at Spack 1.2's
  "Trust key [y/N]" prompt on a real head node, against a mirror that
  published a key in Spack's own layout; Spack asks nothing of a mirror
  that publishes none. That was a defect in the released 0.0.1 and 0.0.2,
  fixed in 0.0.3
  ([specs/003-mirror-keys-yes-to-all/](../003-mirror-keys-yes-to-all/spec.md)).
  This stage's container run did not meet it, and its site mirror's list,
  the case that would have, was not applied (Out of scope).
- The Cloud Sandbox's part is done in the Cloud-Sandbox repository, under
  its rules. Its record is its `INPROGRESS/STAGE-11.md` and its
  `exportit/MAP.md`. This spec repeats only what the collection's stage file
  said.
- The Cloud Sandbox now plans its own work in its own `specs/`
  ([specs/README.md](../README.md), "Standing beside them").

## Out of Scope

- Using `spack_buildcache_push` for the `sandbox-ops` mirror scripts.
- The UFS spack-stack.
- Removing the two settings from the login user's scope on a head node that
  already has them there.
- Applying the site mirror's list against the real bucket. The parity test
  holds the list to the script's commands, and the collection's unit tests
  cover each kind; the list itself was to be first applied in the live
  proof on AWS, as Cloud-Sandbox's `MAP.md` says.
- The live proof on AWS.

## Outcome

Recorded 2026-11-14, in full in Cloud-Sandbox's `INPROGRESS/STAGE-11.md`
and `exportit/MAP.md`. For this collection:

- **0.3.0 needed no change.** The sandbox's two lists, and its third, are
  carried out by the `setup` role as released. Under `--tags`, with the
  role included from a tagged role, every step ran: the tags of the
  including task reach the role's own includes (tried first). Applied with
  `apply: {become: true, become_user: ...}`, every step ran as that user.
- **With the real oneAPI, in the sandbox's container test:** installed
  from the tag 0.3.0; first application of `site.yml`, 55 changes; second,
  0; the three roles that use the collection once more in check mode, 0
  changes. What Spack was told is the same, as data, as what the shell
  left, but for the one difference decided (the two settings in the site
  scope).
- **Found about using `spack_env`:** Ansible refuses a task that is both
  asynchronous and in check mode, and a build wants `async`. The module's
  notes said only to use `async`. That became the next stage, collection
  stage 4, a documentation change released in 0.3.1; it is in 0.0.1
  (`plugins/modules/spack_env.py`, notes and example), held by
  `tests/unit/test_async_and_check_mode.py`, and in the constitution's
  principle II.
- **What differed from the plan**, as Cloud-Sandbox's `STAGE-11.md`
  records it: `spack-pubkey.sh` went to `sandbox-provisioning/legacy/`, not
  to the attic; `spack_key` stays; the scope decision is said on the step
  and in `MAP.md`, not in `tests/not_carried.yml`; the site mirror goes to
  the site scope too; the side-by-side proof compares externals by package
  name.
- **Not proved:** the site mirror's list against the real bucket.
