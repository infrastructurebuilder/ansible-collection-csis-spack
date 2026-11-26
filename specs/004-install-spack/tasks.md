---

description: "Task list for the setup step that installs Spack"
---

# Tasks: A `setup` step that installs Spack

**Input**: Design documents from `/specs/004-install-spack/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/interface.md](contracts/interface.md), [quickstart.md](quickstart.md)

**Tests**: included and written first. The constitution asks for them
(Principle IV), and the spec does too (SC-005).

**Branch**: `feature/install-spack`. Commit locally after each phase;
merging, pushing and releasing are on the operator's word.

**Names** (confirmed 2026-11-26): the kind `spack`, the module
`spack_checkout`, the options `version`, `path`, `source`,
`version_added: 0.0.4`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an
  unfinished task)
- **[Story]**: the user story the task belongs to (US1, US2, US3)
- Every check runs through the `Justfile` (`just test`, `just integration`,
  `just full-test`), never the tool under it. Wrap a long run in
  `/usr/local/bin/timeout`.

---

## Phase 1: Setup

- [X] T001 On `feature/install-spack`, run `just test` at the repository root and see it pass, so that later failures are the new tests'
- [X] T002 In `Justfile`, let `integration` take pytest's arguments (`integration *args:` passing `{{ args }}` after `tests/integration`), so that one integration test can be seen to fail without the 35-minute run (`just integration -k checkout`); `full-test` keeps calling it with none. Say so in the target's comment, and run `just integration --collect-only -q` to see the arguments reach pytest

---

## Phase 2: Foundational — sources to install from, and the list's rules

**Purpose**: every story needs a git repository to install from in the unit
tests, and the role needs the new kind and its rules before any step of it
can run. Nothing in Phase 3 starts before this phase passes.

- [X] T003 [P] Create `tests/unit/spack_source.py`: a function `make_source(directory, *, runs=None)` that makes a git repository (real `git`, run as argument lists) with, in this order, commits tagged `v0.23.0`, `v1.0.0` and `v1.2.0`, and a branch `releases/v1.2` from `v1.2.0` with one more commit; at each commit an executable `bin/spack` that, given `--version`, prints `<version> (<40 hex digits>)` as research.md R5 shows (`0.23.0`, `1.0.0`, `1.2.0`, and `1.2.1.dev0` on the branch) and exits 0; with `runs` (a path to the stand-in `spack`), `bin/spack` instead execs `runs` with its arguments, so that a role test's later steps run the stand-in. It returns the repository's `file://` address and a mapping of each tag and branch to its commit's full hash
- [X] T004 [P] Write the filter's tests in `tests/unit/test_setup_filter.py` (data-model.md "The step" and "Where the step may be"): a `spack` step with `version` and `path` has no problem; `version` and `path` are each "required"; `source`, `label` and `environment` are allowed; `yes_to_all`, `scope` and another kind's option are "not an option of this kind"; a `spack` step as step 2 is a problem, and so is a second `spack` step; a relative `path` is a problem; a `spack` step whose `environment` is a name is a problem (no earlier step can capture it), and one whose `environment` is a mapping is not; `setup_problems(steps, "spack")` and `setup_problems(steps, "/opt/spack/bin/spack")` with `path: /opt/spack` (and with `path: /opt/spack/`) have none, `setup_problems(steps, "/usr/bin/spack")` has one naming both; `setup_problems(steps)` with no second argument behaves as today for every existing list. `setup_executable([spack step at /opt/spack, ...], "spack")` is `/opt/spack/bin/spack`; with no `spack` step it is the executable given, unchanged. `setup_label` of a `spack` step is `spack: v1.2.0 at /opt/spack`
- [X] T005 Run `just test` and see T004's tests fail because `spack` is not a kind (the rest pass)
- [X] T006 In `plugins/filter/setup_problems.py`: add `KINDS["spack"]` (`module: spack_checkout`, required `version`, `path`, optional `source`), allowed `label` and `environment`; add the three rules of data-model.md "Where the step may be" to `setup_problems(steps, executable=None)`, comparing `os.path.normpath`ed paths; add `setup_executable(steps, executable)` and register it in `FilterModule.filters()`; label the kind; update the `DOCUMENTATION` of `setup_problems` (the new argument); create `plugins/filter/setup_executable.yml` with `DOCUMENTATION`, `EXAMPLES` and `RETURN`, in the form of `plugins/filter/setup_label.yml`
- [X] T007 Run `just test`: T004's tests pass and nothing else changed. Commit

