---

description: "Task list, as a record, for the Cloud Sandbox's move to the setup role"
---

# Tasks: The Cloud Sandbox replaces its Spack set-up shell with the `setup` role

**Input**: Design documents from `/specs/010-sandbox-adopts-setup/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md)

**These tasks are a record of work done on 2026-11-14, before this
repository adopted Spec Kit.** They were written down on 2026-11-27 from
the collection's stage file, and every one is ticked. A task is ticked as
the stage file records it done. Where the work went otherwise than
planned, the task says what was done. Where only Cloud-Sandbox's
`INPROGRESS/STAGE-11.md` holds the result, the task says so.

**Tests**: no test of this repository changed in 2026-11, but T029 (2026-11-27),
which added tests of FR-005. The tests that proved the
work are Cloud-Sandbox's.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: could run in parallel (different files, no dependencies)
- **[Story]**: the user story the task belongs to (US1 to US4)
- Each task names the repository it was done in: **Collection** (this
  repository) or **Cloud-Sandbox**

---

## Phase 1: Setup

- [X] T001 **Collection**: plan the stage as `ATTIC/COLL-INPROGRESS/COLL-STAGE-3.md` on `feature/coll-stage-3`, with what existed in Cloud-Sandbox's `exportit/sandbox-provisioning/`, what stage 2 found, and nine items
- [X] T002 **Collection**: answer the operator's question whether 0.3.0 can set a step's scope (yes: `scope` on the step, or `spack_setup_scope`; no change), research.md R2
- [X] T003 **Collection**: ask the six decisions one at a time, before execution, and record the answers under "Decisions taken" and what they change in the items (spec, Clarifications)
- [X] T004 **Cloud-Sandbox**: on the operator's "do coll 3", start `feature/stage-11-csis-spack-0.3.0`, and record the stage as stage 11: a short `INPROGRESS/STAGE-11.md` that points to the collection's stage and carries the decisions, and a row in `INPROGRESS/TODO.md`

---

## Phase 2: User Story 2 - A site states how often module files are regenerated (Priority: P2)

(The stage's items 1 and 2, in its order: the pin moves before anything
else can use 0.3.0.)

- [X] T005 [US2] **Cloud-Sandbox**: move the pin to 0.3.0 in `exportit/sandbox-provisioning/requirements.yml` and `exportit/cloud-sandbox/units.toml`; `just init` installs it (FR-009)
- [X] T006 [US2] **Cloud-Sandbox**: give the `spack_env` task in `roles/spack_environment/tasks/main.yml` `refresh_modules: when_needed`, with a comment saying where it differs from the script (FR-010)

---

## Phase 3: User Story 1 - A site's Spack set-up shell becomes the `setup` role (Priority: P1)

- [X] T007 [US1] **Cloud-Sandbox**: before any role changes, dump what the shell roles leave in the site and user scopes into `tests/container/expected-spack-config.json`, committed unedited (decision 4)
- [X] T008 [US1] **Cloud-Sandbox**: replace the shell task of `roles/spack/tasks/main.yml` with one `include_role` of `infrastructurebuilder.csis_spack.setup`, applied as `sandbox_user`, under `when: spack_save.stat.exists`, with the list `spack_setup_base` as `vars:` and a `# Replaces funcs-setup-instance.sh L<n>` comment on each step (FR-011)
- [X] T009 [US1] **Cloud-Sandbox**: remove the conditional loading of the Intel modules from the `spack` role, and replace its comment with what was found (research.md R6)
- [X] T010 [US1] **Cloud-Sandbox**: leave the first step with no `scope`, so the padding and the Tcl modules go to the site scope; say on the step (`# Replaces funcs-setup-instance.sh L672-L673`) that the script's `config add` has no `--scope`, and in `exportit/MAP.md`. Done on the step and in `MAP.md`, not in `tests/not_carried.yml` as planned (FR-012)
- [X] T011 [US1] **Cloud-Sandbox**: replace the three Spack tasks of `roles/intel_oneapi/tasks/main.yml` with an `include_role` and the list `spack_setup_intel`, built from `sandbox_modules_init`, `sandbox_load_intel_modules`, `intel_oneapi_spack_externals` and `intel_oneapi_spack_providers`; the `detect` step requires `intel-oneapi-compilers@{{ oneapi_version }}` (FR-013)
- [X] T012 [US1] **Cloud-Sandbox**: remove `intel_oneapi_spack_packages_file`, which nothing writes by hand any more (FR-013)
- [X] T013 [US1] **Cloud-Sandbox**: remove `spack_config_json` and `spack_fingerprint` from `group_vars/all.yml`, and have `tests/container/verify.yml` read Spack's configuration with `spack config get --json` (FR-014)
- [X] T014 [P] [US1] **Cloud-Sandbox**: teach `tests/test_traceability.py` to read a `# Replaces` or `# New:` comment on each step of a list; every line of the four functions that does something is still replaced or in `tests/not_carried.yml` (FR-015, SC-005)
- [X] T015 [P] [US1] **Cloud-Sandbox**: have `tests/test_parity.py` read the script's Spack commands (L661-L700, L919-L959) and hold the lists to them, command for step, in the script's order, with the first step's settings held to the script's two paths and its scope to `site`; the externals and providers held as before (FR-015)
- [X] T016 [US1] **Cloud-Sandbox**: have the container test compare data: each scope's `config`, `modules`, `mirrors` and declared `packages`, read with `spack config --scope <s> get --json`, against the variables; `spack compiler list` against the system's GCC and the Intel compilers at `oneapi_version`; and the whole against `expected-spack-config.json`, expecting exactly the one stated difference. Externals were compared by package name (FR-016)
- [X] T017 [US1] **Cloud-Sandbox**: add the third list, `spack_setup_site_mirror`, to the `spack` role, applied by a second `include_role` only when `spack_site_mirror` is true (false by default): a `gpg_key` step with `spack_key_url` and `spack_key_fingerprint`, a `mirror` step `s3-mirror` with `spack_mirror`, a `gpg_key` step with `from_mirrors`, each with `# Replaces scripts/spack-pubkey.sh L<n>`. The site mirror went to the site scope; `spack_key` stays (FR-017)
- [X] T018 [US1] **Cloud-Sandbox**: supersede `spack-pubkey.sh`. Done by moving it to `sandbox-provisioning/legacy/`, not to the attic as planned (FR-017, SC-006)

