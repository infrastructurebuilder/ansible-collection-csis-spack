# Implementation Plan: The install step moves a Spack to another version, when a site asks

**Branch**: `feature/move-spack-version` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-move-spack-version/spec.md`

## Summary

`spack_checkout`, from spec 004, gains an option `move`, off by default.
With it on, a Spack at the path at another version is moved to the version
named, in place: the new version is first cloned into a hidden directory
beside the path, its `spack --version` checked, and its files compared with
the files the site keeps at the path; only then is it fetched into the path
and checked out. A site's edited files, or a site's file that the new
version would overwrite, refuse the move with nothing changed. The `setup`
role's `spack` step passes `move` through.

What was tried first is in [research.md](research.md): a shallow checkout
moves in place (R1), git silently overwrites a site's ignored file that the
new version tracks (R2, which is why the move compares first), and staging
the new version beside the path costs one clone (R3).

**Names, confirmed by the operator on 2026-11-26** (spec, Clarifications): the
option `move` (bool, default `false`) on `spack_checkout` and on the `spack`
step, `version_added: 0.0.4` (spec 004's module is not released yet, so both
go out together), and the result key `moved_from`. See "Names" below.

## Technical Context

**Language/Version**: Python 3.12 (the module, the filter, the tests); YAML
(the role)

**Primary Dependencies**: ansible-core 2.16; `git` 2.18 or later on the node
(as spec 004); Spack 1.0 or later

**Storage**: N/A

**Testing**: pytest through `just test`: the module's tests run real `git`
against `tests/unit/spack_source.py`'s repositories, which gain a
`.gitignore` and a file one version tracks and an earlier one ignores (R2);
`just full-test`: integration tests that move the real Spack between 1.0.0,
1.1.0 and 1.2.0 using the local clones as sources

**Target Platform**: the managed node, as spec 004

**Project Type**: an Ansible collection; this adds one option to one module
and one option to one step kind

**Performance Goals**: a move costs one shallow clone of the new version
(about 6 MB from GitHub, R3 of 004) and one local fetch; a run with the
option on and the Spack at the version costs nothing more than spec 004's

**Constraints**: with `move` off, everything spec 004 does is unchanged; no
file a site added is lost and no file a site edited is overwritten; nothing
at the path changes until every check has passed; check mode changes
nothing and contacts no source

**Scale/Scope**: `plugins/modules/spack_checkout.py`;
`plugins/filter/setup_problems.py` (one optional option);
`roles/setup/tasks/kinds/spack.yml`; `tests/unit/spack_source.py`; the
module's and the role's unit tests; one integration test; the role README,
the module's docs, `CHANGELOG.md`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Result |
| --- | --- | --- |
| I. A Site's Choices Are Configuration, Not Code | Whether to move is the site's choice, an option off by default. No version or path is built in. | Pass |
| II. A Repeat Run Changes Nothing, and Says So | A move reports a change; a repeat run finds the Spack at the version and reports none (FR-004). Check mode reports the move and changes nothing, `.git` included, and contacts no source (R4). The option's documentation says what a run with it on does. | Pass |
| III. Written to What Spack Does | The move is git's, as Spack's install is (004, R1); what git does was tried against the real Spack clones first (R1–R6), and it found the overwrite R2 that the design guards against. After a move the module asks the moved Spack for its version. | Pass |
| IV. Acceptance Tests Run Through the Justfile | Tests first, seen to fail (`just unit -k move`, `just integration -k move`), then `just test`, then `just full-test`. Every case of FR-002–FR-010 in a real run and in check mode (SC-005). | Pass |
| V. The Operator Decides | The spec exists on the operator's word (004's Clarifications). The option's name, `version_added` and the result key were proposed here and confirmed by the operator on 2026-11-26, with three more answers (spec, Clarifications). Committed locally. | Pass |
| The ATTIC | Not consulted. | Pass |

No violations; Complexity Tracking is not needed.

**Re-checked after the design below:** unchanged. One point weighed under
Principle II: a move refused after its staging clone leaves nothing at the
path changed, since the staging is beside it; a move stopped during the
checkout can leave the path half moved, which the next run reports as edited
files and refuses (R5), as the spec allows.

## Design

### Names

| Thing | Chosen | Why | Weighed |
| --- | --- | --- | --- |
| The option | `move` (bool, default `false`) | The spec's word; says what it allows | `update` (as `ansible.builtin.git`, which also pulls a branch forward, which this does not); `allow_move` |
| `version_added` | `0.0.4` | `spack_checkout` itself is 0.0.4 and unreleased | `0.0.5`, a release of its own |
| The result key | `moved_from` | What was there before a move: the tag, branch or commit, and its `spack --version` | `previous_version` |

### The module, `plugins/modules/spack_checkout.py`

The state machine of spec 004 is unchanged but for one row:

| At `path` | `move: false` (default) | `move: true` |
| --- | --- | --- |
| A Spack at another version | fails, nothing changed (004 FR-007) | moved, as below; `changed` true, `moved_from` set |

Every other row (nothing, empty, at the version, not a Spack) is as 004.

The move, with `move: true`, in this order; any failure stops it, and
nothing at the path has changed before step 5:

1. **Edited files**: `git -C <path> status --porcelain --untracked-files=no`;
   any line refuses, naming the files (FR-005).
2. **Stage**: clone the version named into `tempfile.mkdtemp(dir=<parent>,
   prefix=".<name>.move-")`, with spec 004's `clone()` (tag or branch by
   `clone --depth 1 --branch`, a full hash by init and fetch). A version not
   in the source fails here (FR-007).
3. **Check the staged version**: its `bin/spack --version` must be 1.0 or
   later, with 004's `Installer.check()` (spec edge case: refused before the
   Spack there is changed).
4. **Compare**: the staged version's files (`git -C <stage> ls-tree -r
   --name-only HEAD`) against the files at the path that git does not track
   (`git -C <path> ls-files --others`, and the same with `--ignored
   --exclude-standard`); any name in both refuses, naming them (FR-006, R2).
5. **Move**: fetch from the staged copy into the path (`git -C <path> fetch
   --quiet --depth 1 file://<stage> <ref>`: `refs/tags/<v>:refs/tags/<v>`
   for a tag, `refs/heads/<b>:refs/remotes/origin/<b>` for a branch, the
   hash for a commit); check out (`checkout --quiet --detach
   '<v>^{commit}'`, `checkout --quiet -B <b> origin/<b>`, or `checkout
   --quiet --detach FETCH_HEAD`); set `origin` to the source named
   (`remote set-url origin <source>`).
