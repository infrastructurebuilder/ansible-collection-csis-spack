---

description: "Task list for removing the ATTIC once the specs hold everything in it"
---

# Tasks: Remove the ATTIC, because the specs hold everything in it

**Input**: Design documents from `/specs/012-remove-attic/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/live-files.md](contracts/live-files.md),
[quickstart.md](quickstart.md)

**Tests**: included and written first. The constitution asks for them
(principle IV), and the operator chose one that holds SC-002 (plan,
"Decisions to confirm", 3).

**Branch**: `feature/remove-attic`. Commit locally after each phase.
Merging, pushing and releasing happen only on the operator's word.

**Two gates belong to the operator**: the constitution's amendment (T018),
on their instruction, and the removal of `ATTIC/` (T010), on their word.
`/speckit-implement` asks for both before it starts. One answer does not
carry over to the other (principle V).

**Reading the ATTIC**: on the operator's word of 2026-11-27, for this spec
only. Phase 2 reads it to finish the coverage record, and nothing reads it
after T010.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an
  unfinished task)
- **[Story]**: the user story the task belongs to (US1, US2)
- Every check runs through the `Justfile` (`just unit`, `just test`,
  `just full-test`). Wrap a long run in `/usr/local/bin/timeout`.

---

## Phase 1: Setup

- [ ] T001 On `feature/remove-attic`, run `just test` at the repository root and see it pass, so that later failures are the new test's

---

## Phase 2: Foundational — the coverage record is complete (FR-001, SC-001, SC-004)

**Purpose**: nothing is removed until every paragraph and item of the ATTIC
is placed. This blocks T010.

- [ ] T002 [P] Write `specs/012-remove-attic/coverage/001-galaxy-publish.md`:
  - **Source:** every paragraph, bullet, table row and block of `ATTIC/COLL-INPROGRESS/COLL-STAGE-5.md` (140 lines), in order, plus `ATTIC/PLAN.md` lines 13–15 and 40–44 (the stage-5 lines).
  - **Form:** one table with the columns Lines | Source | Carried in, as in `coverage/008-repeat-runs-say-so.md`. Each "Carried in" cell links a section of `specs/001-galaxy-publish/spec.md`, `plan.md` or `tasks.md`, or says **Not carried** with one of the reasons in [data-model.md](data-model.md).
  - **Known:** lines 8–12, why stage 5 came before the Cloud Sandbox's relocation, are "the Cloud Sandbox's work, recorded in that repository" (research R1).
  - **Ending:** sections "Where the source and the code disagree" and "Could not place".
- [ ] T003 [P] Write `specs/012-remove-attic/coverage/plan-header.md`, in the same form:
  - lines 1–8 of `ATTIC/PLAN.md`: the title, and the "closed" paragraph, carried in the constitution's Development Workflow ("There is no `PLAN.md`") and in `specs/README.md`;
  - any of lines 9–47 that none of the records for 001 and 007–011 places, checked against each record's "Collection stages" section. Lines 46–47 are the Cloud Sandbox's.

  End with "Could not place".
- [ ] T004 If T002 or T003 finds an item that no spec holds and that is still wanted, stop and ask the operator: carry it into `specs/001-galaxy-publish/` (or the spec it belongs to), or list it as not needed with their reason. Record the answer in that record's row. If nothing was found, write "nothing found" against this task
- [ ] T005 Write `specs/012-remove-attic/coverage/README.md`:
  - the seven parts of the ATTIC (`ATTIC/PLAN.md` lines 1–8, 9–47 and 49–227, and `COLL-STAGE-1.md` to `COLL-STAGE-5.md`), each with its line count and the record that covers it, as links;
  - each record's "Could not place" and "disagree" items, and where each was settled (research R2);
  - the record's state: **complete** when every part has a record and every "Could not place" says nothing, otherwise **open**, naming what is open ([data-model.md](data-model.md), "States").

  Commit.

**Checkpoint**: `coverage/README.md` says **complete**. If it says **open**, stop: T010 waits.

---

## Phase 3: User Story 1 — Everything the repository knows is in its specs (Priority: P1) 🎯 MVP

**Goal**: `ATTIC/` is gone, its last state can be found from the index, and
`just full-test` passes without it (FR-002, FR-003, FR-006, FR-007).

**Independent Test**: `test ! -e ATTIC`; the commit the index names shows
`ATTIC/PLAN.md`; `just full-test` passes.

### Tests for User Story 1 (written first; they must fail)

- [ ] T006 [US1] Create `tests/unit/test_no_attic.py` with a module docstring: spec 012 removed the ATTIC, and its content is in specs 001 and 007–011, recorded in `specs/012-remove-attic/coverage/`. Add one test whose name contains `there_is_no_attic`: `(ROOT / "ATTIC").exists()` is false. Use `from runner import ROOT`, as `tests/unit/test_no_site_knowledge.py` does
- [ ] T007 [US1] Run `just unit tests/unit/test_no_attic.py` and see it fail because `ATTIC/` exists. Do not commit T006 yet: `just test` must pass after every commit

### Implementation for User Story 1

- [ ] T008 [US1] Check FR-002: the specs the record relies on (001, 006, 007, 008, 009, 010, 011) are merged into `develop`. Each one's row in `specs/README.md` says merged or complete, and `git log develop --oneline -- specs/<dir>/spec.md` shows each. Note the result against this task
- [ ] T009 [US1] Read `ATTIC/` for anything not tracked by git (`git status --short --ignored ATTIC`), so that the removal takes nothing that history lacks. If there is something, stop and ask the operator
- [ ] T010 [US1] **On the operator's word only** (FR-003):
  1. `git rm -r -q ATTIC`, and commit it together with T006's test. The commit message says the ATTIC is removed because specs 001 and 007–011 hold its content, as recorded in `specs/012-remove-attic/coverage/README.md`.
  2. Run `just unit tests/unit/test_no_attic.py`: the test passes.
- [ ] T011 [US1] In `specs/README.md`, rewrite the paragraph below the table that says the retrospective specs were "planned then in files now in the ATTIC" (FR-006). It should say:
  - the work before Spec Kit (2026-11-13 to 2026-11-17) is recorded in specs 007–011 and 001;
  - the coverage record is [012-remove-attic/coverage/README.md](012-remove-attic/coverage/README.md);
  - the retired plans can be read in git at the parent of T010's commit, named by its short hash, with `git show <hash>:ATTIC/PLAN.md`.

  Run that command and see it print the old plan's header. Commit

**Checkpoint**: User Story 1 works: no ATTIC, its last state named, the unit test holding it.

---

## Phase 4: User Story 2 — The rules no longer speak of an ATTIC (Priority: P2)

**Goal**: no live file outside `specs/` and `CHANGELOG.md` names the ATTIC.
The constitution is amended to 1.1.0, and every comment that cited a stage
file now cites the spec that holds it (FR-004, FR-005, SC-002).

**Independent Test**: `just unit tests/unit/test_no_attic.py` passes, and so
does `git grep -n -w ATTIC -- . ':!specs' ':!CHANGELOG.md' ':!tests/unit/test_no_attic.py'`, which prints nothing.

### Tests for User Story 2 (written first; they must fail)

- [ ] T012 [US2] In `tests/unit/test_no_attic.py`, add a test whose name contains `no_live_file_names_the_attic`:
  - it runs `git grep -l -w ATTIC -- . ':!specs' ':!CHANGELOG.md' ':!tests/unit/test_no_attic.py'` in `ROOT`, with `subprocess.run` and an argument list;
  - it asserts the list of files printed is empty, with the list as the message (`git grep` exits 1 when nothing matches: accept 0 and 1, fail on anything else).

  The docstring says why `specs/` and `CHANGELOG.md` are left out: they are history, which says where the content went (spec, User Story 1, scenario 2).
- [ ] T013 [US2] Run `just unit tests/unit/test_no_attic.py` and see the new test fail, naming `.specify/memory/constitution.md`, `CLAUDE.md`, `galaxy.yml`, `Justfile`, `plugins/module_utils/spack.py` and `tests/unit/fake_spack_setup.py`

### Implementation for User Story 2

- [ ] T014 [P] [US2] In `CLAUDE.md`, remove the bullet "**Nothing in [ATTIC/](ATTIC/) can affect you unless the operator says so.**" and its continuation lines. Leave the rest as it is
- [ ] T015 [P] [US2] In `galaxy.yml`, remove `- ATTIC` from `build_ignore`, and change the comment above that group to "# Planning and agent material: Spec Kit and its specs."
- [ ] T016 [P] [US2] Change the build, the comment and the docstring that name the ATTIC:
  - `Justfile`: remove `':!ATTIC'` from the sanity tree's `git ls-files` (line 64).
  - `plugins/module_utils/spack.py`: in the comment above "Configuration, as data" (line 423), replace the reference to `ATTIC/COLL-INPROGRESS/COLL-STAGE-2.md` with `specs/009-setup-role/research.md`, R7 to R9.
  - `tests/unit/fake_spack_setup.py`: in the docstring (line 4), replace the same reference with `specs/009-setup-role/research.md` (R7 to R9, R12, R13, R16, R17).
- [ ] T017 [P] [US2] In `CHANGELOG.md`, "Before 0.0.1", replace "Their plans are kept, as history only, in [ATTIC/COLL-INPROGRESS/](ATTIC/COLL-INPROGRESS/)." with a sentence saying their plans are recorded in the specs 007 to 011 and 001, linking `specs/README.md`. In the Unreleased section, add a line saying the retired plans (the ATTIC) were removed from the repository because those specs hold them (spec 012). Nothing a user installs changes
- [ ] T018 [US2] **On the operator's instruction only** (FR-004), run `/speckit-constitution` on `.specify/memory/constitution.md` with the change the operator confirmed (plan, "Decisions to confirm"):
  - remove the section "## The ATTIC", heading to **Why**;
  - under Technical Constraints, drop `` `ATTIC/` `` from the tarball's list of development material;
  - under Development Workflow, reword "There is no `PLAN.md`" to "The one this repository had was closed on 2026-11-17; the work it planned is recorded in the specs 007 to 011 and 001." Keep "and none is created again" and the sentence after it;
  - set **Version** to 1.1.0 and **Last Amended** to the day of the amendment.

  Record what changed and why against this task and in the commit message, not in the constitution's text. Then, as Governance asks, read the open specs (013) for anything the amendment makes untrue, and correct it.
- [ ] T019 [US2] Run `just unit tests/unit/test_no_attic.py`: both tests pass. Run the `git grep` of the Independent Test above: it prints nothing. Commit

**Checkpoint**: both stories work.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T020 Run `just test`
- [ ] T021 Run `/usr/local/bin/timeout 4800 just full-test` (about 55 minutes; the limit is raised from 4200, because the last run took 58). The sanity tree and the tarball are built without `ATTIC/` (FR-007, SC-003). Fix what it finds, and run it again until it passes
- [ ] T022 Check every FR-001–FR-007 and SC-001–SC-004 of [spec.md](spec.md), and the scenarios of [quickstart.md](quickstart.md), against a test or a task above; add any that are missing
- [ ] T023 Set the Status line of `specs/012-remove-attic/spec.md` (done, the date, `just full-test` passing, not merged) and spec 012's row in `specs/README.md` (State, Tasks: 24). Commit
- [ ] T024 Outside the repository: update the agent's own memory notes that speak of the ATTIC (`speckit-workflow.md`, `collection-repo.md` and the index `MEMORY.md` in the agent's memory directory), so that they say the ATTIC was removed by spec 012 and its content is in specs 001 and 007–011. This is the spec's edge case; nothing is committed

---

## Dependencies & Execution Order

- Phase 1, then Phase 2. T002 and T003 can run together; then T004 and T005.
- Phase 2's checkpoint (**complete**) before T010.
- US1: T006 and T007, then T008 and T009, then T010 (the operator's word), then T011.
- US2 needs nothing of US1 except the test file T006 made, so it follows US1. T014–T017 can run together; T018 needs the operator's instruction; T019 last.
- Polish: T020, T021, T022, T023, then T024.

## Parallel Example: Phase 2 and User Story 2

```text
T002 specs/012-remove-attic/coverage/001-galaxy-publish.md
T003 specs/012-remove-attic/coverage/plan-header.md

T014 CLAUDE.md
T015 galaxy.yml
T016 Justfile, plugins/module_utils/spack.py, tests/unit/fake_spack_setup.py
T017 CHANGELOG.md
```

## Implementation Strategy

- **MVP**: Phases 1–3: the record complete, then the ATTIC removed and named in the index.
- **Then** Phase 4: the rules, the build and the comments; the constitution at 1.1.0.
- **Done** when T021 passes and T023 is committed. Merging into `develop` waits for the operator's word, then `/speckit-converge`.
