# Feature Specification: Two known limits, said where a site reads them, or removed

**Feature Branch**: `feature/known-limits`

**Created**: 2026-11-27

**Status**: Draft

**Input**: The operator, 2026-11-27, after reading what the ATTIC holds that no
live file says: "I want the new small spec for the two undocumented
limitations." The two limits were recorded on 2026-11-14 as out of scope in
the plan of the work that made repeat runs do nothing and say so (spec 008,
the retrospective of that work), and are true of the code today.

## Clarifications

### Session 2026-11-27

- Q: When `spack_buildcache_push` runs with `update_index: true` and there is
  nothing new to push, should it still rebuild the mirror's index? → A: No.
  The index is rebuilt only after a push that sent something, so a repeat
  run changes nothing. An index that drifted by other means is not put right
  by an ordinary run.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A site that rebuilds a mirror's index knows what each run does (Priority: P1)

A site pushes an environment's packages to a mirror with
`spack_buildcache_push` and `update_index: true`. Every run rebuilds the
mirror's index, whether anything was pushed or not, and the task reports no
change when nothing was pushed. A site that reads the module's documentation
learns this before it finds it out on a large mirror, where rebuilding the
index takes minutes.

**Why this priority**: the module promises that a repeat run changes nothing
and says so (constitution, principle II). Rebuilding the index is a change to
the mirror that the task does not report. Either the documentation says so,
or the module stops doing it.

**Independent Test**: push an environment twice to a mirror with
`update_index: true`; see what the second run does to the index, and that
what it does is what the documentation says.

**Acceptance Scenarios**:

1. **Given** an environment already pushed to a mirror, **When**
   `spack_buildcache_push` runs again with `update_index: true`, **Then**
   nothing is pushed, the mirror's index is not rebuilt, and the task
   reports no change.
3. **Given** an environment with a package the mirror lacks, **When**
   `spack_buildcache_push` runs with `update_index: true`, **Then** the
   package is pushed, the index is rebuilt, and a change is reported.
2. **Given** the module's documentation, **When** a site reads
   `update_index`, **Then** it says what a run with nothing to push does to
   the index.

---

### User Story 2 - A site that previews an environment with files beside it knows what the preview sees (Priority: P2)

A site's environment's `spack.yaml` names other files by a path relative to
the environment's directory: an `include:` of a configuration file, or a
`develop:` package's source. In check mode `spack_env` concretizes a copy of
the environment in a temporary directory, where those relative paths point
at nothing. The preview then fails, or concretizes something other than what
a real run would.

**Why this priority**: check mode is how a site previews a long build
(principle II and the retrospective spec 011). A preview that differs from
the run is worse than none. It is P2 because environments that use relative
`include:` or `develop:` are fewer than those that do not.

**Independent Test**: an environment whose `spack.yaml` includes
`./extra.yaml`; run `spack_env` in check mode; see that the preview is what
the documentation says it is.

**Acceptance Scenarios**:

1. **Given** an environment whose `spack.yaml` names a file by a relative
   path, **When** `spack_env` runs in check mode, **Then** [NEEDS
   CLARIFICATION: is the limit only documented (the preview may fail or
   differ, and the documentation says so and what to do), or removed (the
   files the relative paths name are copied with the environment, or the
   copy is made so that they resolve, and the preview matches a real run)?].
2. **Given** the module's documentation, **When** a site reads check mode,
   **Then** it says what the preview sees of files named by relative paths.

---

### Edge Cases

- **An `include:` or `develop:` path that is absolute**: it resolves the same
  from the copy, and is not this spec's concern.
- **A relative path that points outside the environment's directory**
  (`../shared.yaml`): it is named by the same rule as any relative path.
- **`update_index: true` with `force`**: a forced push is a push, so the
  index is rebuilt after it, as today.
- **An index that drifted** (a mirror edited by hand, a push from elsewhere
  without `--update-index`): a run with nothing to push leaves it as it is.
  A site that wants it rebuilt runs `spack buildcache update-index` itself,
  for example in a `command` step.
- **A mirror that cannot be written to**: as today, the push fails.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `spack_buildcache_push`'s documentation of `update_index` MUST
  say what a run does to the mirror's index when nothing is pushed, and
  whether that is reported.
- **FR-002**: With `update_index: true`, a run with nothing to push MUST NOT
  rebuild the mirror's index; a run that pushes something MUST rebuild it, as
  today. The documentation of `update_index` MUST say that an index changed
  by other means is not put right by a run with nothing to push.
- **FR-003**: `spack_env`'s documentation of check mode MUST say what the
  preview sees of files that `spack.yaml` names by a relative path, and what
  a site with such an environment should do.
- **FR-004**: In check mode, an environment whose `spack.yaml` names files by
  a relative path MUST [NEEDS CLARIFICATION: see User Story 2, scenario 1:
  be documented as possibly previewing wrongly, or be previewed with those
  files in reach].
- **FR-005**: Each behaviour this spec settles MUST be held by a test: a unit
  test against the stand-in `spack`, and, for what depends on Spack itself,
  an integration test against the real Spack 1.0.0, 1.1.0 and 1.2.0.
- **FR-006**: `CHANGELOG.md` MUST record what changed, and the retrospective
  spec 008, which lists these limits as out of scope, MUST point to this
  spec.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A site reading only the modules' documentation can say, for
  each of the two cases, what a run does, before running it.
- **SC-002**: No behaviour of either case differs from what the
  documentation says: each is held by a test that fails if it does.
- **SC-003**: Neither limit is recorded only in the ATTIC: after this spec,
  spec 012 (removing the ATTIC) finds both carried here.

## Assumptions

- The limits are as recorded on 2026-11-14 and as the code reads today:
  `spack_buildcache_push` passes `--update-index` to every push it runs, and
  it runs a push on every run; `spack_env`'s check mode copies the
  environment's directory (without `.spack-env/` and logs) into a temporary
  directory and concretizes the copy.
- Removing either limit is a change in what a module does, so it is tried
  against the real Spack first (principle III) and recorded in this spec's
  research.
- No release is cut by this spec. It goes out in the release after 0.0.4, on
  the operator's word.