6. **Check the moved Spack**: `<path>/bin/spack --version` (FR-008).
7. **Clean up**: remove the staged copy, in every case.

Whether the staged version is a tag or a branch is read from the staged
clone: after `clone --branch`, `symbolic-ref -q HEAD` succeeds for a branch
and fails for a tag.

In check mode, with `move: true` over another version: report `changed` true
and `moved_from`, run only spec 004's reads, and add to `msg` that whether
the version exists and whether a site's file would be overwritten are found
when the move is made (R4).

Nothing that the old version built is touched (FR-010): the move changes
only what git tracks, and the compare step keeps every other file.

### The role

- `plugins/filter/setup_problems.py`: `KINDS["spack"]["optional"]` gains
  `move`.
- `roles/setup/tasks/kinds/spack.yml`: passes `move: "{{
  spack_setup_step.move | default(omit) }}"`.
- After a move in a real run the later steps run the moved Spack, as they run
  any Spack at `<path>/bin/spack`. In check mode a move is a change the
  later steps cannot preview either (the Spack there is not the version they
  would run), so `spack_setup_not_installed` is set for a would-be move as for
  a would-be install, and they are recorded as not previewed. The message
  says "Spack is not installed or moved yet".

### Tests

- **`tests/unit/spack_source.py`**: every commit gets a `.gitignore` of
  `/opt` and `/etc/site/*`; `v1.2.0` and the branch also track
  `etc/site/README.md` (un-ignored with `!/etc/site/README.md`), as Spack 1.2
  does with `etc/spack/site/README.md` (R2). Spec 004's tests are unchanged.
- **`tests/unit/test_spack_checkout.py`**, a section for spec 005: with
  `move: true`, from `v1.0.0` to `v1.2.0`, to the branch, to a full hash, and
  back to `v1.0.0`: each a change, `moved_from` naming the old version, HEAD
  as 004's install leaves it, `origin` the source named, then no change; with
  `move` left out, spec 004's failure; check mode over another version:
  `changed` true, `moved_from`, nothing changed (HEAD, `.git`'s refs and
  objects counted, files) and no `git` but reads; edited files: refused,
  named, nothing changed; a site's file under `opt/`, and in `etc/site/`
  other than the README: kept; a site's `etc/site/README.md` on `v1.0.0`:
  the move to `v1.2.0` refused, naming it, the file as the site left it; a
  version not in the source: refused, nothing changed, no `.spack.move-*`
  left; `v0.23.0`: refused before the path changes; a source other than the
  one the Spack came from: used, and `origin` set to it.
- **`tests/unit/test_setup_filter.py`**: `move` is an option of the `spack`
  kind.
- **`tests/unit/test_setup_role.py`**: a `spack` step with `move: true` and
  another version, then a `config` step: both change, the `config` step runs
  the moved Spack; check mode: the `config` step not previewed.
- **`tests/integration/test_real_spack.py`**, a test whose name contains
  `move`, once (not per version): install v1.0.0 from its clone, add a site
  file under `etc/spack/` and one under `opt/`, move to v1.1.0 and to v1.2.0
  and back to v1.0.0, each from its own clone; each `spack --version` the
  version moved to, the site's files kept, a repeat run no change.

### Documentation

- The module's docs: `move`, what a move does and keeps, that it is off by
  default, that it refuses over edited files and over a site's file the new
  version would overwrite, that it does not rebuild what the old version
  built and that environments may need to be concretized and installed
  again, that check mode does not find a missing version or an overwrite,
  and that `.git` keeps both versions' objects.
- `roles/setup/README.md`: `move` in the kinds table and in the `spack`
  step's section.
- `CHANGELOG.md`: the Unreleased section gains `move`.

## Project Structure

### Documentation (this feature)

```text
specs/005-move-spack-version/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0: what git does to a Spack moved in place
├── data-model.md        # Phase 1: the option, the move's steps, the result
├── quickstart.md        # Phase 1: how to see it work
├── contracts/
│   └── interface.md     # Phase 1: the option, what is run
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks; not made here)
```

### Source Code (repository root)

```text
plugins/modules/spack_checkout.py        # move, the staged move, moved_from
plugins/filter/setup_problems.py         # move on the spack kind
roles/setup/tasks/kinds/spack.yml        # move passed through; a would-be move in check mode
roles/setup/tasks/step.yml               # the not-previewed message
roles/setup/README.md
tests/unit/spack_source.py               # .gitignore, etc/site/README.md
tests/unit/test_spack_checkout.py, test_setup_filter.py, test_setup_role.py
tests/integration/test_real_spack.py
CHANGELOG.md
```

**Structure Decision**: the collection's existing layout; no new file
outside `specs/`.
