---

description: "Task list for moving a Spack to another version, when a site asks"
---

# Tasks: The install step moves a Spack to another version, when a site asks

**Input**: Design documents from `/specs/005-move-spack-version/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/interface.md](contracts/interface.md), [quickstart.md](quickstart.md)

**Tests**: included and written first. The constitution asks for them
(Principle IV), and the spec does too (SC-004, SC-005, SC-006).

**Branch**: `feature/move-spack-version` (spec 004 merged into it). Commit
locally after each phase; merging, pushing and releasing are on the
operator's word.

**Names** (confirmed 2026-11-26): the option `move` (bool, default `false`)
on `spack_checkout` and on the `spack` step, `version_added: 0.0.4`, the
result key `moved_from`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an
  unfinished task)
- **[Story]**: the user story the task belongs to (US1, US2)
- Every check runs through the `Justfile` (`just unit`, `just integration`,
  `just test`, `just full-test`), never the tool under it. Wrap a long run in
  `/usr/local/bin/timeout`.

---

## Phase 1: Setup

- [X] T001 On `feature/move-spack-version`, run `just test` at the repository root and see it pass (326 tests after spec 004), so that later failures are the new tests'

---

## Phase 2: Foundational — sources with a site's place in them, and the option

**Purpose**: both stories install from `tests/unit/spack_source.py`'s
repositories, which must hold what research R2 found (a file one version
tracks where an earlier one leaves room for the site's), and both need
`move` to be an option the role and the module accept.

- [X] T002 In `tests/unit/spack_source.py`, give every commit a tracked `.gitignore` of `/opt` and `/etc/site/*`; at `v1.2.0` and on the branch `releases/v1.2`, also track `etc/site/README.md` ("Spack's own site README"), un-ignored by `!/etc/site/README.md` in that version's `.gitignore`, as Spack 1.2 does with `etc/spack/site/README.md` (research R2). Say so in the module docstring. Spec 004's tests must still pass unchanged: run `just unit tests/unit/test_spack_checkout.py tests/unit/test_setup_role.py tests/unit/test_examples.py`
- [X] T003 [P] In `tests/unit/test_setup_filter.py`, a test that `move` is an option of the `spack` kind (`setup_problems([{"kind": "spack", "version": "v1.2.0", "path": "/opt/spack", "move": True}]) == []`); run `just unit tests/unit/test_setup_filter.py` and see it fail, and the existing test that each kind's options are its module's options still pass
- [X] T004 In `plugins/filter/setup_problems.py`, add `move` to `KINDS["spack"]["optional"]`. In `plugins/modules/spack_checkout.py`, add the option `move` (`type="bool"`, `default=False`) to the argument spec and to `DOCUMENTATION` (`version_added: 0.0.4`; "Only changes what happens when the path holds a Spack at another version"; the rest of its documentation is T019), with no behaviour yet. Run `just unit tests/unit/test_setup_filter.py`: T003 passes, and so does the options test. Commit

**Checkpoint**: `move` is accepted and does nothing yet.

---

## Phase 3: User Story 1 — A site moves its nodes to a new Spack by changing one value (Priority: P1) 🎯 MVP

**Goal**: with `move: true`, a Spack at another version is moved to the
version named in place, forward or back, to a tag, a branch or a commit;
a repeat run changes nothing; without the option, spec 004's failure; check
mode reports the move and changes nothing (FR-001–FR-004, FR-007–FR-009).

**Independent Test**: install `v1.0.0`, run again naming `v1.2.0` with
`move: true`: changed, `moved_from` names `v1.0.0`, `spack --version` 1.2.0;
once more: no change.

### Tests for User Story 1 (written first; they must fail)

- [X] T005 [P] [US1] In `tests/unit/test_spack_checkout.py`, a section for spec 005 (test names containing `move`), against `make_source` (T002): from `v1.0.0` to `v1.2.0` with `move: true`: `changed` true, `found: spack`, `moved_from` naming `tag v1.0.0` and `1.0.0 (`, `spack_version` starting `1.2.0`, HEAD the tag's commit, `git status --porcelain` empty, no `.spack.move-*` beside the path; then again, `changed` false and no `moved_from`; back from `v1.2.0` to `v1.0.0`, the same; to the branch `releases/v1.2`, HEAD on that branch (`symbolic-ref --short HEAD`), then no change; to `v1.0.0`'s full hash, HEAD that commit, then no change; from a Spack installed from one source to a version fetched from a second source made by `make_source` in another directory: moved, and `git remote get-url origin` the second source (FR-003); without `move`, spec 004's failure ("was asked for", "Nothing was changed"); with `move: true`, a version not in the source (`v9.9.9`): fails with git's "not found", HEAD, the tags and the files as before, no `.spack.move-*` left; `v0.23.0`: fails saying below 1.0, the Spack there unchanged; in check mode, `move: true`, from `v1.0.0` to `v1.2.0`: `changed` true, `moved_from` set, the message saying that whether the version exists and whether a site's file would be overwritten are found only when the move is made, HEAD, `git tag`, `git count-objects -v`'s `count` and `in-pack`, and the files as before, and (with the recording `Git` wrapper) no `git` subcommand outside `--version`, `rev-parse`, `symbolic-ref`, `status`, `tag`; in check mode, `move: true`, over a Spack already at the version: no change, and only those reads (SC-005); `move: true` over a directory that is not a git repository: spec 004's "it is not a Spack" failure, nothing changed (the edge case of a Spack not installed from git); a move with a stale hidden `.spack.move-old` beside the path, as a killed move leaves: the move succeeds and leaves that directory alone (research R5)
- [X] T006 [P] [US1] In `tests/unit/test_setup_role.py`, with `installed_by_the_role()`'s source: apply `[spack step at v1.0.0, config step]`, then `[spack step at v1.2.0 with move: true, config step with another setting]`: both steps change, the mark shows the `config` step ran `<path>/bin/spack`, and the stand-in holds the new setting; in check mode with `move: true` and another version: the `spack` step changes, the `config` step is recorded `previewed: false` with "Spack is not installed or moved yet: check mode does not change it, so this step cannot be previewed", and no `config` call is made. Update `NOT_PREVIEWED` in that file to the new message
- [X] T007 [P] [US1] In `tests/integration/test_real_spack.py`, one test whose name contains `move` (not parametrized by version: it uses all three clones): install `v1.0.0` from `spack_root("v1.0.0")` into `tmp_path`; with `move: true`, move it to `v1.1.0` from `spack_root("v1.1.0")`, then to `v1.2.0` from `spack_root()`, then back to `v1.0.0`: each a change, `moved_from` the version before, `<path>/bin/spack --version` the version moved to; each repeated: no change. Use the environment of `real_spack_env()`
- [X] T008 [US1] Run `just unit -k move` and see T005's and T006's tests fail (no move: spec 004's failure instead, or the old message); run `/usr/local/bin/timeout 1200 just integration -k move` and see T007 fail the same way

### Implementation for User Story 1

- [X] T009 [US1] In `plugins/modules/spack_checkout.py`, implement the move of plan.md "The module" steps 2, 3, 5, 6 and 7 (stage beside the path in `tempfile.mkdtemp(dir=<parent>, prefix=".<name>.move-")` with `clone()`; check the staged `bin/spack --version` with `Installer.check()`; fetch from `file://<stage>` into the path with `--depth 1` and the refspec for a tag, a branch or a commit as contracts/interface.md says; check out; `git remote set-url origin <source>`; check `<path>/bin/spack --version`; remove the stage in every case), taken only when `move` is true and the Spack there is at another version. Tell a branch from a tag by `git -C <stage> symbolic-ref -q HEAD`. Set `moved_from` to "<tag/branch/commit HEAD was at>, spack --version printed <...>" before moving, as 004's `checked_out()` and `Installer.check()` give them. In check mode, report the move as a change with `moved_from` and the message of FR-009, and run only reads. Steps 1 and 4 (the site's files) are US2's: leave a comment where they go
- [X] T010 [US1] In `roles/setup/tasks/kinds/spack.yml`, pass `move: "{{ spack_setup_step.move | default(omit) }}"`. In `roles/setup/tasks/step.yml`, change the not-previewed message to "Spack is not installed or moved yet: check mode does not change it, so this step cannot be previewed" (a check-mode move reports a change, so `spack_setup_not_installed` is already set for it by `kinds/spack.yml`; check that it is). Update the message in `roles/setup/README.md` and in `specs/004-install-spack/contracts/interface.md` "Results recorded by the role", with a line there that spec 005 changed it ("or moved"), so that a later converge of 004 reads the change as 005's; leave 004's `spec.md` as written
- [X] T011 [US1] Run `just unit -k move` and `just unit tests/unit/test_setup_role.py`: T005's and T006's tests pass, and every earlier test still passes. Run `/usr/local/bin/timeout 1200 just integration -k "move or checkout or spack_step"`: T007 passes and spec 004's integration tests still do. Commit

**Checkpoint**: User Story 1 works alone: the MVP. A site's ignored file can still be overwritten (research R2) until US2.

---

## Phase 4: User Story 2 — What a site keeps in its Spack is not lost (Priority: P2)

**Goal**: a move keeps every file the site added, refuses over Spack's own
files the site edited, and refuses when the new version would overwrite a
file the site added, each with nothing changed and the files named
(FR-005, FR-006, FR-010).

**Independent Test**: on a Spack at `v1.0.0` with a site's
`etc/site/README.md`, a move to `v1.2.0` is refused and names it; with it
moved aside, the move is made, and the site's other files are there.

### Tests for User Story 2 (written first; they must fail)

- [ ] T012 [P] [US2] In `tests/unit/test_spack_checkout.py` (names containing `move`): on `v1.0.0`, a site's files `opt/built/package`, `etc/site/packages.yaml` and `notes.txt` (untracked, not ignored): after a move to `v1.2.0`, each there with its content unchanged; Spack's own `README.md` edited on `v1.0.0`: the move refused, the message naming `README.md` and saying nothing was changed, HEAD and the edit as before, and the same in check mode; a site's `etc/site/README.md` ("MY OWN") on `v1.0.0`: the move to `v1.2.0` refused, naming `etc/site/README.md`, the file still "MY OWN", HEAD as before, no `.spack.move-*` left (research R2); a site's untracked `bin/extra` that `v1.2.0` does not have: kept; on `v1.0.0`, a site's file named `etc/site` where `v1.2.0` has the directory `etc/site/` (for its README): the move refused, naming it, the file unchanged
- [ ] T013 [P] [US2] In `tests/integration/test_real_spack.py`, in T007's test: before the first move, add a site's `etc/spack/packages.yaml` and `opt/spack/built/x`; after each move, both there unchanged. And a second test (name containing `move`): on `v1.0.0` from its clone, a site's `etc/spack/site/README.md`; the move to `v1.2.0` refused, naming it, the file unchanged
- [ ] T014 [US2] Run `just unit -k move` and `/usr/local/bin/timeout 1200 just integration -k move`; see the edited-files and the overwrite tests fail (the overwrite one with the site's README replaced: the defect of research R2)

### Implementation for User Story 2

- [ ] T015 [US2] In `plugins/modules/spack_checkout.py`, plan.md "The module" step 1: before staging, `edited_files()` (spec 004's); any refuses the move, naming them, with "Nothing was changed", in check mode too. Step 4: after the staged checks, the files the staged version tracks (`git -C <stage> ls-tree -r --name-only HEAD`) less those the path's current version tracks (`git -C <path> ls-tree -r --name-only HEAD`); for each, refuse if `os.path.lexists(<path>/<file>)`, or if a parent directory of it is a file or link at the path (`os.path.lexists` and not `os.path.isdir`); the refusal names them and says that the site should move them aside and run again, with nothing at the path changed and the stage removed. Do not walk the site's files (`git ls-files --others` would list a whole install tree)
- [ ] T016 [US2] Run `just unit -k move` and `/usr/local/bin/timeout 1200 just integration -k move`: T012 and T013 pass. Commit

**Checkpoint**: both stories work.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T017 [P] In `roles/setup/README.md`: `move` in the kinds table's options for `spack`, and in "Installing Spack: the `spack` step" a paragraph on moving: off by default; with `move: true` a Spack at another version is moved in place, forward or back; what it keeps and what refuses it (edited files; a site's file the new version tracks, named, to be moved aside); that nothing the old version built is rebuilt, and environments may need to be concretized and installed again; that check mode does not find a missing version or an overwrite; that `.git` keeps both versions' objects; and that the steps after a move run the new version (FR-011)
- [ ] T018 [P] In `CHANGELOG.md`'s Unreleased section, `move` on `spack_checkout` and the `spack` step, and the not-previewed message's new wording
- [ ] T019 [P] In `plugins/modules/spack_checkout.py`, the documentation of `move` (FR-011): what a move does and keeps, off by default, the refusals, that it does not rebuild, that check mode does not contact the source, that `origin` becomes the source named, that `.git` keeps both versions' objects, that a move killed part-way can leave a hidden directory `.<name>.move-*` beside the path, which later runs ignore and a site may delete; an `EXAMPLES` entry with `move: true`; `moved_from` in `RETURN` ("returned: when a Spack was moved, or would be in check mode"); and the description's sentence "this module does not move a Spack to another version" changed to say it does so only with `move`
- [ ] T020 Run `just test`
- [ ] T021 Run `/usr/local/bin/timeout 4200 just full-test` (about 55 minutes); fix what it finds and run it again until it passes
- [ ] T022 Check every FR-001–FR-011 and SC-001–SC-006 of [spec.md](spec.md), and the scenarios of [quickstart.md](quickstart.md), against a test named above; add any that is missing, and run `just unit -k move`
- [ ] T023 Set the Status line of `specs/005-move-spack-version/spec.md` (done, the date, `just test` and `just full-test` passing, not released) and spec 005's row of `specs/README.md` (State, Tasks: 23). Commit

---

## Dependencies & Execution Order

- **Phase 1**, then **Phase 2** (T002 before every test that installs; T003
  before T004).
- **US1** (T005–T011) before **US2** (T012–T016): US2's checks sit inside
  US1's move. Within US1: T005–T007 together, T008, T009, T010, T011.
- **Polish**: T017–T019 together, then T020, T021, T022, T023.

## Parallel Example: User Story 1

```text
T005 tests/unit/test_spack_checkout.py
T006 tests/unit/test_setup_role.py
T007 tests/integration/test_real_spack.py
```

## Implementation Strategy

- **MVP**: Phases 1–3: a site moves its Spack by changing the version with
  `move: true`. Until US2, a move can still overwrite a site's ignored file
  that the new version tracks, so the MVP is not one to release alone.
- **Then** US2, which makes a move safe for what a site keeps.
- **Done** when T021 passes and T023 is committed; merging into `develop`
  waits for the operator's word, then `/speckit-converge`.
