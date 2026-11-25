---

description: "Task list for answering Spack's confirmations: the mirrors' keys, and yes_to_all"
---

# Tasks: `spack_gpg_key` trusts the mirrors' keys without a prompt

**Input**: Design documents from `/specs/003-mirror-keys-yes-to-all/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/interface.md](contracts/interface.md), [quickstart.md](quickstart.md)

**Tests**: included and written first. The constitution asks for them
(Principle IV), and the spec does too (FR-003, FR-004, FR-007, SC-002).

**Branch**: `feature/mirror-keys-yes-to-all`. Commit locally after each
phase; merging, pushing and releasing are on the operator's word.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an
  unfinished task)
- **[Story]**: the user story the task belongs to (US1, US2)
- Every check runs through the `Justfile` (`just test`, `just full-test`),
  never the tool under it. Wrap a long run in `/usr/local/bin/timeout`.

---

## Phase 1: Setup

- [X] T001 On `feature/mirror-keys-yes-to-all`, run `just test` at the repository root and see it pass (228 tests at planning), so that later failures are the new tests'

---

## Phase 2: Foundational — the stand-in's help, and the check in the shared code

**Purpose**: both stories rest on `Spack.answered()` and on a stand-in
`spack` that prints help as the real one does. Nothing in Phase 3 or 4
starts before this phase passes.

- [X] T002 [P] Create `tests/unit/fake_spack_help.json`: a mapping from a command's words to its help text, copied from the real Spack 1.2.0 in `.tmp/spack` (`spack <words> --help`, with the environment of `tests/integration/real_spack.py`), for `gpg`, `gpg trust`, `buildcache`, `buildcache keys`, `buildcache push`, `install`, `concretize`, `module`, `module tcl`, `module lmod`, `module tcl refresh`, `module lmod refresh`, `mirror`, `mirror add`, `mirror remove`, `mirror list`, `config`, `compiler`, `compiler find`, `external`, `external find`, `gc`; and a function that gives the text as Spack 1.0 and 1.1 print it for `gpg trust` and `buildcache keys` (the `-y, --yes-to-all` line, and `y` in the usage line, removed; research.md R1)
- [X] T003 In `tests/unit/fake_spack.py`, answer any call that ends in `--help` before anything else: print the text from `tests/unit/fake_spack_help.json` for the words before it, exit 0; for words it has no text for, print `==> Error: <word> is not a recognized Spack command or extension command; check with \`spack commands\`.` and exit 1 (research.md R3). State key `spack_like: "1.1"` selects the 1.0/1.1 texts. Also answer `gc` and `gc -y` / `gc --yes-to-all` (print a line, exit 0), so `spack_command` has a command that takes the option. Document both in the module docstring's state keys
- [X] T004 [P] In `tests/unit/fake_spack_setup.py`, accept `gpg trust <file>`, `gpg trust -y <file>` and `gpg trust --yes-to-all <file>`, and `buildcache keys --install --trust` with or without `--yes-to-all` (it is matched exactly today, line 281); with `spack_like: "1.1"`, `-y` or `--yes-to-all` on either prints `==> Error: unrecognized arguments: -y` (or `--yes-to-all`) and exits 1, as research.md R2 recorded
- [X] T005 Write the tests of `answered()` in `tests/unit/test_module_utils.py`, against the stand-in through a minimal module object whose `run_command` runs `tests/unit/fake_spack.py` and records calls. Each rule of data-model.md "Rules" gets a test: with `yes_to_all=False` and no `consent`, the arguments come back unchanged and no help is read; with the flag, `["install", "--fake"]` and `words=1` give `["install", "--yes-to-all", "--fake"]`; `["mirror", "add", "n", "u"]` and `words=2` come back unchanged after one help call; arguments already holding `-y` or `--yes-to-all` come back unchanged and no help is read; `consent=True` adds the option with the flag off; with `spack_like: "1.1"`, `["gpg", "trust", "f"]` with `consent=True` comes back unchanged; the same words twice read the help once. And the walk (`words=None`): `["module", "tcl", "refresh", "--delete-tree"]` reads `module`, `module tcl`, `module tcl refresh` and inserts after `refresh`; `["config", "--scope", "user", "add", "a:b"]` reads only `config` and comes back unchanged; `["gc"]` gives `["gc", "--yes-to-all"]`; an argument that is not a listed subcommand is never followed by `--help` (`["buildcache", "keys", "mirror1"]` reads `buildcache`, `buildcache keys`, and no help with `mirror1` in it); a first argument that starts with `-`, or empty arguments, read no help; a help that fails counts as "does not take it"
- [X] T006 Run `just test` (`Justfile`) and see T005's tests fail because `answered()` does not exist (and the rest still pass)
- [X] T007 In `plugins/module_utils/spack.py`, implement the design of plan.md "The check": `Spack(module, executable, yes_to_all=False)`; a help cache per object (words → takes, subcommands; data-model.md "The help cache"); `answered(args, words=None, consent=False)` following data-model.md "Rules" 1–3; the option line matched as `^\s+-y, --yes-to-all\b`, subcommands read from the indented names (and bracketed aliases, `push (create)`) under `positional arguments:` (research.md R3). Module docstring and comments say why help is never read after an unknown word. `run()` does not change
- [X] T008 Run `just test` (`Justfile`): T005's tests pass, nothing else changed. Commit

