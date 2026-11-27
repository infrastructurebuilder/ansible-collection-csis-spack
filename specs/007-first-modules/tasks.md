---

description: "Task list, as a record, for the first modules: spack_env and spack_buildcache_push"
---

# Tasks: The first modules: an environment, and a build cache

**Input**: Design documents from `/specs/007-first-modules/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md)

**These tasks are a record of work done on 2026-11-13, before this
repository used Spec Kit.** They were written on 2026-11-27 from the items,
the decisions and the outcome of the plan of the time (`ATTIC/PLAN.md`),
and every one is ticked because it was done. They are grouped as Spec Kit
groups tasks, by user story; the record does not say in which order the
work was done within a day, nor whether each test was seen to fail first.
Files are named as they are today. The record gives the unit tests' count
(45), not their names; the tests below are described by today's names for
the cases 0.1.0 had.

**Tests**: included; the plan of the time asked for them (its item 5).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: could run in parallel (different files, no dependencies)
- **[Story]**: the user story the task belongs to (US1, US2, US3)

---

## Phase 1: Setup

- [X] T001 Ask the operator the five decisions one at a time (one module or three for the environment; pushing as a module of its own; what surrounds Spack; where the integration test runs; which Spack versions), and record each answer; now in `specs/007-first-modules/spec.md` under Clarifications
- [X] T002 Read the `--help` of the Spack v1.2.0 commands the modules would run (`concretize`, `install`, `find`, `module tcl refresh`, `buildcache push`), and try them by hand on the local machine: concretize, `install --fake`, `find --json`, `module tcl refresh`, `buildcache push` twice, `buildcache check -o`; what was found is now in `specs/007-first-modules/research.md` (R1 to R6)

---

## Phase 2: Foundational

**Purpose**: the runner both modules share, and the stand-in every unit test
runs against.

- [X] T003 Create `plugins/module_utils/spack.py`: the class `Spack`, which runs Spack with `-e <env>` as a list of arguments through `run_command`, never through a shell, collects its output, writes it to a log file when asked, and raises `SpackError` with the command and the end of the output on a failure; `version()` and `require_version()` (1.0 or later); `installed()` from `find --json`; `mirrors()` from `mirror list`; and the functions `file_digest`, `tree_digest`, `parse_version`, `lock_specs`, `mirror_url`, `parse_mirror_list`
- [X] T004 [P] Create `tests/unit/fake_spack.py`: a stand-in `spack`, put first on `PATH`, that answers `--version`, `concretize`, `install`, `find --json`, `module ... refresh`, `mirror list`, `buildcache push` and `buildcache check` from a JSON state file, as the real v1.2.0 answered them in T002, and records how it was called
- [X] T005 [P] Create the unit-test harness that runs a module of the collection through `ansible` itself against the stand-in, in `tests/unit/conftest.py`
- [X] T006 [P] Write the shared runner's tests in `tests/unit/test_module_utils.py`: versions read from `spack --version`, `mirror list` read as v1.2.0 prints it, a mirror as a URL, a path or a name, a missing lock, a lock's specs and roots, digests

---

## Phase 3: User Story 1 - A site builds its environment with a module (Priority: P1)

**Goal**: `spack_env` concretizes, installs and regenerates module files,
reporting each change on its own; a repeat run reports none.

**Independent Test**: the stand-in, then the real Spack: a first run reports a
change, a second none.

- [X] T007 [P] [US1] Write `tests/unit/test_spack_env.py` for a real run: a first run concretizes and installs; a second changes nothing; externals never reported as installed; a new lock with nothing to install is a change; `state: concretized` installs nothing; `fresh: false` leaves out `--fresh`; `install_args` passed as they are and the log kept; a log file named; `spack` found on `PATH`; module files regenerated and their change reported; a failed build fails with the end of its output; a directory without `spack.yaml` refused; Spack before 1.0 refused; an unknown option refused
- [X] T008 [US1] Create `plugins/modules/spack_env.py` with the options `path`, `spack`, `state`, `fresh`, `install_args`, `modules`, `delete_tree` and `log_file`; concretize with `--force -q [--fresh]`; install with `install_args`, its output to `log_file`; regenerate each system's module files with `refresh -y [--delete-tree]`; report `concretized`, `installed`, `modules_refreshed`, `roots`, `spack_version` and `log_file`, and `changed` as any of the first three

---

## Phase 4: User Story 2 - A site previews what a build would do (Priority: P2)

**Goal**: check mode reports what would change and touches nothing.

**Independent Test**: check mode before the first run: a change reported, and
no `spack.lock` in the environment.

- [X] T009 [P] [US2] Add to `tests/unit/test_spack_env.py`: check mode says what would change and touches nothing; after a run, check mode reports no change; check mode sees a new spec to install
- [X] T010 [US2] In `plugins/modules/spack_env.py`, carry out check mode: copy the environment into a temporary directory, concretize the copy, report whether `spack.lock` would change and which of its specs are not installed, and remove the copy

---

## Phase 5: User Story 3 - A site pushes what it built to a build cache (Priority: P3)

**Goal**: `spack_buildcache_push` pushes what the mirror lacks, says what it
pushed, and in check mode what it would.

**Independent Test**: a push to a mirror in a local directory: reported once.

- [X] T011 [P] [US3] Write `tests/unit/test_spack_buildcache_push.py`: a first push pushes what was built and says so; a second changes nothing; the options reach Spack; `key` and `unsigned` together refused; a mirror named in Spack resolved to its URL; an unknown mirror name refused; check mode lists what the mirror lacks and pushes nothing; check mode never counts externals; check mode after a push reports no change; check mode follows `only`; a failed push fails
- [X] T012 [US3] Create `plugins/modules/spack_buildcache_push.py` with the options `env`, `mirror`, `key` or `unsigned`, `update_index`, `only`, `force` (a boolean) and `spack`; push in the environment with no specs named; read what was pushed from the `Pushed <spec>/<short hash>` lines (research R5); in check mode ask `buildcache check -m <url> -o <file>`, exit 1 allowed, externals left out and `only` applied (research R6); return `pushed`, `mirror_url` and `spack_version`; never handle a key

---

## Phase 6: Against the real Spack

- [X] T013 [US1] [US2] [US3] Write `tests/integration/test_real_spack.py`: the real Spack v1.2.0 cloned once into `.tmp/`, its user configuration and caches in `.tmp/` too; an environment of one small package installed with `install_args: [--fake]`; `spack_env` in check mode first, changing nothing, then twice, the second run changing nothing; `spack_buildcache_push` in check mode, then twice to a mirror in a local directory with `unsigned: true`, the push reported once
- [X] T014 [US1] Fix what T013 found: Spack stamps every module file with the time it wrote it, so every refresh changed every file. Add `module_tree_digest` and the pattern `CREATED_ON` to `plugins/module_utils/spack.py`, compare module trees with it in `plugins/modules/spack_env.py`, and test it in `tests/unit/test_module_utils.py` (research R7)
- [X] T015 [US1] Record that the same flaw is in the Cloud Sandbox's `spack_environment` role, in that repository's `MAP.md` (the Cloud Sandbox's work, not this repository's)

---

## Phase 7: Documentation and acceptance

- [X] T016 [P] Write each module's `DOCUMENTATION`, `EXAMPLES` and `RETURN` in `plugins/modules/spack_env.py` and `plugins/modules/spack_buildcache_push.py`, with `version_added: 0.1.0`
- [X] T017 [P] In `README.md`, describe both modules under "What it holds"
- [X] T018 [P] Create `CHANGELOG.md` with an entry for 0.1.0, and set the version to 0.1.0 in `galaxy.yml`
- [X] T019 Run `just test`: ruff, pyright with 0 errors, 45 tests against the stand-in run through `ansible` itself, and a build that installs
- [X] T020 Run `just full-test`: the same; then both modules against the real Spack v1.2.0, where check mode reports and touches nothing, the first run concretizes, installs and writes module files, the second changes nothing, and a push to a mirror in a directory is reported once; then `ansible-test sanity`, which passes for both modules
- [X] T021 Run `just build` and see `dist/infrastructurebuilder-csis_spack-0.1.0.tar.gz` hold both modules and install
- [X] T022 Release 0.1.0: tag it and push it, 2026-11-13. Nothing was uploaded to Ansible Galaxy

## Dependencies & Execution Order

- T001 and T002 before everything: the decisions and the Spack behaviour
  the modules rely on.
- Phase 2 before the stories: T003 is the runner both modules use; T004 the
  stand-in every unit test runs against.
- US1 before US2, which is check mode in the same module. US3 needs only
  Phase 2.
- T013 after the three stories; T014 after T013, which found it.
- Phase 7 last; T019, T020, T021 in that order; T022 after them.

## What became of it

- The tag 0.1.0 and its `release/*` branch were deleted on 2026-11-18, and
  the history was reset to a single commit the same day; the branch
  `feature/spack-env-module` is not in the repository either. Everything 0.1.0 held is in
  0.0.1, where every `version_added` became 0.0.1 and `CHANGELOG.md` was
  rewritten as one 0.0.1 entry
  ([specs/001-galaxy-publish/tasks.md](../001-galaxy-publish/tasks.md),
  T021).
- The changes since are noted in [spec.md](spec.md) and [plan.md](plan.md)
  where they fall: 0.2.0, 0.3.0 and 0.3.1 (2026-11-14), and spec 003
  (0.0.3).
