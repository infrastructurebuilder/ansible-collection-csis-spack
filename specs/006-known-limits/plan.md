# Implementation Plan: Two known limits, said where a site reads them, or removed

**Branch**: `feature/known-limits` | **Date**: 2026-11-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-known-limits/spec.md`

## Summary

Tried against the real Spack 1.0.0, 1.1.0 and 1.2.0 first
([research.md](research.md)), the two limits turned out otherwise than
recorded on 2026-11-14:

- **The index (User Story 1).** Spack itself leaves a mirror's index alone
  when a push sends nothing, `--update-index` or not (R1). What the operator
  chose is already what happens. The work is the documentation and an
  integration test that holds it; no code changes.
- **The preview (User Story 2).** Files inside the environment's directory
  are already in the preview's copy. What breaks is a relative `include:`
  that leads above it (Spack refuses the copy, R2) and any relative
  `develop:` path (the copy's lock records the wrong `dev_path`, R3). In
  check mode `spack_env` rewrites the copy's relative `include:` and
  `develop:` paths to the originals' absolute paths, with Spack's own Python,
  so that the preview reads and records what a real run would (R4).

**Confirmed by the operator, 2026-11-27**: User Story 2's design goes beyond
the clarified answer (copy the files inside, name the ones above), which R2
and R3 show cannot work as written; the rewrite covers both cases, and the
spec now says so. See "Decision to confirm" below.

## Technical Context

**Language/Version**: Python 3.12 (the module, the tests)

**Primary Dependencies**: ansible-core 2.16; Spack 1.0 or later on the node
(its own Python, `spack python`, and `spack.util.spack_yaml`)

**Storage**: N/A

**Testing**: `just test`: unit tests against the stand-in `spack`, which
learns to run a `spack python <script>` the module gives it (the script runs
in the test's own Python, with a small stand-in for
`spack.util.spack_yaml`); `just full-test`: integration tests against the
real 1.0.0, 1.1.0 and 1.2.0 for both limits

**Target Platform**: the managed node, as today

**Project Type**: an Ansible collection; this changes one module's check
mode and two modules' documentation

**Performance Goals**: a preview costs one more `spack python` run (about a
second); a real run costs nothing more

**Constraints**: nothing of the real environment, or of what its paths
name, is written in check mode; a real run is unchanged; a `spack.yaml`
with no relative `include:` or `develop:` path is previewed as today

**Scale/Scope**: `plugins/modules/spack_env.py` (check mode; docs);
`plugins/modules/spack_buildcache_push.py` (docs); the stand-in `spack`;
unit and integration tests; `CHANGELOG.md`; a note in spec 008

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Result |
| --- | --- | --- |
| I. A Site's Choices Are Configuration, Not Code | Nothing of a site is built in; the paths come from the site's own `spack.yaml`. | Pass |
| II. A Repeat Run Changes Nothing, and Says So | The index: held by a test that a repeat push changes nothing (R1). The preview: check mode writes only into its own temporary directory, and now reports what a real run would. | Pass |
| III. Written to What Spack Does | Both limits were tried against the real 1.0.0, 1.1.0 and 1.2.0 before design, and the first turned out not to be one (R1). The rewrite uses Spack's own Python and YAML (R4, R5). | Pass |
| IV. Acceptance Tests Run Through the Justfile | Unit tests first, seen to fail; integration tests on the three versions; `just test`, then `just full-test`. | Pass |
| V. The Operator Decides | The two answers are in the spec's Clarifications, and the operator confirmed User Story 2's design, which goes beyond the second (2026-11-27). Committed locally. | Pass |
| The ATTIC | Not consulted. | Pass |

No violations; Complexity Tracking is not needed. Re-checked after the
design below: unchanged.

## Decision to confirm (confirmed 2026-11-27)

The clarified answer for User Story 2 was: copy the files that relative
paths name inside the environment's directory into the preview, and name
the ones above it in the result, the preview made without them.

R2 shows the files inside are copied already, and that a preview without an
`include:` above the environment cannot be made: Spack refuses it. R3 shows
that every relative `develop:` path, inside or above, gives the preview a
lock a real run would not write. Rewriting the copy's relative paths to the
originals' absolute paths (R4) makes the preview read and record what a real
run would in every case, and leaves nothing to name.

**Proposed:** do that, and change FR-004, User Story 2 and the edge case of
a path above the environment to say so.

## Design

### `spack_env`, check mode (User Story 2)

After `shutil.copytree` of the environment into the temporary directory, and
before `concretize`:

1. Write a short script into the temporary directory (not into the copy) that
   loads the copy's `spack.yaml` with `spack.util.spack_yaml`, replaces each
   relative `include:` entry (a string, or a mapping's `path`) and each
   `develop:` entry's `path` with the absolute path it names from the real
   environment's directory, leaves absolute paths, paths with `$`, and a
   mapping with no `path` (a git include) as they are, and writes the file
   back.
2. Run it with `spack python <script> <copy>/spack.yaml <real directory>`, as
   an argument list, through the shared runner (no `-e`).
3. Concretize the copy as today.

A `spack.yaml` with neither key is left as it is, and the script is not run.

### `spack_buildcache_push` (User Story 1)

No change to what it runs. Its documentation of `update_index` says: "Spack
rebuilds the index only after a push that sent something; a run with nothing
to push leaves it as it is, and an index changed by other means is not put
right by such a run (run `spack buildcache update-index` for that, in a
`command` step)."

### Tests

- **`tests/unit/test_spack_env.py`**: in check mode, an environment whose
  `spack.yaml` has `include: [./extra.yaml, ../shared.yaml, /abs/x.yaml]` and
  `develop: {pkg: {path: ../src}}`: the copy the stand-in concretizes has
  `../shared.yaml` and `../src` rewritten to the real absolute paths, the
  others as they were; the real environment's `spack.yaml` is unchanged; one
  with neither key runs no `spack python`.
- **`tests/unit/fake_spack.py`**: `python <script> <args>` runs the script
  with the stand-in's own Python, with `spack.util.spack_yaml` given by a
  module under `tests/unit/` that reads and writes YAML with PyYAML.
- **`tests/integration/test_real_spack.py`**, per version: (1) the preview
  of an environment that includes `../shared.yaml` succeeds and reports no
  change after a real concretize; (2) an environment pushed twice with
  `update_index: true`: the second push reports no change and the index file
  is not rewritten.

### Documentation

- `spack_env`'s check-mode note: relative `include:` and `develop:` paths
  are read where they are, also above the environment's directory; a
  develop source above the environment is not copied (one inside it is
  copied with the directory, as today), and the preview records the real
  path either way.
- `spack_buildcache_push`'s `update_index`: as above.
- `CHANGELOG.md`: the preview's paths; the index documented.
- `specs/008-repeat-runs-say-so/spec.md`, Out of Scope: a note that spec 006
  found the index limit not to be one (R1), and removed the preview's.

## Project Structure

### Documentation (this feature)

```text
specs/006-known-limits/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0: what Spack does with both
├── quickstart.md        # Phase 1
├── contracts/
│   └── interface.md     # Phase 1: what check mode runs; the docs
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

No `data-model.md`: there is no new data, only a rewrite of an existing file
in a temporary copy.

### Source Code (repository root)

```text
plugins/modules/spack_env.py             # check mode: the rewrite; docs
plugins/modules/spack_buildcache_push.py # docs of update_index
tests/unit/fake_spack.py                 # python <script>
tests/unit/spack/util/spack_yaml.py      # a stand-in of Spack's YAML (new)
tests/unit/test_spack_env.py
tests/integration/test_real_spack.py
CHANGELOG.md
specs/008-repeat-runs-say-so/spec.md     # a note in Out of Scope
```

**Structure Decision**: the collection's existing layout; one helper for the
stand-in under `tests/unit/`.