**Checkpoint**: the check exists, held by unit tests; no module uses it yet.

---

## Phase 3: User Story 1 — The mirrors' keys are trusted, unattended (Priority: P1) 🎯 MVP

**Goal**: `spack_gpg_key` answers Spack 1.2's trust prompt for `from_mirrors`
and for `key`, and passes nothing Spack 1.0 and 1.1 reject (FR-001, FR-002,
FR-004, FR-005, FR-008).

**Independent Test**: against the real Spack, a mirror that publishes a key:
the step trusts it and reports a change; run again, it reports none (the
integration tests of T010 and T011).

### Tests for User Story 1 (written first; they must fail before T013)

- [X] T009 [P] [US1] In `tests/unit/test_spack_gpg_key.py`, hold the new forms (FR-004): change `test_the_keys_the_mirrors_publish_are_trusted` to expect `["buildcache", "keys", "--install", "--trust", "--yes-to-all"]`; a key file is trusted with `["gpg", "trust", "--yes-to-all", <file>]`; with `spack_like: "1.1"`, both run without the option and succeed (SC-004); with `yes_to_all: false` (the default) both still pass the option (consent); check mode reads no help and runs no trust; a second run reports no change (FR-002, unchanged)
- [X] T010 [P] [US1] In `tests/integration/test_real_spack.py`, add a test of `from_mirrors` (FR-003, plan.md "The integration tests", research.md R4): a signing keyring and a trust keyring made with `tempfile.mkdtemp(prefix="csis-gpg-")` (short paths for gpg's socket; kill each agent with `gpgconf --homedir <dir> --kill gpg-agent` and remove the directory afterwards, as `test_real_setup.py`'s `keyring` fixture does); two keys made with `spack gpg create` in the signing keyring; zlib installed with `--fake`; pushed with `spack_buildcache_push` `key: <A>` to a mirror under `tmp_path`, then `spack buildcache update-index --keys <mirror>`; user and system scopes pointed at directories of the test's (`SPACK_DISABLE_LOCAL_CONFIG` left out for this part, R4 item 6) and the mirror added with `spack_mirror` `scope: user`; `spack_gpg_key` `from_mirrors: true` into the trust keyring: `changed` and `trusted == [A]`; again: not changed; pushed again with `force: true` and `key: <B>`, index again; `trusted == [B]` only
- [X] T011 [P] [US1] In `tests/integration/test_real_setup.py`, add a signed mirror (FR-003, SC-001): before the play, through `subprocess` with the test's environment, a signing keyring and key, an environment of zlib installed with `--fake` into a store under `tmp_path`, pushed signed to the `file://{tmp_path}/mirror` that the `mirror` step already names, and `spack buildcache update-index --keys`; add a `gpg_key` step of `from_mirrors: true` after the `mirror` step; assert it reports a change on the first play and none on the second. Rewrite the module docstring's "Nothing is built or fetched" to say what is now installed and pushed
- [X] T012 [US1] Run `just test` (T009 fails on the command's arguments) and `just full-test` (T010 and T011 fail at the `from_mirrors` step with `Trust key: … [y/N] ==> Error: EOF when reading a line`, exit 3: SC-002). Keep what failed, and how, for T015's commit message

### Implementation for User Story 1

- [X] T013 [US1] In `plugins/modules/spack_gpg_key.py`, run `spack.answered(["gpg", "trust", path], words=2, consent=True)` and `spack.answered(["buildcache", "keys", "--install", "--trust"], words=2, consent=True)` in place of the two hard-coded commands (the `-y` at line 163 goes). Change reporting stays as it is (FR-002)
- [X] T014 [US1] In `plugins/modules/spack_gpg_key.py` `DOCUMENTATION` (FR-005): `from_mirrors` trusts every key the mirrors publish without asking, with no fingerprint to check them against, and `key` with `fingerprint` is the way to trust one known key; both trusts pass `--yes-to-all` where Spack's help lists it (1.2 and later) and not on 1.0 and 1.1, which do not ask; the help is read once per trust; in check mode neither runs
- [X] T015 [US1] Run `just test`, then `just full-test` (`Justfile`): T009, T010 and T011 pass. Commit tests and fix together, the message saying how the tests failed before the fix
- [X] T016 [US1] Once, by hand, against the real Spack 1.0.0 and 1.1.0 (quickstart.md §3; clones outside the repository, own user scope, cache and throwaway keyring; never Spack's own `etc/spack`): `spack_gpg_key` with `key: tests/fixtures/throwaway-mirror-key.pub` succeeds (a change, then none), and `from_mirrors: true` against a mirror with a published key succeeds. Record what was seen, with the date, as R6 in `specs/003-mirror-keys-yes-to-all/research.md` (SC-004)

**Checkpoint**: User Story 1 is done: the head node's failure is fixed, and
the released `gpg trust -y` defect with it. It can ship alone.

---

## Phase 3b: User Story 3 — The collection works on every Spack it supports (Priority: P2)

Added 2026-11-25 on the operator's word (spec Clarifications, Session
2026-11-25), to be done before Phase 4.

**Goal**: every module works on Spack 1.0, 1.1 and 1.2 (FR-009 to FR-011).

**Independent Test**: `just integration` passes against the real 1.0.0,
1.1.0 and 1.2.0.

- [X] T039 [US3] In `tests/integration/real_spack.py`, run every integration test once per version in `SPACK_VERSIONS` (`v1.0.0`, `v1.1.0`, `v1.2.0`), each cloned once into `.tmp/spack-<version>` (the pin stays in `.tmp/spack`) with a user configuration and cache of its own; the test helpers find `spack` on the environment's `PATH`, and read the signing keys from gpg's own listing (FR-010)
- [X] T040 [US3] Run `just integration` (`Justfile`) before any fix, and record each failure on 1.0.0 and 1.1.0 (research.md R8)
- [X] T041 [US3] In `plugins/module_utils/spack.py`, the table `BEHAVIOUR` by (major, minor) and `behaviour()`, a newer Spack read as the last row; `Spack.does()`, `Spack.trusting()` (replacing the help check for the two trusts), `Spack.config_section()` (`config get --json`, or `spack python -c` on 1.0), `Spack.trusted_keys()` (`--fmt colons`, or gpg's own listing on 1.0 and 1.1), and `Configuration.get` reading a missing scope as empty in 1.1's words too (FR-009); `spack_gpg_key` uses them
- [X] T042 [US3] The stand-in plays 1.0 and 1.1 by its `version` (`tests/unit/fake_spack.py`, `tests/unit/fake_spack_setup.py`), and unit tests hold the table, each fallback and `spack_gpg_key` on each version (`tests/unit/test_module_utils.py`, `tests/unit/test_spack_gpg_key.py`) (FR-011)
- [X] T043 [US3] Run `just integration` (`Justfile`) again; for each failure left on 1.0.0 or 1.1.0, record it in research.md R8, add the row or fallback to `plugins/module_utils/spack.py` with a unit test, and repeat until it passes on all three
- [X] T044 [US3] Run `just test`, then `just full-test` (`Justfile`). Commit

## Phase 4: User Story 2 — The tests would have caught it; `yes_to_all` (Priority: P3)

**Goal**: every module that runs Spack takes `yes_to_all`, and the `setup`
role takes `spack_setup_yes_to_all` with a per-step override (FR-007); the
help check is shown against the real Spack.

**Independent Test**: with `yes_to_all: true`, `spack_command` runs `gc` as
`gc --yes-to-all`; with it off, every module runs exactly what 0.0.2 ran and
reads no help.

### Tests for User Story 2 (written first; they must fail before T024)

- [X] T017 [P] [US2] In `tests/unit/test_spack_command.py`: `yes_to_all: true` with `args: [gc]` runs `["gc", "--yes-to-all"]`; with it off runs `["gc"]` and reads no help; `args: [gc, -y]` is run as written; `args: [mirror, list]` with the flag on runs as written after reading `mirror`, `mirror list`; in check mode nothing runs and no help is read
- [X] T018 [P] [US2] In `tests/unit/test_spack_env.py`: with `yes_to_all: true`, `install` is run with `--yes-to-all` straight after `install` and before `install_args`, `concretize` is run as written, and `module tcl refresh` keeps its single `-y`; with it off, the calls are exactly those of today and include no `--help`
- [X] T019 [P] [US2] In `tests/unit/test_spack_buildcache_push.py`, `tests/unit/test_spack_mirror.py`, `tests/unit/test_spack_config.py` and `tests/unit/test_spack_detect.py`: with `yes_to_all: true`, the help of each command that changes something is read and nothing is added (none takes it in 1.2.0, research.md R1); with it off, no help is read and the calls are those of today
- [X] T020 [P] [US2] In `tests/unit/test_setup_filter.py`: `yes_to_all` is accepted on steps of kind `config`, `mirror`, `gpg_key`, `detect` and `command`, and refused on `environment` as "not an option of this kind" (`test_each_kinds_options_are_its_modules_options` must keep passing)
- [X] T021 [P] [US2] In `tests/unit/test_setup_role.py`: the defaults hold `spack_setup_yes_to_all: false`; with `spack_setup_yes_to_all: true`, a `command` step `args: [gc]` runs `gc --yes-to-all`; a step's `yes_to_all: false` overrides the role's `true`; a step's `true` with the role's default runs `gc --yes-to-all`
- [X] T022 [P] [US2] In `tests/integration/test_real_spack.py`, add a test of the help check against the real Spack 1.2.0, through `plugins/module_utils/spack.py` with a minimal module object that runs the real `spack`: `answered(["gpg", "trust", "f"], words=2, consent=True)` adds the option; `answered(["mirror", "add", "n", "u"], words=2, consent=True)` does not; with `yes_to_all=True`, `answered(["module", "tcl", "refresh"])` walks to `refresh` and adds it; `answered(["config", "--scope", "user", "add", "a:b"])` reads only `config` and adds nothing (FR-007)
- [X] T023 [US2] Run `just test` (`Justfile`) and see T017–T021 fail because the option and the variable do not exist; run the integration test of T022 through `just full-test` and see it pass already (it tests T007's code against the real Spack)

### Implementation for User Story 2

- [X] T024 [P] [US2] In `plugins/modules/spack_command.py`: option `yes_to_all` (`dict(type="bool", default=False)`), documented as contracts/interface.md gives it, including the note on the leading words; `Spack(module, params["spack"], yes_to_all=params["yes_to_all"])`; the site's `args` run through `spack.answered(params["args"])` (words walked)
- [X] T025 [P] [US2] In `plugins/modules/spack_env.py`: option and documentation as in T024; `concretize` (words 1), `install` (words 1) and `module <system> refresh` (words 3) through `answered()`
- [X] T026 [P] [US2] In `plugins/modules/spack_buildcache_push.py`, `plugins/modules/spack_mirror.py` and `plugins/modules/spack_detect.py`: option and documentation as in T024; `buildcache push` (words 2), `mirror add` and `mirror remove` (words 2), `compiler find` and `external find` (words 2) through `answered()`
- [X] T027 [US2] In `plugins/modules/spack_config.py` and the `Configuration` class of `plugins/module_utils/spack.py`: option and documentation as in T024; `Configuration.add` and `Configuration.remove` through `answered(..., words=1)`, since `config` takes `--scope` before its subcommand and `config`'s help decides (research.md R5); a comment says so
- [X] T028 [US2] In `plugins/modules/spack_gpg_key.py`: option `yes_to_all`, documented with the contract's note that it changes nothing in this module, and passed to `Spack(...)`
- [X] T029 [US2] In the role: `spack_setup_yes_to_all: false` in `roles/setup/defaults/main.yml`, with a comment; `yes_to_all: "{{ spack_setup_step.yes_to_all | default(spack_setup_yes_to_all) }}"` in `roles/setup/tasks/kinds/command.yml`, `config.yml`, `detect.yml`, `gpg_key.yml` and `mirror.yml`; `yes_to_all` added to the `optional` list of those five kinds in `plugins/filter/setup_problems.py`
- [X] T030 [US2] In `roles/setup/README.md`: the variable in the Variables table, `yes_to_all` in the list of what any Spack step may have, and the warning of FR-007 (it answers "yes" to every confirmation of a command that takes it, including ones that remove or overwrite; without it such a prompt fails the task, as Ansible gives Spack no terminal); say that `gpg_key` steps answer the trust prompt in any case
- [X] T031 [US2] Run `just test`, then `just full-test` (`Justfile`): T017–T022 pass. Commit

**Checkpoint**: both stories work; with `yes_to_all` off, every module runs
what 0.0.2 ran, apart from `spack_gpg_key`'s two trusts.

---

## Phase 5: Polish, documentation and acceptance

- [X] T032 [P] In `CHANGELOG.md`, under a new `## Unreleased` heading (to become 0.0.3, FR-006): the fix of `from_mirrors` on Spack 1.2 (the head node's `Trust key … EOF` failure, quoted); the fix of `key` on Spack 1.0 and 1.1 (`unrecognized arguments: -y`, a defect of 0.0.1 and 0.0.2); the new `yes_to_all` option of the seven modules and `spack_setup_yes_to_all`, off by default, with its warning; a playbook written for 0.0.2 runs unchanged
- [X] T033 [P] In `README.md`, where it describes the modules (the table at line 63 and any list of common options), mention `yes_to_all` and point to the role README; leave `docs/examples/` as they are (`cloud-sandbox.yml`'s `from_mirrors` steps now work as written) unless `tests/unit/test_examples.py` asks otherwise
- [X] T034 Run `/speckit-analyze` for spec 003 and settle anything it finds between `spec.md`, `plan.md` and this file
- [X] T035 Run `just test` (`Justfile`)
- [X] T036 Run `just full-test` (`Justfile`)
- [X] T037 Tick this file's tasks, and set the Status line of `specs/003-mirror-keys-yes-to-all/spec.md` to done, with the date. Commit
- [ ] T038 **Only on the operator's word, asked first:** finish the feature with `git flow feature finish mirror-keys-yes-to-all --squash --keep` (push only when told), check `git diff develop feature/mirror-keys-yes-to-all` is empty; then, on a separate word, release 0.0.3 as the collection's release procedure says. Say before any tag is pushed that pushing it publishes to Ansible Galaxy (Principle V)

---

## Dependencies & Execution Order

- **Phase 1** before everything.
- **Phase 2**: T002 and T004 in parallel; T003 after T002; T005 after T003
  and T004; then T006, T007, T008 in order. Blocks Phases 3 and 4.
- **Phase 3 (US1)**: T009, T010, T011 in parallel; T012 after all three;
  T013 after T012; T014 after T013; T015; T016 after T015.
- **Phase 3b (US3)**: after Phase 3 and before Phase 4, on the operator's
  word; T039 and T040 before T041 and T042; T043 repeats until the tests
  pass on every version; T044 last.
- **Phase 4 (US2)**: can start after Phase 2, alongside Phase 3, except that
  T028 and T013 both change `plugins/modules/spack_gpg_key.py` (do T013
  first), and T022 and T010 both change `tests/integration/test_real_spack.py`
  (do them one after the other). T017–T022 in parallel; T023 after them;
  T024, T025, T026 in parallel; T027 after T007 (same file); T028 after T013;
  T029 and T030; T031 last.
- **Phase 5** after Phases 3 and 4: T032 and T033 in parallel; then T034,
  T035, T036, T037 in order; T038 only on the operator's word.

## Parallel examples

```text
# Phase 2
T002 tests/unit/fake_spack_help.json      T004 tests/unit/fake_spack_setup.py

# User Story 1, tests first
T009 tests/unit/test_spack_gpg_key.py
T010 tests/integration/test_real_spack.py
T011 tests/integration/test_real_setup.py

# User Story 2, tests first
T017 test_spack_command.py   T018 test_spack_env.py   T019 four module tests
T020 test_setup_filter.py    T021 test_setup_role.py

# User Story 2, implementation
T024 spack_command.py   T025 spack_env.py   T026 push, mirror, detect
```

## Implementation Strategy

- **MVP**: Phases 1, 2 and 3. That fixes the head node's failure and the
  released 1.0/1.1 defect, and is enough for the Cloud-Sandbox to go back to
  `from_mirrors`. The `yes_to_all` option and variable stay unset everywhere,
  so nothing else changes.
- **Then** Phase 4 adds `yes_to_all`, which changes nothing unless a site
  turns it on.
- Both go out together in 0.0.3 (FR-006); Phase 5 before the release.

## Notes from implementation

- **T002**: the help texts are data, `tests/unit/fake_spack_help.json`,
  captured from the real 1.2.0 and 1.1.0 (1.0.0 printed the same as 1.1.0
  for `gpg trust` and `buildcache keys`); as Python their long lines would
  have broken the line length.
- **T008**: `just test` was not green at this checkpoint, and could not be:
  the stand-in now asks before trusting a key, as Spack 1.2 does, so six
  existing tests of `from_mirrors` failed with the head node's error until
  T013. Phase 2 was committed together with Phase 3.
- **T011**: written as a test of its own in `tests/integration/test_real_setup.py`
  (a `mirror` step and a `gpg_key` step of `from_mirrors: true`, played twice),
  so the existing test's expected changes stay as they were.
- **T012**: `just full-test` runs `just test` first, which the new unit tests
  fail; `just integration` was added to the `Justfile` to see the integration
  tests fail on their own (both failed with `EOF when reading a line`, exit 3).
  `just format` was added too.
- **T028**, and the `gpg_key` part of **T029** (its kind file, the filter, the
  role's default), were done in Phase 3: T009's tests pass `yes_to_all`, and
  the filter's test holds each kind's options to its module's.
- **T016** found that the collection does not work with Spack 1.0 or 1.1 at
  all (research.md, R6). The operator chose to fix it in this spec, as User
  Story 3 (Phase 3b); T016 is met by T043's runs against the real 1.0.0 and
  1.1.0.
- **Phase 3b** replaced the help check for `spack_gpg_key`'s two trusts with
  the version table (operator, 2026-11-25): `answered()` lost its `consent`,
  the trusts read no help, and the stand-in's 1.1 help texts went. So T003's
  and T004's `spack_like` became the stand-in's `version`, and T009's and
  T013's `answered(..., consent=True)` became `trusting()`; the tasks are left
  as they were done.
- **T022**'s test reads `install` (has the option), `mirror add` (has not),
  `module tcl refresh` (walked to) and `config --scope user add` (only
  `config` read), rather than `gpg trust`: it runs on 1.0 and 1.1 too, whose
  `gpg trust` has no option, and the trusts no longer use the help check.

## Phase 6: Convergence

- [X] T045 Add a `yes_to_all: true` example to `EXAMPLES` in `plugins/modules/spack_command.py` (for instance `args: [gc]`, `changes: always`), saying it answers every confirmation `gc` asks, and a `yes_to_all` step to the example in `roles/setup/README.md`; no module's `EXAMPLES` and no example in the role's README shows the new option, per Constitution, Technical Constraints ("Documentation is part of a change: each module's `DOCUMENTATION`, `EXAMPLES` and `RETURN`") (partial)
