---

description: "Task list for renaming the setup role's executable variable"
---

# Tasks: Name the setup role's Spack executable `spack_setup_executable`

**Input**: Design documents from `/specs/002-setup-executable-rename/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md)

**Tests**: included, written first; the constitution asks for them (principle IV).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: the user story the task belongs to (US1, US2)

## Phase 1: Setup

- [X] T001 Record the two decisions in `specs/002-setup-executable-rename/spec.md` under Clarifications

---

## Phase 2: Tests first (they must fail before Phase 3)

- [X] T002 [US1] In `tests/unit/test_setup_role.py`, add a second way to the stand-in `spack`, outside `PATH`, that leaves a mark when run; add a test that `spack_setup_executable` set to it is what runs; hold the role's defaults to the new name
- [X] T003 [US2] In `tests/unit/test_setup_role.py`, add a test that `spack_setup_spack` alone still names what runs, and a test that with both set `spack_setup_executable` is what runs
- [X] T004 Before the role changes, run the new tests and see them fail for the right reason (three failed: the defaults, the new name ignored, and with both names the old one run; the two that describe today's behaviour passed)

---

## Phase 3: User Story 1 - A name that says what the variable is (Priority: P1)

**Goal**: the role takes the executable from `spack_setup_executable`.

**Independent Test**: T002's tests pass.

- [X] T005 [US1] In `roles/setup/defaults/main.yml`, replace `spack_setup_spack` with `spack_setup_executable`, whose default reads the old name when it is set
- [X] T006 [P] [US1] In `roles/setup/tasks/kinds/command.yml`, `config.yml`, `detect.yml`, `gpg_key.yml` and `mirror.yml`, pass `spack_setup_executable`
- [X] T007 [P] [US1] In `tests/integration/test_real_setup.py`, use the new name

---

## Phase 4: User Story 2 - A playbook written for 0.3.1 keeps working (Priority: P2)

**Goal**: the old name still names what runs.

**Independent Test**: T003's tests pass.

- [X] T008 [US2] Confirm T005's default carries the old name: T003's tests pass with no further change to the role

---

## Phase 5: Documentation and acceptance

- [X] T009 [P] In `roles/setup/README.md`, use the new name in the Variables table and the example, and say that `spack_setup_spack` still works
- [X] T010 [P] In `docs/examples/cloud-sandbox.yml` and `docs/examples/system-compiler.yml`, use the new name
- [X] T011 In `CHANGELOG.md`, record the rename under Unreleased
- [X] T012 Run `just test`
- [X] T013 Run `just full-test`
- [X] T014 Set the Status line of `specs/002-setup-executable-rename/spec.md`

## Dependencies & Execution Order

- T002 and T003 before T004; T004 before T005.
- T005 before T006, T007 and T008.
- T009, T010 and T011 are independent of each other.
- T012 and T013 last, in that order; T014 after both pass.
