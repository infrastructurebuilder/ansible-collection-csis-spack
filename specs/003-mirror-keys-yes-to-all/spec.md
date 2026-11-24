# Feature Specification: `spack_gpg_key` trusts the mirrors' keys without a prompt

**Feature Branch**: none yet

**Created**: 2026-11-24

**Status**: Draft. Written in the Cloud-Sandbox workshop's session, on the
operator's instruction ("write a new spec for the collection project"), and
committed on `develop`; to be clarified, planned and built in a session of
this repository's own.

**Input**: a failure on a real head node, in the Cloud-Sandbox workshop's
spec 002 (a RHEL 10 build cache), 2026-11-24. A play applying the `setup`
role with a `gpg_key` step of `from_mirrors: true` stopped:

```text
spack buildcache keys --install --trust failed (exit 3):
==> Trust key: 8D58116F59406FF3B70812BA065FBB8F66F38D66 [y/N] gpg: key 065FBB8F66F38D66: ... not changed
```

## Why

`spack_gpg_key` trusts keys in two ways. For a key file or URL it runs
`spack gpg trust -y <file>` (`plugins/modules/spack_gpg_key.py`, the `-y`
answers Spack's confirmation). For `from_mirrors` it runs
`spack buildcache keys --install --trust` with no `-y`. Spack 1.x asks
"Trust key: <fingerprint> [y/N]" for each key a mirror publishes, and under
Ansible there is no terminal to answer it, so the command reads end-of-file
and fails.

It went unseen because:

- the unit tests run a fake Spack that never asks, and one of them holds the
  command to its present form, without `-y`
  (`tests/unit/test_spack_gpg_key.py`, `test_the_keys_the_mirrors_publish_are_trusted`);
- the integration tests against the real Spack do not exercise
  `from_mirrors`;
- a mirror that publishes no keys, or none in the layout Spack 1.x reads,
  never prompts. The prompt appeared once a mirror in Spack's own layout
  (written by `spack buildcache push` in Spack 1.2.0) published a key.

Spack asks even for a key that is trusted already: the failing run's key was
in the keyring ("not changed") and was asked about again.

The Cloud-Sandbox's playbooks (`csis-sandbox-provisioning`) worked around it
the same day by running `spack buildcache keys --install --trust
--yes-to-all` through this collection's generic `command` step in place of
`from_mirrors`. They can go back to `from_mirrors` once this is released.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The mirrors' keys are trusted, unattended (Priority: P1)

A site's play applies the `setup` role with a `gpg_key` step of
`from_mirrors: true`, against mirrors that publish keys, and the keys are
trusted with no prompt, as a key from a file is.

**Why this priority**: today the step fails on every run against a mirror that
publishes a key, which is the case it exists for.

**Independent Test**: against the real Spack, a mirror in a directory that
publishes a key (a package pushed to it signed with a test key); the step
trusts the key and reports a change; run again, it reports none.

**Acceptance Scenarios**:

1. **Given** a binary mirror that publishes one key Spack does not trust,
   **When** the step runs, **Then** it finishes with no prompt, Spack trusts
   the key, and the step reports it as newly trusted.
2. **Given** the same mirror and the key already trusted, **When** the step
   runs again, **Then** it finishes with no prompt and reports no change.
3. **Given** a mirror that publishes several keys, **When** the step runs,
   **Then** all of them are trusted, with no prompt.

### User Story 2 - The tests would have caught it (Priority: P2)

The tests exercise `from_mirrors` against the real Spack, so that a Spack
release that adds or changes a confirmation is found by `just full-test`, not
on a head node.

**Why this priority**: the fake Spack cannot know what the real one asks; the
same gap could hide the next prompt.

**Independent Test**: the new integration test fails on the module as it is
today (it reads end-of-file at the prompt), and passes with the fix.

### Edge Cases

- A key a mirror publishes that is already trusted: Spack still asks; the
  step must not stop, and must report no change (Principle II).
- No binary mirror configured: the step fails as Spack does ("Please add a
  spack mirror"), as today.
- Check mode: nothing is run and nothing trusted, as today; the step says it
  could not preview (`previewed: false`).
- A Spack older than the collection's floor that has no `--yes-to-all` on
  `buildcache keys`: the collection needs Spack 1.0 or later; if any 1.x
  lacks the option, the module says so rather than failing obscurely.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: With `from_mirrors: true`, `spack_gpg_key` MUST run
  `spack buildcache keys --install --trust --yes-to-all` (or `-y`), so that
  Spack's confirmation is answered, as it already is for `spack gpg trust -y`.
- **FR-002**: The step's report MUST stay as it is: a change only for keys
  trusted afterwards and not before (from `spack gpg list --trusted`), so a
  second run against the same mirrors reports none (Principle II).
- **FR-003**: An integration test against the real Spack MUST exercise
  `from_mirrors` with a mirror that publishes a key, made in the test (a
  throwaway signing key, a package pushed signed to a mirror in a directory),
  covering User Story 1's three scenarios; it MUST fail on the module as it
  is today.
- **FR-004**: The unit test that holds the command's arguments MUST hold them
  to the new form.
- **FR-005**: The module's documentation MUST say that the keys a mirror
  publishes are trusted without confirmation, which is what `from_mirrors`
  asks for: every key the mirrors publish, with no fingerprint to check them
  against. It SHOULD point at `key` with `fingerprint` as the way to trust one
  known key.
- **FR-006**: The fix MUST go out in a release (the next of the 0.0 series, by
  semantic versioning a patch), with a changelog entry naming the failure it
  fixes; releasing is on the operator's word (Principle V).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A play applying the `setup` role with `from_mirrors: true`
  against a mirror that publishes a key finishes with no prompt, and a second
  run reports no change.
- **SC-002**: The new integration test fails on 0.0.2's module and passes on
  the fixed one, through `just full-test`.
- **SC-003**: After the release, the Cloud-Sandbox's playbooks can replace
  their `command` steps with `from_mirrors` again; that change is theirs, not
  this spec's.

## Assumptions

- Spack 1.2.0's `spack buildcache keys` has `-y, --yes-to-all` ("assume 'yes'
  is the answer to every confirmation request"); seen on the head node,
  2026-11-24.
- The collection's floor stays Spack 1.0; whether 1.0 and 1.1 have the option
  is to be checked while planning.

## Dependencies

- None in this repository. The Cloud-Sandbox's `csis-sandbox-provisioning`
  pins this collection (`>=0.0.1,<0.1.0`) and will take the release.

## Out of Scope

- Pinning the keys a mirror publishes to fingerprints (a different feature:
  `key` with `fingerprint` already does that for one key).
- Changing the Cloud-Sandbox's playbooks.
