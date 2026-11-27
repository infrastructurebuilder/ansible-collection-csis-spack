# Implementation Plan: Repeat runs that do nothing, and say so

**Branch**: `feature/coll-stage-1`, until the history was reset on 2026-11-18 | **Date**: 2026-11-14 (retrospective, written 2026-11-27) | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/008-repeat-runs-say-so/spec.md`

## Summary

`spack_env` gets `refresh_modules`. With its default, `when_needed`, the
module files are regenerated only when the run concretized or installed
something, a root is missing, or a stamp the module writes after each
regeneration no longer matches `spack.lock`, the merged `modules`
configuration or the module trees. The result says why, in `modules_reason`.
`spack_buildcache_push` learns what it pushed by asking the mirror before and
after, not by reading Spack's messages; it gets `force: once`, which
overwrites each package on a mirror one time; and `force: true` warns.

What was tried first is in [research.md](research.md): where the module
roots come from (R1), where the module's own files can live (R2), that the
mirror can be asked right after a push (R3), and how to overwrite a chosen
set of packages (R4). R5 is what was found while writing it: one module root
shared by several environments.

This plan is a record, written after the work. The design below is the
design as built, checked against the code in 0.0.4.

## Technical Context

**Language/Version**: Python 3.12 (the modules, the stand-in, the tests)

**Primary Dependencies**: ansible-core 2.16; Spack 1.0 or later on the
managed node, tested then against the real Spack v1.2.0 only (since spec 003,
1.0.0, 1.1.0 and 1.2.0)

**Storage**: two JSON files of the modules' own in the environment's
`.spack-env/` directory ([data-model.md](data-model.md))

**Testing**: pytest through `just test`, the modules run through Ansible
against the stand-in `spack` (`tests/unit/fake_spack.py`); `just full-test`,
the integration test against the real Spack and `ansible-test sanity`

**Target Platform**: the managed node (Linux; the local machine for the
tests)

**Project Type**: an Ansible collection; this changes two modules and the
shared code under them

**Performance Goals**: a repeat run of `spack_env` with nothing to do runs
no `spack module ... refresh`; a push run reads the mirror's index twice,
a few seconds on S3

**Constraints**: a run that changes nothing reports no change and touches no
module file; check mode writes nothing in the environment and pushes
nothing; Spack's printed lines are not relied on

**Scale/Scope**: 2 modules, the shared module utilities, the stand-in, 2
unit test files, the integration test, the README, `CHANGELOG.md`

## Constitution Check

The constitution was ratified on 2026-11-17, three days after this work.
The check below holds the work, as built, to today's principles (version
1.0.1), and says where it would not have met them.

| Principle | Check | Result |
| --- | --- | --- |
| I. A Site's Choices Are Configuration, Not Code | The new option and value are a site's to set. The stamp and the record name only what Spack reports (paths, hashes, the mirror's URL). No site's name is built in; `test_no_site_knowledge.py` holds this code to that today. | Pass |
| II. A Repeat Run Changes Nothing, and Says So | This is the work that made principle II true for both modules: a repeat run of `spack_env` touches no module file, and what `spack_buildcache_push` reports comes from the mirror. Check mode regenerates nothing, writes no stamp or record, and pushes nothing. `force: true` and `refresh_modules: always` do work on every run on purpose, and their documentation says so; `force: true` also warns. One gap is left: `update_index: true` rebuilds the index on every run and does not report it (spec, Out of scope; spec 006). | Pass, with a known limitation |
| III. Written to What Spack Does | The modules call Spack's commands without a shell and read their machine-readable output (`config get --json`, `buildcache check -o`, `location -r`); the printed push lines are no longer read. They read `spack.lock` and the module trees, which no Spack command reports as a digest, and write two files of their own in `.spack-env/`, a directory of Spack's; they write no file of Spack's. What they rely on was tried against the real Spack v1.2.0 first (research). The stand-in prints its push lines in a second form, so that the tests do not depend on Spack's wording. Not met then: the collection said it supported Spack 1.0 or later but was tried only on 1.2.0, and `config get --json` does not exist in 1.0. Spec 003 found and fixed that in 0.0.3. | Pass for the pinned version; 1.0 fixed later |
| IV. Acceptance Tests Run Through the Justfile | Unit tests against the stand-in for each reason, each value of `force`, change reporting both ways and check mode; the integration test against the real Spack for the claims about it. `just test` and `just full-test` passed, `ansible-test sanity` included. The record does not say that the tests were seen to fail first. | Pass |
| V. The Operator Decides | Four decisions were asked one at a time and taken (spec, Clarifications). Merged, tagged and pushed on the operator's word. | Pass |
| The ATTIC | Did not exist then. This retrospective was written from `ATTIC/COLL-INPROGRESS/COLL-STAGE-1.md` on the operator's word for this task. | Pass |

No violation needs Complexity Tracking.

## Design, as built

### `spack_env`

- `refresh_modules` (`when_needed` by default, or `always`), with `choices`
  so that Ansible refuses any other value.
- After installing, when `modules` is not empty, the module reads the merged
  `modules` configuration once (`Spack.modules_config`) and the roots from it
  (`Spack.module_roots`, research R1), and asks `refresh_reason()` for the
  reason, in the order of [data-model.md](data-model.md).
- On any reason but `not_needed`, each system is regenerated as before:
  digest of its tree, `spack module <system> refresh -y [--delete-tree]`,
  digest again; a system is in `modules_refreshed` only when the two differ.
  Then the stamp is written (`write_state`).
- In check mode the copy of the environment is concretized as before. Then
  `refresh_reason()` is asked against the real environment, with the copy's
  `concretized` and `installed`. `modules_refreshed` is filled only for
  `missing_root` and `files_changed` (`CERTAIN`).
- `changed` is `concretized`, `installed` or `modules_refreshed`, as before.

### `spack_buildcache_push`

- `force` is `type: raw`, read by `read_force()` as `false`, `true` or
  `once`; anything else fails before Spack runs.
- `selection()` gives the environment's installed packages, externals left
  out, cut down by `only`. `lacking()` runs `spack buildcache check -m <url>
  -o <file>` (exit 1, "something is missing", is not a failure) and gives the
  selected hashes the mirror lacks.
- A real run: `lacking()`; with `force: once`, the selected hashes not in the
  record for this URL are pushed first with `--only package --force <mirror>
  /<hash>...` (research R4); then the normal push, with `--update-index`,
  `--only` and, for `force: true`, `--force` and the warning; then
  `lacking()` again. `pushed` is what was lacking before and is not after,
  plus what was overwritten. With `force: once` the record is updated.
- Check mode: `lacking()` once; `pushed` is what is lacking, plus what `force`
  would overwrite. Nothing is pushed, nothing is written, and there is no
  warning.

### Shared code, `plugins/module_utils/spack.py`

`file_digest`, `data_digest`, `tree_digest` and `module_tree_digest` (with
`CREATED_ON`, the time line), `read_state` and `write_state` (with
`STATE_DIRECTORY`, `.spack-env`), `Spack.modules_config` and
`Spack.module_roots` (with `DEFAULT_MODULE_ROOTS`). The record of this work
does not say which of these were new in it; they are listed as where it
lives today.

### Tests

- `tests/unit/test_spack_env.py`: a repeat run touches no file; installing
  alone is a reason; the stamp's contents; a file deleted, or edited, by hand
  is put back; the time line alone is not a change; a changed modules
  configuration, a missing root, no stamp, a lock changed behind the stamp, a
  system the stamp does not know; `not_requested`; check mode after a hand
  change and after a run; an unknown `refresh_modules` refused; a configured
  root is the one watched.
- `tests/unit/test_spack_buildcache_push.py`: the mirror asked before and
  after (`check`, `push`, `check`); the stand-in wording its lines another
  way; only what the mirror gained; `force: true` every run with the warning;
  no warning without it; `force: once` one time, per mirror, only a new
  package, in check mode; `force` other than true, false or once refused.
- `tests/unit/fake_spack.py`: `config get --json modules` with Spack's
  default roots; `module <system> refresh` writing Spack's time line;
  `buildcache push` with chosen hashes and `--only package`, and
  `push_format: other`; `buildcache check` from what the stand-in's mirror
  holds.
- `tests/unit/test_module_utils.py`: the digests, the time line left out,
  state kept in `.spack-env/`, unreadable state read as none.
- `tests/integration/test_real_spack.py`, `test_both_modules_against_the_real_spack`:
  a repeat run leaves every module file's modification time; `always`
  rewrites without a change; a deleted file is put back; a changed modules
  configuration (`hash_length`) regenerates with nothing to install; the push
  is reported once, from the mirror; `force: once` overwrites one time;
  `force: true` warns. Since spec 003 it runs against 1.0.0, 1.1.0 and 1.2.0.

### Documentation

- Each option's `DOCUMENTATION`, and `modules_reason` in `RETURN`.
- `README.md`: "Building an environment", "What the modules keep in the
  environment's directory", "One module tree, several environments".
- `CHANGELOG.md`: then the 0.2.0 section; now the 0.0.1 section.

## Project Structure

### Documentation (this feature)

```text
specs/008-repeat-runs-say-so/
├── spec.md
├── plan.md              # This file
├── research.md          # What Spack v1.2.0 did, tried first
├── data-model.md        # The two files, the reasons, the values of force
├── checklists/
│   └── requirements.md
└── tasks.md             # The work, as done
```

No `contracts/` or `quickstart.md`: the interface is two options and one
return value, given in the spec and the data model; the integration test is
how to see it work.

### Source Code (repository root)

```text
plugins/modules/spack_env.py               # refresh_modules, modules_reason, the stamp
plugins/modules/spack_buildcache_push.py   # asked from the mirror, force: once, the warning
plugins/module_utils/spack.py              # digests, state files, modules config and roots
tests/unit/fake_spack.py
tests/unit/test_spack_env.py
tests/unit/test_spack_buildcache_push.py
tests/unit/test_module_utils.py
tests/integration/test_real_spack.py
README.md
CHANGELOG.md
```

**Structure Decision**: the collection's existing layout.
