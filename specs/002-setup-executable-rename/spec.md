# Feature Specification: Name the setup role's Spack executable `spack_setup_executable`

**Feature Branch**: `feature/setup-executable-rename`, until the history was reset on 2026-11-18

**Created**: 2026-11-17

**Status**: Done 2026-11-17 on `feature/setup-executable-rename`: `just test`
and `just full-test` pass. It goes out with the next release.

**Input**: User description: "what is `spack_setup_spack` referred to in the
examples?", then "can we change that to `spack_setup_executable`?"

## Clarifications

### Session 2026-11-17

- Q: The variable was released in 0.3.0 and 0.3.1, and the Cloud Sandbox pins
  0.3.1. Should the old name keep working: as an alias, as an alias that
  warns, or not at all? → A: Keep the old name as an alias. No warning.
- Q: Where does the rename go: on its own branch after the Spec Kit conversion
  is merged, on its own branch from the unmerged conversion, or on the
  conversion's branch with no spec? → A: Its own branch, with its own short
  spec, after the conversion is merged into `develop`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A name that says what the variable is (Priority: P1)

Someone reading a site's configuration for the `setup` role sees
`spack_setup_executable: /opt/spack/bin/spack` and knows what it is: the Spack
executable the role runs. The old name, `spack_setup_spack`, reads as a
repetition and had to be asked about.

**Why this priority**: it is the whole of the change.

**Independent Test**: set `spack_setup_executable` to a Spack that is not on
`PATH`, apply the role, and see that Spack run.

**Acceptance Scenarios**:

1. **Given** a playbook that sets `spack_setup_executable` to a path, **When**
   the role is applied, **Then** every step runs that executable.
2. **Given** a playbook that sets neither name, **When** the role is applied,
   **Then** every step runs `spack` as found on `PATH`, as before.
3. **Given** the role's README and the examples under `docs/examples/`,
   **When** they are read, **Then** they use `spack_setup_executable`.

---

### User Story 2 - A playbook written for 0.3.1 keeps working (Priority: P2)

Someone whose playbook sets `spack_setup_spack`, as 0.3.0 and 0.3.1 document,
upgrades the collection and changes nothing. The role runs the executable they
named.

**Why this priority**: without it the rename breaks every existing user, and
breaks them quietly: the role would ignore their setting and run whatever
`spack` is on `PATH`, or fail to find one.

**Independent Test**: set only `spack_setup_spack` to a Spack that is not on
`PATH`, apply the role, and see that Spack run.

**Acceptance Scenarios**:

1. **Given** a playbook that sets only `spack_setup_spack`, **When** the role
   is applied, **Then** every step runs that executable.
2. **Given** a playbook that sets both names to different executables, **When**
   the role is applied, **Then** `spack_setup_executable` is the one that runs.

---

### Edge Cases

- Both names set: the new one wins, and nothing is said about the old one.
- The old name set to something that does not exist, and the new name not set:
  the role fails as it does today for an executable that does not exist. The
  alias does not hide a wrong value.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `setup` role MUST take the Spack executable, as a path or a
  name looked up on `PATH`, from the variable `spack_setup_executable`.
- **FR-002**: Its default MUST remain `spack`.
- **FR-003**: When `spack_setup_executable` is not set and `spack_setup_spack`
  is, the role MUST use `spack_setup_spack`'s value.
- **FR-004**: When both are set, the role MUST use `spack_setup_executable`.
- **FR-005**: The role's README, the examples and the tests MUST use the new
  name. The README MUST say that the old name still works and that it is the
  name before this release.
- **FR-006**: `CHANGELOG.md` MUST record the rename and that the old name
  still works.
- **FR-007**: The modules' own option, `spack`, MUST NOT change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A playbook written for 0.3.1 runs unchanged against 0.0.1, with
  the same result.
- **SC-002**: No file of the collection that a user reads (the role's README,
  the examples) uses the old name, except to say that it still works.
- **SC-003**: Each of the three cases (new name, old name, both) is held by a
  test that fails if the role runs a different executable.

## Assumptions

- "The old name keeps working" has no end date. Removing it would be a
  breaking change with a spec of its own.
- The Cloud Sandbox needs no change. It can move to the new name whenever it
  next changes its pin; that is its own decision, in its own repository.
- The modules' `spack` option is not part of this: it sits beside `path`,
  `scope` and the rest in a task that already names a Spack module, and reads
  clearly there.
- No release is cut by this spec. The rename goes out with the first release,
  0.0.1 ([specs/001-galaxy-publish/](../001-galaxy-publish/spec.md)).
- The versions 0.3.0 and 0.3.1 named in this spec were development versions,
  withdrawn on 2026-11-18 when the first release became 0.0.1. The old name
  stays an alias all the same: the Cloud Sandbox's playbooks set it.
