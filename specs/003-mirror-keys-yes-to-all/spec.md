# Feature Specification: `spack_gpg_key` trusts the mirrors' keys without a prompt

**Feature Branch**: `feature/mirror-keys-yes-to-all`

**Created**: 2026-11-24

**Status**: Draft. Written in the Cloud-Sandbox workshop's session, on the
operator's instruction ("write a new spec for the collection project"), and
committed on `develop`; to be clarified, planned and built in a session of
this repository's own. Clarified on `develop` and planned on its feature
branch, 2026-11-24. **Done 2026-11-25** on
`feature/mirror-keys-yes-to-all`: every task but T038 ticked, and
`just full-test` passed (270 unit tests; 15 integration tests, each of five
run against the real Spack 1.0.0, 1.1.0 and 1.2.0; `ansible-test sanity`;
Galaxy's import checks). Not yet merged into `develop` or released: both on
the operator's word (T038).

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
`spack buildcache keys --install --trust` with no `-y`. Spack 1.2 asks
`Trust key: <fingerprint> [y/N]` for each key a mirror publishes, and under
Ansible there is no terminal to answer it, so the command reads end-of-file
and fails.

Planning found the other side of it ([research.md](research.md), R2). The
prompt and its option arrived together, in Spack 1.2.0: Spack 1.0 and 1.1
never ask, and have no `-y` on `gpg trust` or `buildcache keys`. So the
`gpg trust -y` that a key file gets fails on Spack 1.0 and 1.1
(`unrecognized arguments: -y`): a defect in the released 0.0.1 and 0.0.2,
which say they support Spack 1.0 or later, unseen because only 1.2.0 is
tested. This spec fixes it too (FR-008).

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

## Clarifications

### Session 2026-11-24

- Q: If a supported Spack (1.0 or 1.1) has no `--yes-to-all` on
  `spack buildcache keys`, what does `spack_gpg_key` do with
  `from_mirrors: true`? → A: It passes `--yes-to-all` where the command's
  help lists it, and runs without it where it does not, since planning found
  that such a Spack never asks; the same holds for `gpg trust` (FR-001,
  FR-008). The floor stays Spack 1.0. This replaces an earlier answer, to
  fail where the option is missing, which the operator changed during
  planning once [research.md](research.md) (R2) showed that Spack 1.0 and 1.1
  have neither the prompt nor the option, and that `from_mirrors` works on
  them today.
- Q: Does this spec check only `buildcache keys` for an unanswered
  confirmation prompt, or every Spack command the collection runs? → A: Every
  module that runs Spack gets a `yes_to_all` flag, set for the whole `setup`
  role by `spack_setup_yes_to_all` and for one step by its own `yes_to_all`.
  When the flag is on, a command that takes `--yes-to-all` is given it
  (FR-007). This replaces an earlier answer, which was to fix in this spec
  every prompt that checking turned up.
  - Q: What is the flag's default, and does `from_mirrors` depend on it? →
    A: Off by default. `from_mirrors: true` passes `--yes-to-all` whatever
    the flag says (FR-001); the flag governs every other command.
  - Q: How does a module tell that a command takes `--yes-to-all`? → A: It
    asks the Spack that is installed: it reads `spack <command> --help` and
    adds the option only when the help lists it, and adds nothing when the
    command already has `-y` or `--yes-to-all`.
- Q: Where does the new real-Spack test of `from_mirrors` run: through the
  module, through the `setup` role, or both? → A: Both. The module test
  (`tests/integration/test_real_spack.py`, signing its zlib push) covers User
  Story 1's three scenarios; the role test
  (`tests/integration/test_real_setup.py`) runs one `from_mirrors` step twice,
  a change and then none (FR-003, SC-001).
- Q: Is the release a patch (0.0.3) or a minor version (0.1.0), given that
  it adds an option and the Cloud-Sandbox pins `<0.1.0`? → A: 0.0.3
  (FR-006). Asked during planning; when to release is still the operator's
  word.

### Session 2026-11-25

- Q: Implementing User Story 1 showed that the collection does not work with
  Spack 1.0 or 1.1 at all ([research.md](research.md), R6). Is that fixed in
  this spec, in a spec of its own, or by raising the floor? → A: In this
  spec, before User Story 2 (User Story 3, FR-009 to FR-011). Where a
  command lacks the machine-readable option the module uses (as `config get
  --json` in 1.0), the module asks the installed Spack's help, as FR-007
  does, and only then falls back: for configuration, to Spack's own
  `spack python -c`, printing the configuration as JSON
  (`spack.config.get`, or `spack.config.CONFIG.get_config` for one scope),
  which needs nothing more on the node; not to reading YAML, which would
  need PyYAML there.
- Q: Is how each Spack version differs told by reading the help of the
  installed Spack, or from a table keyed by Spack's version? → A: A table in
  the shared code, keyed by major and minor version, for the commands the
  collection runs itself (reading configuration and the trusted keys,
  answering the trust question, the wording of a missing scope); a Spack
  newer than the table's last row is read as that row. The help check stays
  only where the command is not known in advance: `yes_to_all`, above all
  `spack_command`'s. The table is built from what the integration tests find
  on the real 1.0.0 and 1.1.0, run before anything is fixed. This replaces
  the help check for `gpg trust` and `buildcache keys` (FR-001, FR-008).
- Q: On Spack 1.1, which has no configuration scope whose directory does not
  exist (the user and system scopes are optional includes), what does a
  module do when asked to write to one? → A: It fails, saying that Spack 1.1
  has no such scope until its directory exists, and which directory that is;
  it does not make the directory (Spack's own commands only). The modules'
  documentation says so, and the integration tests make the user scope's
  directory first on 1.1, as a site would ([research.md](research.md), R8).

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

### User Story 3 - The collection works on every Spack it supports (Priority: P2)

A site whose head node has Spack 1.0 or 1.1 applies the `setup` role, or
any of the modules, and it works as it does on 1.2: the collection says it
supports Spack 1.0 or later.

**Why this priority**: today every module that reads configuration or the
trusted keys fails on 1.0 or 1.1 (R6), and nothing tested it. It comes before
User Story 2 on the operator's word.

**Independent Test**: the integration tests, unchanged in what they claim,
pass against the real Spack 1.0.0, 1.1.0 and 1.2.0, through `just full-test`.

**Acceptance Scenarios**:

1. **Given** Spack 1.0.0, 1.1.0 or 1.2.0, **When** the integration tests
   run against it, **Then** they pass, with the same changes reported as on
   1.2.0.
2. **Given** a Spack whose command lacks the machine-readable option a
   module uses, **When** the module needs that output, **Then** it reads the
   same data another way that Spack has (the command's help decides), and
   reports the same result.

### User Story 2 - The tests would have caught it (Priority: P3)

The tests exercise `from_mirrors` against the real Spack, so that a Spack
release that adds or changes a confirmation is found by `just full-test`, not
on a head node.

**Why this priority**: the fake Spack cannot know what the real one asks; the
same gap could hide the next prompt. So a site can have every prompt that
Spack offers `--yes-to-all` for answered, with one flag (FR-007).

**Independent Test**: the new integration tests, of the module and of the
role, fail on the module as it is today (it reads end-of-file at the prompt),
and pass with the fix.

### Edge Cases

- A key a mirror publishes that is already trusted: Spack still asks; the
  step must not stop, and must report no change (Principle II).
- No binary mirror configured: the step fails as Spack does ("Please add a
  spack mirror"), as today.
- Check mode: nothing is run and nothing trusted, as today; the step says it
  could not preview (`previewed: false`).
- Spack 1.0 or 1.1, whose `buildcache keys` and `gpg trust` have no
  `--yes-to-all` and never ask: both run without the option, and trust as
  they do today. Nothing is answered on stdin.
- Spack 1.1, asked to write to a configuration scope whose directory does
  not exist yet (the user or system scope): Spack 1.1 has no such scope; the
  module fails, naming the scope and the directory to make, and does not
  make it (FR-009). Reading it gives an empty section, as on 1.0 and 1.2.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: With `from_mirrors: true`, `spack_gpg_key` MUST run
  `spack buildcache keys --yes-to-all --install --trust` on Spack 1.2 and
  later, so that Spack's confirmation is answered, and
  `spack buildcache keys --install --trust` on 1.0 and 1.1, which do not ask
  and refuse the option; which is told by FR-009's table. It does so
  whatever `yes_to_all` says: asking for `from_mirrors` is the site's
  consent to trust what the mirrors publish.
- **FR-002**: The step's report MUST stay as it is: a change only for keys
  trusted afterwards and not before (from `spack gpg list --trusted`), so a
  second run against the same mirrors reports none (Principle II).
- **FR-003**: Integration tests against the real Spack MUST exercise
  `from_mirrors` with a mirror that publishes a key, made in the test (a
  throwaway signing key, a package installed with `--fake` and pushed signed
  to a mirror in a directory), at two levels:
  - the module, in `tests/integration/test_real_spack.py` (signing its zlib
    push), covering User Story 1's three scenarios;
  - the `setup` role, in `tests/integration/test_real_setup.py`, running one
    `gpg_key` step of `from_mirrors: true` twice: the first run trusts the key
    and reports a change, the second reports none. That test's "nothing is
    built or fetched" no longer holds, and its docstring says what it now
    installs and pushes.

  Both MUST fail on the module as it is today.
- **FR-004**: The unit tests that hold `spack_gpg_key`'s arguments MUST hold
  them to the new forms, against a stand-in `spack` that is 1.2 and one that
  is 1.0 or 1.1 (by its `--version`) and rejects the option, for both
  `from_mirrors` and `key`.
- **FR-005**: The module's documentation MUST say that the keys a mirror
  publishes are trusted without confirmation, which is what `from_mirrors`
  asks for: every key the mirrors publish, with no fingerprint to check them
  against. It SHOULD point at `key` with `fingerprint` as the way to trust one
  known key.
- **FR-006**: The fix MUST go out in release 0.0.3, the operator's choice
  although the release also adds an option (FR-007), so that the
  Cloud-Sandbox's pin (`>=0.0.1,<0.1.0`) takes it. Its changelog entry names
  the failures it fixes (FR-001, FR-008) and the option it adds. When to
  release is on the operator's word (Principle V).
- **FR-007**: Every module in `plugins/modules/` that runs Spack MUST take a
  `yes_to_all` option (true or false, default false):
  - When it is true, before the module runs a Spack command it reads that
    command's help (`spack <command> --help`, which changes nothing and so
    also runs in check mode) and adds `--yes-to-all` only when the help lists
    it. Nothing is added when the command already has `-y` or
    `--yes-to-all`.
  - When it is false, nothing is added, apart from FR-001's `from_mirrors`.
  - The `setup` role MUST take `spack_setup_yes_to_all` (default false),
    which sets `yes_to_all` for every step; a step's own `yes_to_all`
    overrides it, as a step's `scope` overrides `spack_setup_scope`.
  - Each module's documentation and the role's README MUST say that the flag
    answers "yes" to every confirmation Spack asks of a command that takes
    it, including ones that remove or overwrite something, and that without
    it such a prompt fails the task, since Ansible gives Spack no terminal.
  - Which commands the modules run take `--yes-to-all` in the pinned Spack
    (1.2.0) is recorded in the spec's research.
  - Unit tests against the stand-in `spack` MUST cover: the flag off; the
    flag on with a command whose help lists the option and with one whose
    help does not; a command that already has `-y`; the role's variable and
    a step's override. An integration test MUST show the help check reading
    the real Spack's help correctly for a command that has the option and
    one that does not.
  - It goes out in the same release and changelog as FR-006.
- **FR-008**: With `key`, `spack_gpg_key` MUST run `spack gpg trust
  --yes-to-all <file>` on Spack 1.2 and later, and `spack gpg trust <file>`
  on 1.0 and 1.1 (FR-009's table), whatever `yes_to_all` says, as FR-001
  does for `from_mirrors`. This fixes the released defect that a key
  file cannot be trusted on Spack 1.0 or 1.1; the changelog entry of FR-006
  names it, and it goes out in 0.0.3 (FR-006).

- **FR-009**: Every module MUST work on Spack 1.0, 1.1 and 1.2. Where a
  command it runs differs between them, the module MUST tell from a table in
  `plugins/module_utils/spack.py`, keyed by the major and minor version that
  `spack --version` gives (a newer Spack is read as the table's last row),
  and, where the option it uses is missing, read the same data another way
  Spack has:
  - configuration, without `config get --json` (1.0): through
    `spack python -c`, printing as JSON what `spack.config.get(section)`
    gives (every scope merged) or
    `spack.config.CONFIG.get_config(section, scope=scope)` (one scope);
  - the trusted keys, without `gpg list --fmt colons` (1.0, 1.1): from
    `gpg list --trusted`'s own listing, which gives each fingerprint on a
    line of its own;
  - any other difference the integration tests find on 1.0.0 and 1.1.0,
    each recorded in [research.md](research.md) with what Spack printed.
  A scope whose directory does not exist yet MUST be read as empty however
  the Spack words it (1.1: `invalid choice`; 1.2: `must refer to an
  existing scope`). On Spack 1.1, which cannot write to such a scope, a
  module MUST fail with a message naming the scope and its directory, and
  MUST NOT make the directory; the documentation of every module that takes
  a scope MUST say so.
- **FR-010**: The integration tests MUST run against the real Spack 1.0.0,
  1.1.0 and 1.2.0, each cloned once into `.tmp/`, through `just full-test`
  (and `just integration`). What a test claims MUST be the same on each; a
  difference in what Spack prints is the module's to absorb, not the test's.
- **FR-011**: The stand-in `spack` MUST be able to behave as 1.0 and 1.1 do
  for each difference of FR-009, and each fallback MUST have unit tests
  against it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A play applying the `setup` role with `from_mirrors: true`
  against a mirror that publishes a key finishes with no prompt, and a second
  run reports no change; the role-level integration test (FR-003) shows it.
- **SC-002**: The new integration tests, module and role, fail on 0.0.2's
  module and pass on the fixed one, through `just full-test`.
- **SC-004**: `spack_gpg_key`, with `key` and with `from_mirrors`, and every
  other module, run on Spack 1.0 and 1.1 as on 1.2: the integration tests
  pass against the real 1.0.0, 1.1.0 and 1.2.0 (FR-010), and unit tests
  against a stand-in that behaves as each does hold the differences
  (FR-004, FR-011).
- **SC-003**: After the release, the Cloud-Sandbox's playbooks can replace
  their `command` steps with `from_mirrors` again; that change is theirs, not
  this spec's.

## Assumptions

- Spack 1.2.0's `spack buildcache keys` and `spack gpg trust` have
  `-y, --yes-to-all` ("assume 'yes' is the answer to every confirmation
  request"); Spack 1.0.0 and 1.1.0 have neither the option nor the prompt.
  Tried against the real Spack while planning ([research.md](research.md),
  R1 and R2).
- The collection's floor stays Spack 1.0. The pin stays 1.2.0, the version
  the integration tests are written to; this spec adds 1.0.0 and 1.1.0 as
  versions they also run against (Principle III's "a spec of its own" is
  this one, for those two).

## Dependencies

- None in this repository. The Cloud-Sandbox's `csis-sandbox-provisioning`
  pins this collection (`>=0.0.1,<0.1.0`) and will take the release.

## Out of Scope

- Pinning the keys a mirror publishes to fingerprints (a different feature:
  `key` with `fingerprint` already does that for one key).
- Changing the Cloud-Sandbox's playbooks.