**Checkpoint**: lists with a `spack` step are checked; nothing runs one yet.

---

## Phase 3: User Story 1 — A node with no Spack gets one from the role (Priority: P1) 🎯 MVP

**Goal**: `spack_checkout` installs the version named at a path that is
absent or empty, and leaves it alone the second time; the role's later
steps run it; check mode changes nothing (FR-001 to FR-006, FR-008,
FR-009, FR-011).

**Independent Test**: on a node with no Spack, an install step and a
`config` step: the Spack is at the path, reports the version, and the
`config` step's setting is held by it; a second run reports no change.

### Tests for User Story 1 (written first; they must fail)

- [X] T008 [P] [US1] Write `tests/unit/test_spack_checkout.py`, running the module through `spack.module("spack_checkout", ...)` as the other module tests do, against `make_source` (T003) in the test's directory: by tag `v1.2.0` into a path that does not exist, `changed` true, `found: nothing`, `spack_version` starting `1.2.0`, `spack` is `<path>/bin/spack`, HEAD is the tag's commit, and `git -C <path> status --porcelain` is empty; then the same again, `changed` false; by branch `releases/v1.2`, HEAD is that branch (`symbolic-ref --short HEAD`), then no change; by the branch's full hash, then no change; into a path whose parent does not exist, the parent made; into an empty directory made with mode 0o750, installed with the mode still 0o750 and `found: empty`; the same in check mode, `changed` true and the directory still empty afterwards; in check mode into a path that does not exist, `changed` true and nothing at the path or beside it (the parent holds no new entry); in check mode over a Spack already at the version, `changed` false and no `git` command run but those that read (`rev-parse`, `symbolic-ref`); with a stale hidden directory `.<name>.install-old` beside the path (as a killed run leaves), an install still succeeds and leaves that directory alone; a version not in the source (`v9.9.9`) fails with git's message and leaves nothing at the path and no hidden directory beside it; `version: 63962ed9` (and any hexadecimal string of 7 to 39 digits) fails with "give the commit's full hash" and no `git` command run; `v0.23.0` fails saying the version is below 1.0 and leaves nothing at the path; a `source` that does not exist fails and leaves nothing; with `PATH` holding no `git`, fails naming `git`; a relative `path` fails; a `path` that is a symbolic link to a directory that does not exist gets the install where it points, and one to an empty directory installs into that directory; a `source` of `https://user:secret@host/spack.git` or `https://token@host/spack.git` fails before any `git` command, and `secret` and `token` appear nowhere in the result; a `git` wrapper that reports `git version 2.17.1` makes the step fail naming 2.17.1 and 2.18; a parent the user cannot write to (mode 0o555) fails with nothing made; `version: deadbeef` is refused as a short hash. Assert, by a `git` wrapper on `PATH` that records its arguments, that every `git` call was an argument list and none went through `sh -c`
- [X] T009 [P] [US1] In `tests/unit/test_setup_role.py`, with a source from `make_source(..., runs=<the stand-in>)` whose `bin/spack` also touches a mark file (as `elsewhere()` does today): a list `[spack step at <tmp>/spack, config step]` applies, the `spack` step and the `config` step both report a change, the mark is there (the `config` step ran `<tmp>/spack/bin/spack`), and the stand-in holds the setting; a second application reports no change for either; in check mode on a new path, the `spack` step reports a change, the `config` step's result has `changed: false`, `previewed: false` and the reason of contracts/interface.md "Results recorded by the role", nothing is at the path, and the role succeeds; with `spack_setup_executable: /usr/bin/spack` and a `spack` step, the role fails before any step, naming both, with nothing made; a list with no `spack` step runs `spack_setup_executable` as before (the existing tests stay as they are)
- [X] T010 [P] [US1] In `tests/integration/test_real_spack.py`, in tests whose names contain `checkout`, for each Spack version the module fixture gives (1.0.0, 1.1.0, 1.2.0): `spack_checkout` with `source` the `file://` address of that version's local clone in `.tmp/`, `version` its tag, `path` a new directory under the test's `tmp_path`: a change, `spack_version` starting with the version, `<path>/bin/spack --version` the same; then no change
- [X] T011 [P] [US1] In `tests/integration/test_real_setup.py`, in a test whose name contains `spack_step`: a `spack` step installing the pinned version from its local clone into `tmp_path`, then a `config` step in the user scope; the setting is read back with the installed Spack's `config get`; a second application reports no change
- [X] T012 [US1] Run `just test` and see T008's and T009's tests fail (no module `spack_checkout`; `kinds/spack.yml` missing), the rest pass; run `/usr/local/bin/timeout 1200 just integration -k "checkout or spack_step"` (the names T010 and T011 use) and see them fail the same way

