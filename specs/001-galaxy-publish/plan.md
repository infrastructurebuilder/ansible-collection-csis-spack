# Implementation Plan: Publish the collection to Ansible Galaxy

**Branch**: `feature/galaxy-publish`, until the history was reset on 2026-11-18 | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-galaxy-publish/spec.md`

**Note**: This plan was written on 2026-11-17 for work already begun, when the
repository adopted Spec Kit. Its first half describes what is built and on
`develop`; what remains is in [tasks.md](tasks.md).

## Summary

The collection is published to Ansible Galaxy from its release tag by one
target, `just publish`, which the operator can run on their local machine and
which a GitHub Actions workflow runs when a release tag is pushed. The target
runs a small tool that refuses every state in which the upload might not be
what was released, and that leaves a version the server already has alone.
Galaxy's own import checks run on the tarball in `just full-test`, so an
upload is not the first time they are run.

Built and merged into `develop`: the tool, the target, the workflow, the
import check, the metadata, the documentation and the tests. Remaining: the
namespace and the token (the operator's), the release of 0.0.1, its upload,
the proof on a clean machine, and the hand-off to the Cloud Sandbox.

## Technical Context

**Language/Version**: Python 3.12 (the tools and tests); YAML (the workflow, `galaxy.yml`)

**Primary Dependencies**: ansible-core 2.16 (`ansible-galaxy collection build` and `publish`); galaxy-importer (0.4.44 when the check was written); `just`; `uv`

**Storage**: N/A

**Testing**: pytest through `just test`; `just full-test` adds `just import-check`

**Target Platform**: the operator's local machine; GitHub Actions on `ubuntu-24.04`; galaxy.ansible.com

**Project Type**: an Ansible collection; this feature is release tooling around it

**Performance Goals**: N/A

**Constraints**: the API key only in the environment or a secret, never on a command line; a published version is exactly its tag; a version is never uploaded twice; nothing is released, pushed or published without the operator's word

**Scale/Scope**: one tool, one workflow, two `just` targets, one test file; no change to any module or to the role

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Result |
| --- | --- | --- |
| I. A Site's Choices Are Configuration, Not Code | Nothing changes in `plugins/` or `roles/`. The tool names this collection's own namespace and server, which are not a site's. | Pass |
| II. A Repeat Run Changes Nothing, and Says So | Not a module, but the same idea holds: publishing a version that is already there uploads nothing, says so and succeeds. | Pass |
| III. Written to What Spack Does | No Spack behaviour is involved. The tool's one assumption about Galaxy (its index answers 200 for a version it has and 404 for one it lacks) is first proved against the real server by the first upload; any other answer fails. | Pass, with that proof outstanding |
| IV. Acceptance Tests Run Through the Justfile | `just publish` and `just import-check` are targets; the workflow calls `just`, not the tools. `tests/unit/test_publish.py` covers every refusal. | Pass |
| V. The Operator Decides | Both decisions were asked and are in the spec's Clarifications. The release, the tag push and the upload each wait for the operator's word. The key is never in the repository. | Pass |
| The ATTIC | This spec was carried over from a retired stage on the operator's instruction and does not depend on it. | Pass |

No violations; Complexity Tracking is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-galaxy-publish/
├── spec.md              # What and why, with the decisions taken
├── plan.md              # This file
├── tasks.md             # What is done and what remains
└── checklists/
    └── requirements.md  # The spec's quality checklist
```

No `research.md`, `data-model.md` or `contracts/`: the feature has no data
model and no interface beyond the `just publish` command, whose behaviour the
spec's requirements state in full.

### Source Code (repository root)

```text
galaxy.yml                       # homepage, documentation; build_ignore keeps tools/ and .github/ out of the tarball
Justfile                         # import-check, publish; full-test runs import-check; release says to publish from the tag
tools/
└── publish.py                   # what `just publish` runs: the refusals, the "already there" question, the upload
.github/workflows/
└── publish.yml                  # on a pushed bare-version tag, or by hand: just init, just test, just publish
tests/unit/
└── test_publish.py              # every refusal, the key kept off the command line, the workflow's trigger and secret
pyproject.toml                   # the ruff rules that mirror ansible-test sanity's pylint
README.md                        # Installing it; Publishing a release
CHANGELOG.md                     # the 0.0.1 entry, and the withdrawn development versions
```

**Structure Decision**: the collection's existing layout. Release tooling
lives in `tools/` and is kept out of the tarball; nothing under `plugins/` or
`roles/` is touched.

## How it works

- **`just publish`** depends on `just import-check`, so the tarball is built
  and passes Galaxy's checks first. It then runs `tools/publish.py` on the
  tarball.
- **`tools/publish.py`** refuses without `GALAXY_API_KEY`; unless HEAD is
  tagged with `galaxy.yml`'s version; and with changes in the working tree. It
  then asks the server's published index whether it has the version: 200 means
  it has, and the tool says so and exits 0; 404 means it has not; anything
  else fails. Only then does it run `ansible-galaxy collection publish`, with
  the key in that process's environment and not on its command line.
  `GALAXY_SERVER` names another server.
- **`.github/workflows/publish.yml`** runs on a pushed tag matching
  `[0-9]+.[0-9]+.[0-9]+`, or by hand. It runs `just init`, `just test` and
  `just publish` with the secret `GALAXY_API_KEY`, in the `galaxy` environment,
  which the operator can give required reviewers so that a tag waits for
  approval. Without the secret it fails. It has never run: its first run is
  the push of the next release's tag.
- **`just import-check`** runs galaxy-importer on the tarball: `ansible-doc` on
  every plugin, and ansible-lint. The tarball of the development version 0.3.1
  passed it unchanged.
- **Ruff mirrors `ansible-test sanity`'s pylint** as far as it can:
  `pyproject.toml` enables the ruff rules whose pylint code is enabled under
  ansible-test 2.16's `collection.cfg`. Ruff has no rule for
  `disallowed-name` or `dangerous-default-value`; only `just full-test` finds
  those.

## What remains, and its order

1. **The operator** is granted the namespace, makes an API token, and sets the
   secret `GALAXY_API_KEY` in the repository or its `galaxy` environment.
2. **Release 0.0.1** from `develop`, on the operator's word: the changelog's
   0.0.1 section gets its date, `just full-test` passes, and the release is
   cut with git-flow and tagged `0.0.1`. (`galaxy.yml` says 0.0.1 already:
   the development tags before it were withdrawn on 2026-11-18.)
3. **Publish from the tag**, one way or the other. Pushing the tag is itself a
   publish, so it is said before the tag is pushed.
4. **Prove it** on a clean machine: install by name, and `ansible-doc` a
   module.
5. **Hand off** to the Cloud-Sandbox workspace: `requirements.yml` by name with
   a range, `units.toml` keeping the version, its `tools` test reading the
   range, and a container run installing from Galaxy.
