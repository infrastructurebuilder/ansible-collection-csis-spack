---

description: "Task list, as a record, for saying how to preview a long build"
---

# Tasks: Say how to preview a long build

**Input**: Design documents from `/specs/011-preview-long-builds/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md)

**A record, not a plan.** This work was done on 2026-11-14, before this
repository used Spec Kit. These tasks are its items, decisions and outcome
as `ATTIC/COLL-INPROGRESS/COLL-STAGE-4.md` recorded them, written in this
format on 2026-11-27. Every one is ticked because it was done; none is to be
carried out again. Where the source does not record the order in which tests
and code were written, none is claimed.

**Tests**: included (principle IV); the test file is part of the change.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: the user story the task belongs to (US1, US2, US3)

## Phase 1: Setup

- [X] T001 Take the finding of collection stage 3 (Ansible refuses `async` with check mode; the form that previews) as the reason for this work; it is now recorded in `specs/011-preview-long-builds/research.md` (R1)
- [X] T002 Ask the operator the two decisions (the release; the Cloud Sandbox's pin), the pin a second time, and record the answers; they are now in `specs/011-preview-long-builds/spec.md` under Clarifications

---

## Phase 2: User Story 1 - A playbook that builds can be previewed (Priority: P1)

**Goal**: a site that copies the documented task can run it with `--check`.

**Independent Test**: T005 to T007 pass.

- [X] T003 [US1] In `plugins/modules/spack_env.py`, add a note after "A build can take hours" that quotes Ansible's message, says a preview builds nothing and does not need `async`, and gives `async: "{{ 0 if ansible_check_mode else 86400 }}"` and `poll: "{{ 0 if ansible_check_mode else 60 }}"`
- [X] T004 [US1] In `plugins/modules/spack_env.py`, write the build example's `async` and `poll` in the form, with a comment saying why
- [X] T005 [P] [US1] In `README.md`, write the "Building an environment" example's `async` and `poll` in the form, with the same comment
- [X] T006 [US1] In `tests/unit/test_async_and_check_mode.py`, run a play holding the form with `--check` against the stand-in `spack` and see it succeed with no `install` call and no `spack.lock` (`test_the_form_previews_without_building`), and without `--check` and see it install (`test_the_form_builds_asynchronously_when_not_previewing`)
- [X] T007 [US1] In `tests/unit/test_async_and_check_mode.py`, run the same play with `async: 86400` and `poll: 60` and `--check`, and see it fail with "check mode and async cannot be used on same task" (`test_a_plain_number_cannot_be_previewed`)

---

## Phase 3: User Story 2 - The documentation stays previewable (Priority: P2)

**Goal**: an example with a plain number fails the unit tests.

**Independent Test**: T008 and T009 pass, and fail when a plain number is put in an example.

- [X] T008 [US2] In `tests/unit/test_async_and_check_mode.py`, read `spack_env`'s `DOCUMENTATION` and hold its notes to Ansible's message and both forms (`test_the_notes_say_why_and_give_the_form`)
- [X] T009 [US2] In `tests/unit/test_async_and_check_mode.py`, fail on any `async:` or `poll:` given as a plain number in `spack_env`'s `EXAMPLES`, `README.md` or `roles/setup/README.md`, and require both forms in the `EXAMPLES` (`test_no_example_gives_async_as_a_plain_number`)

---

## Phase 4: User Story 3 - The README's examples belong to no site (Priority: P3)

**Goal**: the README's examples are any site's.

**Independent Test**: no name of `docs/examples/cloud-sandbox.yml` is in the README's examples.

- [X] T010 [US3] In `README.md`, replace the one site's paths and names in the two examples with neutral ones (`/opt/spack-environments/base`, `site-cache`, `mycompiler_environment`)

---

## Phase 5: Changelog, acceptance and the release

- [X] T011 In `CHANGELOG.md`, record the change under "Unreleased (to be 0.3.1)", documentation only, as the operator decided to keep it on `develop`; the version stays 0.3.0 in `galaxy.yml`
- [X] T012 Run `just test`
- [X] T013 Run `just full-test`
- [X] T014 Run `ansible-doc infrastructurebuilder.csis_spack.spack_env` and see the note
- [X] T015 Merge `feature/coll-stage-4` into `develop`, on the operator's word
- [X] T016 On the operator's word after the Cloud Sandbox's stage 12 found the defect, fix `spack_config` so that a removal that would empty a mapping removes that mapping, from the highest level it empties, in `plugins/module_utils/spack.py`, with tests in `tests/unit/test_spack_config.py` and `tests/integration/test_real_setup.py` (reconstructed from `CHANGELOG.md` 0.0.1 and the code; the source names the fix only)
- [X] T017 Release 0.3.1 with this change and the fix, on the operator's word: set the version in `galaxy.yml`, tag `0.3.1` ("removing a setting removes the mapping it empties; async with check mode documented"), and have the Cloud Sandbox's pin moved to it in `sandbox-provisioning/requirements.yml` and `exportit/cloud-sandbox/units.toml` (its work, in Cloud-Sandbox, in its stage 12)
- [X] T018 Superseded, recorded 2026-11-27: 0.3.1 was withdrawn on 2026-11-18 and its content released in 0.0.1, under "Building an environment" in `CHANGELOG.md`; the Cloud Sandbox installs from Ansible Galaxy by a range ([specs/001-galaxy-publish/spec.md](../001-galaxy-publish/spec.md))
- [X] T019 Set the Status line of `specs/011-preview-long-builds/spec.md`

## Dependencies & Execution Order

- T002 before T011 and T017: the decisions shaped both.
- T003 and T004 (one file) before T008 and T009, which read it; T005 before T009.
- T006 to T009 in one file, one after another.
- T010 independent of T003 to T009.
- T012 and T013 after T003 to T011, in that order; T014 after T013.
- T016 after T015; T017 after T016; T018 and T019 last.