### Implementation for User Story 1

- [X] T013 [US1] Create `plugins/modules/spack_checkout.py` as plan.md "The module" and data-model.md "The states of the path" say, for the states `nothing`, `empty` and `spack` at the version; any other state fails with nothing changed and says what was found (US2 refines the messages). Before anything else: refuse an `http(s)` `source` holding a user name or password (FR-003), and require `git --version` 2.18 or later (spec Edge Cases); follow a symbolic link at `path` (`os.path.realpath`) and judge what it points to; make every missing parent with `os.makedirs` (the user's umask). Options: `version` (str, required; "A tag or a branch of the source, or a commit's full 40-digit hash. Any 7 to 39 hexadecimal digits are taken for a short hash and refused, a tag or branch so named too"), `path` (path, required, absolute), `source` (str, default `https://github.com/spack/spack.git`); `supports_check_mode=True`. `git` from `get_bin_path("git", required=True)`; the commands of contracts/interface.md "What is run on the node", each an argument list to `run_command`; the install beside the path in `tempfile.mkdtemp(dir=<parent>, prefix=".<name>.install-")`, removed if anything fails, renamed into place after the version check; the version check runs `<target>/bin/spack --version` and requires its first word's major.minor to be 1.0 or later. Returns as data-model.md "What the module returns". `DOCUMENTATION` (version_added 0.0.4, what each state does, that the node needs `git`, that the recipes are left to Spack and a site without the network sets its own recipe repository with a `config` step, that a Spack at another version fails the step, and that a run killed during an install can leave a hidden directory `.<name>.install-*` beside the path, which a later run ignores and a site may delete; that `source` may be any address `git` accepts, is trusted as given, and must not hold a credential (use a credential helper or an SSH key); that two plays installing to one path at once are not supported; that a hanging fetch is bounded only by the task's own `timeout` or `async`; that `git` 2.18 or later is needed), `EXAMPLES`, `RETURN` (FR-014's keys, with `source` and `edited`)
- [X] T014 [US1] Create `roles/setup/tasks/kinds/spack.yml`: run `infrastructurebuilder.csis_spack.spack_checkout` with the step's `version`, `path` and `source` (`default(omit)`), `environment: "{{ spack_setup_step_environment }}"`, `register: spack_setup_done`; then set `spack_setup_not_installed` to `ansible_check_mode and spack_setup_done.changed`
- [X] T015 [US1] In `roles/setup/tasks/main.yml`: pass `spack_setup_executable` to `setup_problems`; set `spack_setup_not_installed: false` with the other facts at the start; give the loop `spack_setup_program: "{{ spack_setup | infrastructurebuilder.csis_spack.setup_executable(spack_setup_executable) }}"`. In `roles/setup/tasks/step.yml`: when `spack_setup_not_installed` is true, do not include the kind's tasks, and set `spack_setup_done` to the not-previewed result of contracts/interface.md before the result is recorded (so a step never records the previous step's result)
- [X] T016 [P] [US1] In `roles/setup/tasks/kinds/command.yml`, `config.yml`, `detect.yml`, `gpg_key.yml` and `mirror.yml`, pass `spack: "{{ spack_setup_program }}"` in place of `spack_setup_executable`
- [X] T017 [US1] Run `just test`: T008's and T009's tests pass, and every test written before this spec still passes unchanged. Run `/usr/local/bin/timeout 1200 just integration -k "checkout or spack_step"`: T010's and T011's pass on the three versions. Commit

