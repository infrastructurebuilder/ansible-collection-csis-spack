# Implementation Plan: Remove the ATTIC, because the specs hold everything in it

**Branch**: `feature/remove-attic` | **Date**: 2026-11-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/012-remove-attic/spec.md`

## Summary

The ATTIC is six files of plans made before Spec Kit. The retrospective
specs 007–011 were written from five of its parts, and each has a
line-by-line coverage record under [coverage/](coverage/). Research
([research.md](research.md)) found what is left:

- **Not yet recorded (R1):** `COLL-STAGE-5.md`, which spec 001 was made from
  but which was never mapped line by line, and `ATTIC/PLAN.md` lines 1–8
  (its "closed" header) with its stage-5 lines. A spot check found every
  main item of stage 5 in spec 001. The one exception is the Cloud
  Sandbox's own ordering, which is not needed here.
- **Open in the records (R2):** nothing. Each "disagree" item was carried
  as built.
- **Live files that name the ATTIC (R3):**
  - the rules: the constitution and `CLAUDE.md`;
  - the build: `galaxy.yml` and the `Justfile`;
  - two code comments;
  - one changelog link.

  Only `CLAUDE.md` and the changelog link to it.

The work has four steps:

1. Complete the coverage record and gather it in `coverage/README.md`.
2. On the operator's instruction, amend the constitution with
   `/speckit-constitution`.
3. Change the other live files, and add a test that holds the result.
4. On the operator's word, remove `ATTIC/`, name its last commit in the
   index, and pass `just full-test`.

Nothing in the tarball changes, so no release is needed.

## Technical Context

**Language/Version**: Markdown (the specs, the constitution); Python 3.12
(one comment, one docstring, one new unit test); YAML (`galaxy.yml`); the
`Justfile`

**Primary Dependencies**: Spec Kit (`/speckit-constitution`); git
(`git ls-files`, for the test)

**Storage**: N/A

**Testing**: `just test`, with a new unit test, `tests/unit/test_no_attic.py`
(proposed, R6); `just full-test`, to show the build and sanity tree
unchanged without `ATTIC/` (FR-007)

**Target Platform**: the repository; nothing on a managed node changes

**Project Type**: an Ansible collection; this changes its planning material,
its rules and two comments, not its plugins

**Performance Goals**: N/A

**Constraints**:

- Nothing is removed before the coverage record is complete (FR-001).
- The specs the record relies on (001, 006, 007–011) are merged into
  `develop` first (FR-002). They are, as of 455b053.
- The constitution is amended only on the operator's instruction (FR-004).
- `ATTIC/` is removed only on the operator's word (FR-003).
- Finished specs that name the ATTIC are left as written (the spec's edge
  case).

**Scale/Scope**:

- the ATTIC's six files (1414 lines);
- 7 live files (R3);
- the specs index;
- two new coverage files and a coverage README;
- one new test.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Result |
| --- | --- | --- |
| I. A Site's Choices Are Configuration, Not Code | No plugin or role changes; two comments change their reference. | Pass |
| II. A Repeat Run Changes Nothing, and Says So | No module changes. | Pass |
| III. Written to What Spack Does | No Spack behaviour is relied on or changed. | Pass |
| IV. Acceptance Tests Run Through the Justfile | `just test` after each change, `just full-test` after the removal; a unit test holds SC-002 (R6). | Pass |
| V. The Operator Decides | The amendment and the removal each wait for the operator's word (FR-003, FR-004). The version of the amendment and the test are put to the operator below. Commits are local. | Pass |
| The ATTIC | Read on the operator's word of 2026-11-27, for this spec ("It's OK to read ATTIC/ to create these specs"). Nothing under it is changed or removed until the operator says so (FR-003). It was read for what it holds, not for what to do: what this plan does comes from the spec. | Pass |

No violations, so Complexity Tracking is not needed. Re-checked after the
design below, and unchanged. Once the amendment and the removal are done,
the last row's section no longer exists; this check was made against the
constitution as it stands today (1.0.1).

## Decisions to confirm

1. **The constitution's new version: 1.1.0** (R5). The amendment removes
   the section "The ATTIC", which is not a principle, and rewords two lines
   that name it. Governance gives MAJOR for a principle removed or redefined
   so that earlier work would break it, and PATCH for wording. This is
   neither, so MINOR is the nearest. Proposed: 1.0.1 → 1.1.0.
2. **What replaces the section: nothing, and one bullet reworded.** The
   Development Workflow bullet "There is no `PLAN.md`" would read: "The one
   this repository had was closed on 2026-11-17; the work it planned is
   recorded in the specs 007 to 011 and 001." The "what changed and why"
   that an amendment must say goes in the commit and in this spec's tasks,
   not in the constitution's text, so that the constitution does not name
   the ATTIC again (SC-002).
3. **A unit test holds SC-002** (R6). It is `tests/unit/test_no_attic.py`.
   It fails if `ATTIC/` exists, or if a tracked file outside `specs/` and
   `CHANGELOG.md` contains the word `ATTIC`. Proposed: yes.

## Design

### Step 1: the coverage record (FR-001, SC-001, SC-004)

- `coverage/001-galaxy-publish.md`: `COLL-STAGE-5.md` line by line into
  spec 001, with the `ATTIC/PLAN.md` stage-5 lines, in the form of the
  other records ([data-model.md](data-model.md)). If an item is still
  wanted and spec 001 does not hold it, it is added to spec 001 first.
- `coverage/plan-header.md`: `ATTIC/PLAN.md` lines 1–8, plus any of lines
  9–47 that no other record places. Lines 46–47 are the Cloud Sandbox's.
- `coverage/README.md`: the seven parts, each with its record, and the
  record's state.

### Step 2: the constitution (FR-004)

On the operator's instruction, `/speckit-constitution` with the change in
"Decisions to confirm":

- the section "The ATTIC" removed;
- `ATTIC/` dropped from the tarball's exclusions under Technical
  Constraints;
- the `PLAN.md` bullet reworded;
- the version and Last Amended updated.

It changes whatever in the open specs it makes untrue (Governance). Spec
013's Constitution Check, if it has one by then, would be such a change.

### Step 3: the other live files (FR-005, FR-006)

As in [contracts/live-files.md](contracts/live-files.md):

- `CLAUDE.md` loses its ATTIC bullet.
- `galaxy.yml` and the `Justfile` lose their `ATTIC` entries.
- The comment in `plugins/module_utils/spack.py` and the docstring in
  `tests/unit/fake_spack_setup.py` cite spec 009's research.
- `CHANGELOG.md`'s "Before 0.0.1" points to the specs.
- `tests/unit/test_no_attic.py` is written first and fails while `ATTIC/`
  is there.

### Step 4: the removal (FR-003, FR-006, FR-007)

On the operator's word:

1. `git rm -r ATTIC`, then commit.
2. Note the parent of that commit (R4), write it into `specs/README.md`
   below the table, and check it with `git show <hash>:ATTIC/PLAN.md`.
3. Commit again.
4. `just test`: the new test passes now.
5. `just full-test`.

### After the spec

The agent's own memory notes that speak of the ATTIC are updated by the
agent. They are not part of the repository (the spec's edge case).

## Project Structure

### Documentation (this feature)

```text
specs/012-remove-attic/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0: what is left to record, what names the ATTIC
├── data-model.md        # Phase 1: the coverage record
├── quickstart.md        # Phase 1
├── contracts/
│   └── live-files.md    # Phase 1: each live file, before and after
├── coverage/
│   ├── README.md                    # new: the whole record, part by part
│   ├── 001-galaxy-publish.md        # new: COLL-STAGE-5.md
│   ├── plan-header.md               # new: ATTIC/PLAN.md lines 1–8
│   └── 007…011-*.md                 # as written by specs 007–011
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
ATTIC/                                  # removed
.specify/memory/constitution.md         # amended
CLAUDE.md
galaxy.yml                              # build_ignore
Justfile                                # the sanity tree
plugins/module_utils/spack.py           # a comment
tests/unit/fake_spack_setup.py          # a docstring
tests/unit/test_no_attic.py             # new
CHANGELOG.md                            # "Before 0.0.1"
specs/README.md                         # the note below the table
```

**Structure Decision**: the repository's existing layout; the record stays
in this spec's `coverage/`, as the spec says.
