# Feature Specification: The install step moves a Spack to another version, when a site asks

**Feature Branch**: `feature/move-spack-version`

**Created**: 2026-11-25

**Status**: Done 2026-11-26: `just test` (345 tests) and `just full-test`
pass; merged into `develop` (`0b7babe`) 2026-11-27. Released in 0.0.4 on Ansible Galaxy, 2026-11-27. It changes spec
004's install step ([specs/004-install-spack/](../004-install-spack/spec.md)),
merged into this branch on 2026-11-26

**Input**: The operator, answering spec 004's question about a Spack already
at the destination at another version: "Q2: A", fail and change nothing,
"Also for Q2, make a spec for B": B being "move it to the version named, and
report a change". Spec 004 records the answer under Clarifications. This
spec adds B as a choice a site makes, off by default, so that 004's answer
stays what happens when a site does not make it.

## Clarifications

### Session 2026-11-26

- Q: When the new version would overwrite a file the site added to the
  Spack's directory, what should the move do? → A: Refuse the move, change
  nothing, and name the files in the way; the site moves them aside and runs
  again. (Git itself would replace such a file without a word: research R2.)
- Q: In check mode, should the step ask the source whether the version named
  exists? → A: No. Check mode contacts no source, as spec 004's does not: it
  reports the move it would make, and says that whether the version exists,
  and whether the move would overwrite a site's file, are found only when the
  move is made.
- Q: After a move from a different source than the one the Spack was first
  installed from, which source should the Spack's own git record as its
  origin? → A: The source named in the step: after a move, `origin` is set
  to it, so that it names where the current version came from.
- Q: What should the new option on the install step, and its result, be
  called? → A: As the plan proposed: the option `move` (true or false,
  default false), `version_added: 0.0.4`, and the result key `moved_from`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A site moves its nodes to a new Spack by changing one value (Priority: P1)

A site's nodes have Spack v1.1.0, installed by the role's install step. The
site wants v1.2.0. It changes the version in its install step, says on that
step that the Spack there may be moved, and applies the role. Each node's
Spack is moved to v1.2.0 in place, at the same destination, and the steps
after it run the new version.

**Why this priority**: it is the whole of the feature. Without it, spec 004
makes a site move its Spack by hand, or install the new version at a new
destination and change every path that names the old one.

**Independent Test**: install Spack at one version with the install step,
then apply the role again with another version and the move allowed; see
the Spack at the destination report the new version and the step report a
change. Apply it once more; see no change.

**Acceptance Scenarios**:

1. **Given** a Spack at the destination at another version than the one
   named, and the move allowed, **When** the role is applied, **Then** the
   Spack there is moved to the version named, and the step reports a change
   that names the version it found and the version it moved to.
2. **Given** the same node, **When** the role is applied again, **Then** the
   step reports no change.
3. **Given** a Spack at the destination at another version, and the move
   **not** allowed (the default), **When** the role is applied, **Then** the
   step fails and changes nothing, as spec 004 says.
4. **Given** a Spack at the destination at another version, and the move
   allowed, **When** the role is applied in check mode, **Then** the step
   reports that it would move the Spack, from which version to which, and
   nothing on the node changes.
5. **Given** an older version named than the one there, and the move
   allowed, **When** the role is applied, **Then** the Spack is moved back
   to it, the same way as forward.

---

### User Story 2 - What a site keeps in its Spack is not lost (Priority: P2)

A Spack's directory holds more than Spack's own files: the site's
configuration in it, the packages it built, and sometimes edits a site made
to Spack's own files. A move keeps what the site added, and refuses rather
than overwrite what the site edited.

**Why this priority**: a move that loses a site's built packages or its
edits costs hours of rebuilding or a lost fix, and cannot be undone.

**Independent Test**: on a Spack installed by the step, add a configuration
file and edit one of Spack's own files; apply the role with another version
and the move allowed; see the step fail with nothing changed. Undo the edit,
apply again; see the move done and the added file still there.

**Acceptance Scenarios**:

1. **Given** a Spack whose own files a site has edited, **When** a move is
   attempted, **Then** the step fails, names the edited files, and changes
   nothing.
