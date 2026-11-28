# Feature Specification: Remove the ATTIC, because the specs hold everything in it

**Feature Branch**: `feature/remove-attic`

**Created**: 2026-11-27

**Status**: Done 2026-11-28: the coverage record is complete, `ATTIC/` is removed, the constitution is at 1.1.0, and `just full-test` passes (356 unit, 30 integration). Merged into `develop` (`b161d9b`) and converged 2026-11-28; not released (nothing a user installs changes).

**Input**: The operator, 2026-11-27: "The goal is to have the information in
the ATTIC become redundant and to make speckit hold specs for all the work so
we can remove ATTIC … I also want a final spec for 'Remove ATTIC because it is
redundant'."

## Clarifications

### Session 2026-11-27

- Recorded on the operator's yes to the plan, 2026-11-27: the
  constitution's amendment takes it from 1.0.1 to 1.1.0; the section "The
  ATTIC" is removed with nothing in its place, the bullet on `PLAN.md` says
  the old plan's work is recorded in the specs 007 to 011 and 001, and the
  amendment's "what changed and why" is recorded in the commit and this
  spec's tasks, not in the constitution's text; and a unit test,
  `tests/unit/test_no_attic.py`, holds SC-002.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Everything the repository knows is in its specs (Priority: P1)

A reader, a reviewer or a new session wants to know why the collection is as
it is: what was decided, by whom, and what Spack was found to do. Today part
of that is only in `ATTIC/`, which the constitution forbids an agent to read
and which no reader is pointed to. After this spec, every piece of it is in a
spec under `specs/`, and `ATTIC/` is gone.

**Why this priority**: it is the whole of the feature. Knowledge that only
the ATTIC holds is knowledge no agent may use.

**Independent Test**: for every paragraph and item of `ATTIC/PLAN.md` and of
each file in `ATTIC/COLL-INPROGRESS/`, name the spec, file and section that
carries it, or the reason it is no longer needed; find none unaccounted for.
Then remove `ATTIC/`, and see `just full-test` pass and no live file point
into it.

**Acceptance Scenarios**:

1. **Given** the ATTIC as it is on 2026-11-27, **When** each of its files is
   read against the specs, **Then** every paragraph and item is carried by a
   named spec (001, 007–011, or 006 for the two limits), or is listed with
   the reason it is not needed (a withdrawn version number, a pin that the
   history reset replaced, work that belongs to the Cloud Sandbox and is
   recorded there).
2. **Given** that record, **When** `ATTIC/` is removed, **Then** no file of
   the repository links to it or names a file in it, but for the history in
   `CHANGELOG.md` and in finished specs, which say where it went.
3. **Given** the repository without `ATTIC/`, **When** `just full-test` runs,
   **Then** it passes.

---

### User Story 2 - The rules no longer speak of an ATTIC (Priority: P2)

The constitution's section "The ATTIC", the repository's `CLAUDE.md`, the
build's `build_ignore` and the sanity test's exclusions all name `ATTIC/`.
With it gone, they say nothing of it, or say what replaced it, so that an
agent does not look for it and the rules hold no dead clause.

**Why this priority**: a rule about a directory that does not exist confuses
the next reader, but does no harm until then.

**Independent Test**: search every live file for "ATTIC"; each hit is
history that says where the content went, or nothing.

**Acceptance Scenarios**:

1. **Given** the constitution, **When** it is amended by
   `/speckit-constitution` on the operator's instruction, **Then** the section
   "The ATTIC" and its other mentions are removed or reworded, the version
   and "Last Amended" change by its own governance rules, and the amendment
   says what changed and why.
2. **Given** `CLAUDE.md`, `galaxy.yml`, the `Justfile` and the code comments
   that cite the ATTIC, **When** they are read, **Then** none names `ATTIC/`;
   a comment that cited a stage file cites the spec that now holds it.

---

### Edge Cases

- **Something in the ATTIC is found that no spec carries and that is still
  wanted**: it is carried into the right spec first (or a new one, on the
  operator's word), before anything is removed.
- **A finished spec that names the ATTIC** (its Constitution Check row "The
  ATTIC: not consulted", or its Input line saying what it was converted
  from): it is history, written when the ATTIC existed; it is left as written
  and the specs index says where the ATTIC's content went.
- **Git history**: removing `ATTIC/` removes it from the working tree, not
  from history; its last state stays recoverable from the commit before its
  removal, which the specs index names.
- **The agent's own memory notes** that mention the ATTIC are the agent's to
  update, not part of the repository.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Before anything is removed, a coverage record MUST map every
  paragraph and item of `ATTIC/PLAN.md` and of each file in
  `ATTIC/COLL-INPROGRESS/` to the spec, file and section that carries it, or
  to the reason it is not needed. It is kept in this spec.
- **FR-002**: This spec MUST NOT be carried out until the specs it relies on
  for that coverage (001, 006, 007–011) are merged into `develop`.
- **FR-003**: `ATTIC/` MUST be removed from the repository, on the
  operator's word (the constitution forbids an agent to delete anything under
  `ATTIC/` otherwise).
- **FR-004**: The constitution MUST be amended, by `/speckit-constitution`
  on the operator's instruction and under its own Governance section, so
  that no clause speaks of an ATTIC that does not exist.
- **FR-005**: `CLAUDE.md`, `galaxy.yml`'s `build_ignore`, the `Justfile`'s
  sanity-tree exclusions, the comments in `plugins/module_utils/spack.py` and
  `tests/unit/fake_spack_setup.py`, and the link in `CHANGELOG.md` MUST no
  longer point into `ATTIC/`. A comment that cited a stage file cites the
  spec that now holds it; the changelog's history says where the stage files
  went.
- **FR-006**: The specs index (`specs/README.md`) MUST say, below its table,
  that the work before Spec Kit is recorded in specs 007–011 and 001, and
  name the commit before the ATTIC's removal.
- **FR-007**: `just full-test` MUST pass after the removal.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero paragraphs or items of the ATTIC are unaccounted for in
  the coverage record.
- **SC-002**: After the removal, a search of the repository's live files for
  `ATTIC` finds only history that says where its content went.
- **SC-003**: `just full-test` passes without `ATTIC/`.
- **SC-004**: A new session, given only the repository, can answer every
  question the ATTIC could have answered, from the specs.

## Assumptions

- The retrospective specs 007–011 are written from the ATTIC's files with
  coverage records of their own; this spec's record gathers them and adds
  `ATTIC/PLAN.md`'s own sections and spec 001's for stage 5.
- The constitution's amendment is the operator's to approve, as every
  amendment is.
- No release is cut by this spec: the ATTIC is not in the tarball
  (`build_ignore`), so nothing a user installs changes.