---

## Phase 4: User Story 3 - The role works the way a site's play includes it (Priority: P3)

- [X] T019 [US3] **Cloud-Sandbox**, about the collection: before relying on it, try the role included from a tagged role under `--tags`; every step ran (research.md R3)
- [X] T020 [US3] **Cloud-Sandbox**, about the collection: apply the role with `apply: {become: true, become_user: ...}`; every step ran as that user (research.md R4)

---

## Phase 5: Validation

- [X] T021 [US1] **Cloud-Sandbox**: with the collection installed from the tag 0.3.0 and the real oneAPI, run the container test from a fresh Spack clone: `site.yml` first 55 changes, second 0; the three roles that use the collection once more in check mode, 0 changes; the comparison with `expected-spack-config.json` holding but for the one difference (SC-002, SC-003; research.md R5)
- [X] T022 [US4] **Cloud-Sandbox**: run its root `just test` and `just full-test` (SC-007). Ticked as run: the collection's stage file asked for them and records the container run's numbers, but not their result, which only Cloud-Sandbox's `STAGE-11.md` can show; this repository holds no evidence that they passed

---

## Phase 6: User Story 4 - Records (Priority: P4)

- [X] T023 [P] [US4] **Cloud-Sandbox**: update `exportit/MAP.md`: the `sandbox-provisioning` section (the lists, the variables gone, what the container now proves); the stage 3 note that the two `compiler find` steps undo each other, corrected; the two settings once in the user scope, under "Found", and the settings left in that scope on older head nodes; the site mirror's list first applied in the live proof; the collection's section and state at 0.3.0 (FR-018)
- [X] T024 [P] [US4] **Cloud-Sandbox**: update `sandbox-provisioning/README.md`: `just init`'s line, and the roles' table where it describes the two roles (FR-018)
- [X] T025 [US4] **Cloud-Sandbox**: record the outcome, and what differed from the plan, in `INPROGRESS/STAGE-11.md`, and the row in `INPROGRESS/TODO.md` (FR-018)
- [X] T026 **Collection**: record the outcome in the stage file: 0.3.0 needed no change; `--tags` and `apply: become`; the container run; the `async` finding; what differed, by pointing to `STAGE-11.md`; what was not proved
- [X] T027 **Collection**: leave the `async` and check-mode finding for the next version, as a documentation change (FR-008, research.md R10). It became collection stage 4, released in 0.3.1, and is in 0.0.1
- [X] T028 **Both**: commit locally in both repositories; merge nothing and push nothing

---

## Dependencies & Execution Order

- T001 to T003 before T004; T004 before everything in Cloud-Sandbox.
- T005 before T008, T011 and T017, which need 0.3.0.
- T007 before T008 to T013: the shell's result is recorded before it goes.
- T008 to T018 before T021. T019 was tried before the lists relied on it
  ("tried first", in the stage file); the stage file does not say when T020
  was tried.
- T021 and T022 before T023 to T026.
- T028 last.

## Phase 7: Convergence

- [X] T029 Hold FR-005 with tests in `tests/unit/test_setup_role.py`, through a play that includes the role with `ansible.builtin.include_role` from a task (not with `import_role`): (1) **tags**: the including task tagged `spack`, the play run with `--tags spack`, and a list of a `config` step and a `mirror` step against the stand-in `spack`: both steps are carried out (the stand-in records a `config add` and a `mirror add` call, and the scope and mirror hold what the steps say) and `spack_setup_results` has two entries; (2) **apply**: the role included with `apply: {environment: {CSIS_APPLIED: "yes"}}` (a keyword with no side effect), and the stand-in recording the environment it was run in: every Spack call of every step saw `CSIS_APPLIED=yes`. Switching user with `apply: {become: true, become_user: ...}` is Ansible's own `become`, which these tests do not re-prove (it needs a second user and a password-less become on the test machine): record that in `specs/010-sandbox-adopts-setup/research.md` R4, with what the tests do prove (that `apply:` reaches every step), per FR-005 (partial)