2. **Given** a Spack with files a site added (its configuration in the
   Spack's directory, packages built into it), **When** it is moved,
   **Then** those files are there afterwards, unchanged.

---

### Edge Cases

- **The new version has a file where the site added one** (Spack 1.2 has
  `etc/spack/site/README.md`, which Spack 1.0 leaves to the site): the move
  is refused, nothing changes, and the files are named. The same holds for a
  site's file where the new version has a directory (a file named
  `etc/spack/site` against Spack 1.2's `etc/spack/site/README.md`). The site
  moves its files aside and runs again.
- **The version named does not exist in the source**: the step fails before
  anything at the destination changes, and says which version it could not
  find and where it looked.
- **The Spack at the destination was not installed from git** (copied from
  an archive, for example): it cannot be moved. The step fails and changes
  nothing, and says why.
- **The source named differs from the one the Spack there came from**: the
  version is fetched from the source named in the step, which is the site's
  current choice, and the Spack's git then records that source as its
  origin.
- **A move is stopped part-way**: a later run either completes it or fails
  and says what it found. It never reports success over a Spack that does
  not run, or over one at neither version.
- **The version moved to is older than 1.0**: refused as spec 004 refuses
  installing one, before the Spack there is changed.
- **Environments and packages built by the old version**: left as they are.
  Whether they still work with the new version is Spack's matter and the
  site's; the step's documentation says that they may need to be
  concretized and installed again.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Spec 004's install step MUST take an option that allows it to
  move a Spack at the destination to the version named. It MUST be off by
  default.
- **FR-002**: With the option off, a Spack at the destination at another
  version MUST be handled as spec 004's FR-007 says: the step fails and
  changes nothing.
- **FR-003**: With the option on, a Spack at the destination at another
  version MUST be moved to the version named, at the same destination, and
  the step MUST report a change naming the version found and the version
  moved to. Moving to an older version MUST work the same way. After a move,
  the Spack's git MUST record the source named as its origin.
- **FR-004**: With the option on, a Spack at the destination at the version
  named MUST be left alone, with no change reported.
- **FR-005**: Before moving, the step MUST refuse, changing nothing, when
  Spack's own files at the destination have been edited, and MUST name the
  edited files.
- **FR-006**: A move MUST keep every file a site added in the Spack's
  directory, unchanged. When the version moved to has a file of its own at
  the same place as a file the site added, or a directory where the site has
  a file, the move MUST be refused before anything at the destination
  changes, naming those files.
- **FR-007**: A move MUST NOT start until the version named has been found
  in the source; if it is not found, nothing at the destination changes.
- **FR-008**: After a move, the step MUST check that the Spack runs and
  reports the version moved to, 1.0 or later, as spec 004's FR-006 says for
  an install.
- **FR-009**: In check mode, with the option on, the step MUST report the
  move it would make (from which version to which) and change nothing on the
  node, including Spack's own history at the destination. It MUST NOT
  contact the source, and its report MUST say that whether the version
  exists and whether the move would overwrite a site's file are found only
  when the move is made.
- **FR-010**: The step MUST NOT rebuild, reconcretize or remove anything
  that the old version built.
- **FR-011**: The option's documentation MUST say what a move does and keeps,
  that it is off by default, that a move does not rebuild what the old
  version built, and that the steps after it run the new version.
  `CHANGELOG.md` and the role's README MUST describe it.

### Key Entities

- **The move option**: `move`, an option of the install step (the `spack`
  step and the module `spack_checkout`), off by default, that allows a
  version change at the destination. After a move, the result's `moved_from`
  names the version that was there.
- **Edited files**: Spack's own files at the destination that differ from
  the version they came from. They stop a move.
- **Added files**: files at the destination that are not Spack's own (the
  site's configuration, packages built into Spack's directory). A move keeps
  them.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A site moves a node's Spack to another version by changing one
  value, the version, with the move allowed on its install step, in one
  application of the role.
- **SC-002**: A second application after a move reports no change.
- **SC-003**: Without the option, no Spack at the destination is ever
  changed to another version: every such case ends in a failure with
  nothing changed.
- **SC-004**: No move loses a file a site added, and no move overwrites a
  file a site edited: each is held by a test that fails if it does.
- **SC-005**: Check mode leaves the node exactly as it was, in every case.
- **SC-006**: Moving forward and back between the Spack versions the
  collection is tested against (1.0.0, 1.1.0, 1.2.0) is proved against the
  real Spack.

## Assumptions

- Spec 004 is built first, with its answers: a git repository only as the
  source, and failure on another version by default. This spec changes only
  what happens when a site turns the new option on.
- A move is done in place, at the destination, as a git checkout of another
  version. A move that installs side by side and switches a link is not
  asked for.
- "Spack's own files" are those its git repository tracks at the version
  installed; everything else at the destination is the site's.
- Rebuilding what the old version built is not this step's work. A site
  that needs it adds steps of its own after the install step.
- No release is cut by this spec. It goes out in a release after spec 004's,
  or with it, on the operator's word.
