---

description: "Task list for the two known limits: the index documented and held, the preview's relative paths rewritten"
---

# Tasks: Two known limits, said where a site reads them, or removed

**Input**: Design documents from `/specs/006-known-limits/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [contracts/interface.md](contracts/interface.md),
[quickstart.md](quickstart.md)

**Tests**: included and written first. The constitution asks for them
(Principle IV), and the spec does too (FR-005, SC-002).

**Branch**: `feature/known-limits`. Commit locally after each phase;
merging, pushing and releasing are on the operator's word.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an
  unfinished task)
- **[Story]**: the user story the task belongs to (US1, US2)
- Every check runs through the `Justfile` (`just unit`, `just integration`,
  `just test`, `just full-test`). Wrap a long run in
  `/usr/local/bin/timeout`.

---

## Phase 1: Setup

- [X] T001 On `feature/known-limits`, run `just test` at the repository root and see it pass (349 tests), so that later failures are the new tests'

---

## Phase 2: Foundational — the stand-in runs a Spack Python script

**Purpose**: User Story 2's rewrite is a `spack python <script> <args>`. The
stand-in `spack` must run such a script, as the real one does, so that the
unit tests see what the script does to the copy.

- [X] T002 Create `tests/unit/stand_in/spack/util/spack_yaml.py` (with empty `__init__.py` files in `tests/unit/stand_in/spack/` and `tests/unit/stand_in/spack/util/`; not under `tests/unit/` itself, so that no package named `spack` is on every test's import path): `load(stream)` and `dump(data, stream)` with PyYAML (`yaml.safe_load`, `yaml.safe_dump(..., sort_keys=False)`), standing in for Spack's own `spack.util.spack_yaml`; a module docstring saying what it stands for and that it is the tests' only, never shipped
- [X] T003 In `tests/unit/fake_spack.py`, answer `python <script> <args...>` (no `-c`): run the script with the stand-in's own Python, `sys.argv` set to `[<script>, <args...>]` and `tests/unit/stand_in/` first on `sys.path` for that script only (so `import spack.util.spack_yaml` finds T002's module), and record the call; at `concretize`, also keep the text of the `-e` directory's `spack.yaml` in the state key `concretized_manifest`; leave `python -c` as it is. Document it in the stand-in's docstring
- [X] T004 Run `just unit tests/unit/test_spack_env.py tests/unit/test_spack_config.py` and see the existing tests still pass. Commit

**Checkpoint**: the stand-in runs a Spack Python script; nothing uses it yet.

---

## Phase 3: User Story 1 — A site that rebuilds a mirror's index knows what each run does (Priority: P1) 🎯 MVP

**Goal**: what Spack does with `--update-index` when nothing is pushed is
said in the documentation and held by a test against the real Spack
(FR-001, FR-002, FR-005). No code changes: Spack already leaves the index
alone (research R1).

**Independent Test**: push an environment twice to a mirror with
`update_index: true`; the second run reports no change and the index is not
rewritten.

- [X] T005 [P] [US1] (This test holds behaviour Spack has already, research R1, so it passes from the start; there is no code to make it pass.) In `tests/integration/test_real_spack.py`, a test whose name contains `index`, per version (the `spack_version` and `spack_env` fixtures): an environment of `zlib` installed with `install_args: [--fake]` into a store under `tmp_path`, pushed with `spack_buildcache_push` (`unsigned: true`, `update_index: true`) to a mirror in a directory under `tmp_path`: the first push reports a change and the mirror has `v3/manifests/index/index.manifest.json`; record that file's modification time and contents; push again: `changed` false, `pushed` empty, and the file's time and contents as before (research R1)
- [X] T006 [P] [US1] In `tests/unit/test_spack_buildcache_push.py`, a test that `update_index`'s documentation (read from the module's `DOCUMENTATION`) says the index is rebuilt only after a push that sent something, and names `spack buildcache update-index` for an index changed by other means; run `just unit tests/unit/test_spack_buildcache_push.py` and see it fail
- [X] T007 [US1] In `plugins/modules/spack_buildcache_push.py`, rewrite `update_index`'s description as contracts/interface.md "Documentation" says; run `just unit tests/unit/test_spack_buildcache_push.py`: T006 passes; run `/usr/local/bin/timeout 1500 just integration -k index`: T005 passes on the three versions. Commit

**Checkpoint**: User Story 1 is said and held.

---

## Phase 4: User Story 2 — A site that previews an environment with files beside it knows what the preview sees (Priority: P2)

**Goal**: in check mode the copy's relative `include:` and `develop:` paths
are rewritten to the originals' absolute paths before it is concretized, so
that the preview reads and records what a real run would (FR-003, FR-004,
FR-005).

**Independent Test**: an environment that includes `../shared.yaml`: its
preview succeeds and, after a real concretize, reports no change.

### Tests for User Story 2 (written first; they must fail)

- [ ] T008 [P] [US2] In `tests/unit/test_spack_env.py`, tests whose names contain `relative`: an environment whose `spack.yaml` has `include: [./extra.yaml, ../shared.yaml, {path: ../opt.yaml, optional: true}, /abs/x.yaml, $env/y.yaml, {git: https://git.example.org/c.git, branch: main, paths: [c.yaml]}]` and `develop: {zlib: {spec: zlib@=1.3.1, path: ../zlib-src}, gmake: {spec: gmake@=4.4.1, path: /abs/gmake}}`, in check mode: the stand-in recorded one `python <script> <copy>/spack.yaml <path>` call before `concretize`; the copy it concretized has (read from the stand-in's state key `concretized_manifest`, which T003 makes it set to the text of the `-e` directory's `spack.yaml` at each `concretize`) `<parent of path>/shared.yaml`, `{path: <parent of path>/opt.yaml, optional: true}`, `<path>/extra.yaml` and `<parent of path>/zlib-src`, and `/abs/x.yaml`, `$env/y.yaml`, the git include and `/abs/gmake` as they were; the real `spack.yaml` is byte-for-byte as before; and an environment whose `spack.yaml` has neither key runs no `python` call
- [ ] T009 [P] [US2] In `tests/integration/test_real_spack.py`, a test whose name contains `relative`, per version: a directory `site/` under `tmp_path` holding `shared.yaml` (`config: {build_jobs: 5}`) and an environment `site/env/` whose `spack.yaml` has `specs: [zlib]`, `view: false`, the store under `tmp_path`, and `include: [../shared.yaml]`; `spack_env` with `state: concretized` in check mode succeeds (before this spec: "Required path (../shared.yaml) does not exist"); then a real run with `state: concretized`; then check mode again: `concretized` false; and an environment with `include: [../missing.yaml]` fails in check mode with Spack's "Required path" message, as a real run does
- [ ] T010 [US2] Run `just unit -k relative` and `/usr/local/bin/timeout 1500 just integration -k relative`, and see T008's and T009's tests fail for the right reason (no rewrite: the copy keeps `../shared.yaml`)

### Implementation for User Story 2

- [ ] T011 [US2] In `plugins/modules/spack_env.py`, the check-mode preview (`preview()` or its equivalent, after `shutil.copytree` and before `concretize`): when the copy's `spack.yaml` text contains `include:` or `develop:`, write `REWRITE` (a module-level string: the script of research.md R4, reading `sys.argv[1]` and `sys.argv[2]`, with `spack.util.spack_yaml`; rewriting a relative `include:` string, a mapping's `path`, and each `develop:` entry's `path` to `os.path.normpath(os.path.join(<real directory>, <path>))`; leaving absolute paths, paths with `$`, and a mapping with no `path` (a git include)) to `<tmp>/rewrite.py` beside the copy, not inside it, and run `spack python <tmp>/rewrite.py <tmp>/env/spack.yaml <path>` through the shared runner as an argument list, without `-e`. A failure of the rewrite fails the task with Spack's message
- [ ] T012 [US2] In `plugins/modules/spack_env.py`'s `DOCUMENTATION`, the check-mode note: paths that `spack.yaml` gives relatively in `include:` and in `develop:` are read where they are, also above the environment's directory, and the preview records the same develop paths a real run would; a develop package's source is not copied (contracts/interface.md "Documentation")
- [ ] T013 [US2] Run `just unit -k relative` and `/usr/local/bin/timeout 1500 just integration -k relative`: T008 and T009 pass on the three versions; run `just unit tests/unit/test_spack_env.py`: every earlier test passes. Commit

**Checkpoint**: both stories work.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T014 [P] In `CHANGELOG.md`, an Unreleased section: `spack_env`'s preview now reads relative `include:` and `develop:` paths where they are (it failed on an include above the environment, and recorded a wrong develop path); `spack_buildcache_push`'s `update_index` documented (Spack rebuilds the index only after a push that sent something)
- [ ] T015 [P] In `specs/008-repeat-runs-say-so/spec.md`, Out of Scope, beside the two limits: a note that spec 006 found the index limit not to be one (research R1 of spec 006) and removed the preview's (FR-006 of spec 006)
- [ ] T016 Run `just test`
- [ ] T017 Run `/usr/local/bin/timeout 4200 just full-test` (about 55 minutes); fix what it finds and run it again until it passes
- [ ] T018 Check every FR-001–FR-006 and SC-001–SC-003 of [spec.md](spec.md), and the scenarios of [quickstart.md](quickstart.md), against a test or a task above; add any missing
- [ ] T019 Set the Status line of `specs/006-known-limits/spec.md` (done, the date, `just test` and `just full-test` passing, not merged, not released) and spec 006's row in `specs/README.md` (State, Tasks: 19). Commit

---

## Dependencies & Execution Order

- Phase 1, then Phase 2 (T002 before T003, T003 before T004).
- US1 (T005–T007) needs nothing of Phase 2 and could run first; US2
  (T008–T013) needs Phase 2.
- US1 and US2 touch different modules but the same integration test file:
  write T005 and T009 one after the other.
- Polish: T014 and T015 together, then T016, T017, T018, T019.

## Parallel Example: User Story 2

```text
T008 tests/unit/test_spack_env.py
T009 tests/integration/test_real_spack.py
```

## Implementation Strategy

- **MVP**: Phases 1 and 3 (User Story 1): documentation and a test; no code.
- **Then** Phases 2 and 4 (User Story 2): the rewrite, which is the code.
- **Done** when T017 passes and T019 is committed; merging into `develop`
  waits for the operator's word, then `/speckit-converge`.
