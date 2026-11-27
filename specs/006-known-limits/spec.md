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
- Q: In check mode, `spack_env` previews from a copy of the environment, so
  files its `spack.yaml` names by a relative path are not found. What should
  happen? → A: Bring them along: before the copy is concretized, the files
  and directories that relative `include:` and `develop:` paths name are
  copied in, so that they resolve as they do for the real environment. A
  path the copy cannot reproduce, one that leads above the environment's
  directory, is named in the result and in the documentation.
- Recorded on the operator's yes to the plan, 2026-11-27: tried against the
  real Spack (research R2 to R4), the answer above cannot work as written:
  the files inside the environment are copied already, Spack refuses a copy
  without a required `include:`, and every relative `develop:` path gives
  the copy a lock a real run would not write. Instead, the copy's relative
  `include:` and `develop:` paths are rewritten to the originals' absolute
  paths, so that the preview reads and records what a real run would. And
  the index limit turned out not to be one (research R1): Spack itself
  rebuilds the index only after a push that sent something.

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

1. **Given** an environment whose `spack.yaml` names files by a relative
   path, inside its directory or above it (`include: [./extra.yaml,
   ../shared.yaml]`), **When** `spack_env` runs in check mode, **Then** the
   preview reads those files where they are and concretizes as a real run
   would, and nothing of the real environment, or around it, is written.
2. **Given** a `develop:` package with a relative `path`, **When**
   `spack_env` runs in check mode after a real concretize, **Then** the
   preview reports no change: it records the same develop path a real run
   does.
3. **Given** the module's documentation, **When** a site reads check mode,
   **Then** it says what the preview sees of files named by relative paths.

---

### Edge Cases

- **An `include:` or `develop:` path that is absolute**: it resolves the same
  from the copy, and is not this spec's concern.
- **A relative path that points outside the environment's directory**
  (`../shared.yaml`): it is read where it is, as for the real environment
  (FR-004).
- **A relative path that names nothing**: as for the real environment,
  Spack reports it; the preview does not invent it.
- **A `develop:` source tree**: it is not copied; the preview names its
  real path, as a real run does, and reads nothing of it.
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
  today. (Spack already behaves so on 1.0, 1.1 and 1.2: research R1. The
  module's part is to say so and to hold it with a test.) The documentation of `update_index` MUST say that an index changed
  by other means is not put right by a run with nothing to push.
- **FR-003**: `spack_env`'s documentation of check mode MUST say what the
  preview sees of files that `spack.yaml` names by a relative path, and what
  a site with such an environment should do.
- **FR-004**: In check mode, before the copy of the environment is
  concretized, every relative path in its `spack.yaml`'s `include:` (a
  string, or a mapping's `path`) and in its `develop:` entries' `path` MUST
  be rewritten to the absolute path it names from the real environment's
  directory, so that the preview reads and records what a real run would.
  Absolute paths, and paths with `$`, are left as they are. Nothing of the
  real environment, or of what its paths name, changes.
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