**Checkpoint**: User Story 1 works alone: the MVP.

---

## Phase 4: User Story 2 — A Spack already there is respected (Priority: P2)

**Goal**: a Spack at the path at the version named is left alone however it
got there; one at another version, or something that is not a Spack, fails
the step with nothing changed (FR-005, FR-007, FR-010).

**Independent Test**: a Spack cloned by hand at a version, named with that
version: no change; named with another: the step fails, the Spack untouched.

### Tests for User Story 2 (written first)

- [X] T018 [P] [US2] In `tests/unit/test_spack_checkout.py`: a clone made by hand with `git clone --depth 1 --branch v1.0.0 <source> <path>`, named with `v1.0.0`, no change, `found: spack`; one made with `--branch releases/v1.2`, named with `releases/v1.2`, no change; a Spack installed by the module at `v1.2.0`, named with `v1.0.0`: fails, the message names `v1.2.0` (HEAD's tag) and the `spack --version` it printed, and the version asked for; HEAD, `git status --porcelain` and the list of files are as before; the same in check mode; a path holding a file and no `.git`: fails "not a Spack", nothing changed; a git repository with no `bin/spack`: fails the same; a directory inside another git repository (`<repo>/sub`, not empty): fails, nothing changed (an empty one is an empty directory, which FR-004 installs into; found while implementing); a path that is a file, not a directory: fails, nothing changed; each of these not-a-Spack cases again in check mode, the same failure and nothing changed; a Spack at the version named with one of its tracked files edited: no change, `changed` false, a warning naming that file, and `edited` listing it in the result
- [X] T019 [P] [US2] In `tests/unit/test_setup_role.py`: a `spack` step naming another version than the one at its path fails the role at that step, and the `config` step after it is not run (the stand-in records no call)
- [X] T020 [P] [US2] In `tests/integration/test_real_spack.py`, for each version: the local clone in `.tmp/` itself as `path`, with its tag as `version`, no change (and it is not modified: `git status --porcelain` empty); the same clone named with another of the three tags, a failure naming both, nothing changed
- [X] T021 [US2] Run `just test` and `/usr/local/bin/timeout 1200 just integration -k checkout`; note which of T018–T020 fail against T013's module (the messages, at least)

### Implementation for User Story 2

- [X] T022 [US2] In `plugins/modules/spack_checkout.py`, warn when a Spack at the version named has edited files (`git -C <path> status --porcelain --untracked-files=no`; `module.warn` naming them; `edited` in the result, empty otherwise), changing nothing; and give each state of data-model.md its own failure message: another version (the tag, branch or commit HEAD is at, what `spack --version` printed, and the version named; and that moving it is not done by this module); not a Spack (what was found: a file, a directory with no `.git`, a repository with no `bin/spack`, a directory inside the repository at `<toplevel>`), with "nothing was changed"; never anything that writes to the path in these states, in check mode or not
- [X] T023 [US2] Run `just test` and `/usr/local/bin/timeout 1200 just integration -k checkout`: T018–T020 pass. Commit

**Checkpoint**: User Stories 1 and 2 both work.

---

## Phase 5: User Story 3 — A site whose nodes cannot reach the internet (Priority: P3)

**Goal**: Spack is installed from the source the step names; with none, from
Spack's public repository (FR-003).

**Independent Test**: an install naming a local source fetches only from it.

- [X] T024 [P] [US3] In `tests/unit/test_spack_checkout.py`: with `source` a local repository, `git -C <path> remote get-url origin` is that source, for a tag, a branch and a full hash; with `source` left out, in check mode (so nothing is fetched), the result names `https://github.com/spack/spack.git` as the source it would use; with `HTTPS_PROXY` given through the role step's `environment`, the recording `git` wrapper (T008) saw it in its environment
- [X] T025 [US3] Run `just test`; if T024 fails, return the source in the module's result (`source`, in `RETURN`) and make the full-hash install add `origin` (contracts/interface.md) in `plugins/modules/spack_checkout.py`, until it passes. Commit

**Checkpoint**: all three stories work.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T026 [P] Create `docs/examples/spack-installed-by-the-role.yml`: `spack_setup` with a `spack` step (`version: v1.2.0`, `path: /opt/spack`), a `config` step and a `mirror` step, with comments saying that no `spack_setup_executable` is needed and that `source` names a site's own mirror of Spack's repository. In `tests/unit/test_examples.py`, carry out an example's `spack` step with `source` replaced by a `make_source(..., runs=<the stand-in>)` repository and `path` by one under `tmp_path`, since the unit tests have no network; every other example is carried out as today
- [X] T027 [P] In `roles/setup/README.md`: a row for `spack` in the kinds table (`spack_checkout`; "Installs Spack at a path at a version, by a shallow git clone; leaves a Spack already there at that version alone"; `version` and `path` (required), `source`); a section "Installing Spack: the `spack` step": only as the first step, so its `environment` is a mapping, not a captured name; a commit is given by its full hash; `spack_setup_executable` set to anything but `spack` or `<path>/bin/spack`, including through its old name `spack_setup_spack`, makes the list refused; a Spack at the version with edited files is left alone with a warning; the later steps run `<path>/bin/spack`, and `spack_setup_executable` is then not needed (set otherwise, the list is refused); a Spack at another version fails the step (and that moving it is not done); the node needs `git`; Spack's package recipes are fetched by Spack on first need, and a site without the network sets its own recipe repository with a `config` step; check mode on a new node: the later steps are not previewed, and why
- [X] T028 [P] In `README.md`: Requirements say Spack 1.0 or later is needed on the node unless the list starts with a `spack` step, which needs `git` 2.18 or later; the module table gets `spack_checkout`; "What it holds" says the role can install Spack (FR-013)
- [X] T029 [P] In `CHANGELOG.md`, an Unreleased section: the `spack` kind and `spack_checkout` (what each does, that a Spack at another version fails, that the recipes are left to Spack), `setup_problems`'s new argument and `setup_executable`, and that a list without a `spack` step behaves as before
- [X] T030 Run `just test`
- [ ] T031 Run `/usr/local/bin/timeout 4200 just full-test` (about 55 minutes: the integration tests on three versions, `ansible-test sanity`, which runs validate-modules on the new module, and Galaxy's import checks); fix what it finds and run it again until it passes
- [X] T032 Check every scenario of [quickstart.md](quickstart.md) section 3 is held by a test named in T008–T024, and every FR-001–FR-013 and SC-001–SC-006 of [spec.md](spec.md) by a task above; add a test for any that is not
- [ ] T033 Set the Status line of `specs/004-install-spack/spec.md` (done, the date, `just test` and `just full-test` passing, not released), and the row of spec 004 in `specs/README.md` (State, Tasks: 33). Commit

---

## Dependencies & Execution Order

- **Phase 1** first. T002 before T012.
- **Phase 2** (T003–T007) before every story: T003 is the source every unit
  test installs from; T006 is the kind the role runs.
- **US1** (T008–T017) before US2 and US3: their tests use the module US1
  creates. Within US1: T008–T011 together, then T012, then T013, then
  T014–T016 (T016 in parallel with T014 and T015), then T017.
- **US2** (T018–T023) and **US3** (T024–T025) touch the same test file and
  module, so run them one after the other, US2 first.
- **Polish** (T026–T029 in parallel), then T030, T031, T032, T033.

## Parallel Example: User Story 1

```text
T008 tests/unit/test_spack_checkout.py
T009 tests/unit/test_setup_role.py
T010 tests/integration/test_real_spack.py
T011 tests/integration/test_real_setup.py
```

## Implementation Strategy

- **MVP**: Phases 1–3. A node with no Spack gets one, the later steps run
  it, repeat runs change nothing. A Spack already at the path at another
  version already fails safely there (T013), with a plainer message.
- **Then** US2 (clear refusals over what is there) and US3 (a site's own
  source), each committed when its tests pass.
- **Done** when T031 passes and T033 is committed; merging into `develop`
  waits for the operator's word, then `/speckit-converge`.
