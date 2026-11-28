---

description: "Task list, as done, for repeat runs that do nothing and say so"
---

# Tasks: Repeat runs that do nothing, and say so

**Input**: Design documents from `/specs/008-repeat-runs-say-so/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md)

**This is a record of work done before Spec Kit**, on 2026-11-14 on
`feature/coll-stage-1`: planned that day, and carried out the same day on
the operator's word ("do coll 1"). It was written on 2026-11-27 from
`ATTIC/COLL-INPROGRESS/COLL-STAGE-1.md`. The tasks are the items of that
plan, in the order it gave them, each ticked because it was done. The file
paths are those the work lives in today. The record does not keep the order
within an item, nor whether each test was seen to fail first.

**Tests**: included; the plan of the time asked for them (its item 4).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: could run in parallel (different files, no dependency)
- **[Story]**: the user story the task belongs to (US1 to US4)

---

## Phase 1: Decisions and research

- [X] T001 Ask the operator the four decisions one at a time (the default of `refresh_modules`; what counts as "needed"; `force`; how to know what was pushed) and record the answers, now in `specs/008-repeat-runs-say-so/spec.md` under Clarifications
- [X] T002 Try against the real Spack v1.2.0: `spack -e <env> config get --json modules`; when `.spack-env/` exists; `spack buildcache check` right after a push with no `--update-index`; `spack buildcache push --force --only package <mirror> /<hash>...`. Recorded now in `specs/008-repeat-runs-say-so/research.md` R1 to R4

---

## Phase 2: Foundational

- [X] T003 In `plugins/module_utils/spack.py`, read the merged `modules` configuration and the module roots from `config get --json modules` and `spack location -r` (`Spack.modules_config`, `Spack.module_roots`), with no PyYAML (research R1)
- [X] T004 In `plugins/module_utils/spack.py`, keep a module's own state in the environment's `.spack-env/` directory: `read_state`, which reads a missing or unreadable file as none, and `write_state`, which replaces the file in one step; and `data_digest` for the configuration (research R2)
- [X] T005 [P] In `tests/unit/fake_spack.py`, answer `config get --json modules` with Spack's default roots, write Spack's time line into each module file on `module <system> refresh`, push chosen hashes with `--only package`, word its push lines another way with `push_format: other`, and answer `buildcache check` from what its mirror holds

---

## Phase 3: User Story 1 and 2 - Module files regenerated only when they need to be (Priority: P1)

- [X] T006 [US1] Write unit tests in `tests/unit/test_spack_env.py`: a repeat run with the default touches no module file and says `not_needed`; `always` regenerates every run with no change reported; installing alone is a reason; `not_requested`; an unknown `refresh_modules` refused
- [X] T007 [US2] Write unit tests in `tests/unit/test_spack_env.py`: the stamp's contents; outdated by a lock change, by a modules configuration change, by a module file deleted by hand and by one edited by hand, and not by Spack's time line alone; a missing root; no stamp; a system the stamp does not know; check mode after a hand change and after a run
- [X] T008 [US1] In `plugins/modules/spack_env.py`, add `refresh_modules` (`when_needed` by default, `always`) and `refresh_reason()`, which gives the reason in the order of `specs/008-repeat-runs-say-so/data-model.md`; regenerate only on a reason other than `not_needed`
- [X] T009 [US2] In `plugins/modules/spack_env.py`, write the stamp `.spack-env/csis_spack.modules.json` after every regeneration: the digests of `spack.lock`, of the merged `modules` configuration, and of each module tree with Spack's time line left out
- [X] T010 [US1] In `plugins/modules/spack_env.py`, return `modules_reason` on every run; in check mode give the reason and report the module files as changing only for `missing_root` and `files_changed`
- [X] T011 [US1] In `plugins/modules/spack_env.py`, document `refresh_modules` and `modules_reason`; and, in `delete_tree`'s documentation, that Spack's default module root is shared by every environment of a Spack and `--delete-tree` removes all of it (found while writing it, research R5)

---

## Phase 4: User Story 3 - What was pushed is known from the mirror (Priority: P2)

- [X] T012 [US3] Write unit tests in `tests/unit/test_spack_buildcache_push.py`: the mirror asked before and after the push; the stand-in wording its lines another way reports the same; only what the mirror gained is reported
- [X] T013 [US3] In `plugins/modules/spack_buildcache_push.py`, ask `spack buildcache check` before and after the push (`lacking()`), and report as pushed what the mirror lacked before and has after, externals and `only` applied as in check mode; stop reading the printed lines (`pushed_specs()` removed)

---

## Phase 5: User Story 4 - `force: once`, and saying so when `force` is left on (Priority: P3)

- [X] T014 [US4] Write unit tests in `tests/unit/test_spack_buildcache_push.py`: `force: true` overwrites and reports everything every run, and warns; no warning without it; `force: once` overwrites each package one time, remembers per mirror, overwrites only a package that is new, and in check mode lists what it would overwrite and writes nothing; `force` other than true, false or once refused
- [X] T015 [US4] In `plugins/modules/spack_buildcache_push.py`, take `force` as `false`, `true` or `once` (`read_force()`); for `once`, overwrite by hash with `--only package --force` the selected packages not yet in `.spack-env/csis_spack.pushed.json` for this mirror URL, then push normally, then record them (research R4)
- [X] T016 [US4] In `plugins/modules/spack_buildcache_push.py`, warn on every real run with `force: true` that it overwrites every package and reports a change every run, naming `force: once`; document the three values

---

## Phase 6: Integration, documentation and acceptance

- [X] T017 In `tests/integration/test_real_spack.py`, against the real Spack v1.2.0: a second run with `when_needed` leaves every module file with its modification time; `always` rewrites them without a change; a deleted module file is put back; a changed modules configuration regenerates with nothing to install; the push is reported once, from the mirror; `force: once` overwrites one time; `force: true` warns
- [X] T018 [P] In `README.md`, describe `refresh_modules` and what was pushed; say what the two files in `.spack-env/` are, that the directory is Spack's, that Spack leaves them alone and removes them with the environment, and that deleting either is safe; and say to give each environment its own module root or set `delete_tree: false`
- [X] T019 [P] In `CHANGELOG.md`, record the work (then under 0.2.0; it is now under 0.0.1), and set the modules' `version_added` for the new options (since withdrawn: the modules carry `version_added: 0.0.1`)
- [X] T020 Run `just test` (72 unit tests through `ansible` against the stand-in, 45 before) and see it pass
- [X] T021 Run `just full-test` (the integration test against the real Spack v1.2.0, and `ansible-test sanity` on both modules) and see it pass
- [X] T022 Merge `feature/coll-stage-1` into `develop`, tag 0.2.0 and push, each on the operator's word (2026-11-14). Withdrawn on 2026-11-18; the work went out in 0.0.1

## Dependencies & Execution Order

- T001 and T002 before everything else.
- T003 and T004 before T008 to T010 and T013 to T015. T005 before the tests
  that use it.
- In each story the tests come before the code in this list; the record does
  not say whether they were run and seen to fail first.
- T017 to T019 after the stories; T020, T021 and T022 last, in that order.
