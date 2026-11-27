# Implementation Plan: Say how to preview a long build

**Branch**: `feature/coll-stage-4`, until the history was reset on 2026-11-18 | **Date**: 2026-11-14 (retrospective, written 2026-11-27) | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/011-preview-long-builds/spec.md`

## Summary

Documentation and a test, no change to any module. `spack_env`'s notes say
that Ansible refuses `async` in check mode and give the form that previews,
`async: "{{ 0 if ansible_check_mode else 86400 }}"` and the same for `poll`;
its example and the README's use it; the README's examples are made neutral;
and a unit test holds the documentation to the form and shows, against the
stand-in `spack`, that the form previews and builds. Released as 0.3.1 with a
`spack_config` fix found the same day by the Cloud Sandbox's stage 12;
withdrawn 2026-11-18, and part of 0.0.1.

What Ansible does, and why the form works, is in [research.md](research.md)
(R1).

## Technical Context

**Language/Version**: YAML in Python strings (the module's `DOCUMENTATION`
and `EXAMPLES`), Markdown (the README); Python 3.12 (the test)

**Primary Dependencies**: ansible-core 2.16

**Storage**: N/A

**Testing**: pytest through `just test`: the documentation read as text and
YAML, and three plays run with `ansible-playbook` against the stand-in
`spack`. `just full-test`: the same, then `ansible-test sanity` and Galaxy's
import checks, which run `ansible-doc` on every plugin.

**Target Platform**: wherever a site runs `spack_env`

**Project Type**: an Ansible collection; this feature changes one module's
documentation and the README

**Performance Goals**: N/A

**Constraints**: no module's behaviour changes (spec, FR-007)

**Scale/Scope**: one module's notes and example, the README, one new unit
test file, the changelog

## Constitution Check

The constitution was ratified on 2026-11-17, three days after this work, so
this check is made against today's constitution (1.0.1), after the fact.

| Principle | Check | Result |
| --- | --- | --- |
| I. A Site's Choices Are Configuration, Not Code | Nothing is added to `plugins/` or `roles/` but documentation. The README's examples, which named one site's paths, are made neutral. The numbers in the form are an example's. | Pass |
| II. A Repeat Run Changes Nothing, and Says So | This work is where principle II's last rule comes from: a task that builds for hours runs under `async`, and every example gives `async` and `poll` in the form that previews. The module already supported check mode; now its documentation lets a site use it. | Pass |
| III. Written to What Spack Does | No Spack behaviour is relied on. What Ansible does was found by running it (the Cloud Sandbox's container test) and is held by a test that runs Ansible (R1). | Pass |
| IV. Acceptance Tests Run Through the Justfile | Unit tests for the documentation and for the claim, both ways (previews, builds) and the failure it avoids. "What the documentation promises is held by a test": the notes and examples are read by the test. `just test`, then `just full-test`. | Pass |
| V. The Operator Decides | The release and the pin were asked, the pin twice, and the answers are in the spec's Clarifications; so was the release of the `spack_config` fix, a defect in a released version, as 0.3.1. | Pass |
| The ATTIC | This retrospective was written from the ATTIC, on the operator's word for this task. The spec stands without it. | Pass |

No violations; Complexity Tracking is not needed.

## Design, as built

### `spack_env`'s documentation, [plugins/modules/spack_env.py](../../plugins/modules/spack_env.py)

- `notes`: the existing "A build can take hours. Run the task with
  C(async) and C(poll)." is kept, and followed by a note that quotes
  Ansible's message, gives the reason (a preview builds nothing and is over
  in a minute, so it does not need `async`), and gives both keywords in the
  form.
- `EXAMPLES`: the build task's `async` and `poll` are in the form, with a
  comment: "Asynchronous for the build, and not when previewing: Ansible
  refuses async in check mode."

### The README, [README.md](../../README.md)

- The "Building an environment" example is the same task in the same form,
  with the same comment.
- Its two examples use neutral paths and names:
  `/opt/spack-environments/base`, `/opt/spack/bin/spack`, `site-cache`,
  `mycompiler_environment`, `<the key's fingerprint>`.

### The test, [tests/unit/test_async_and_check_mode.py](../../tests/unit/test_async_and_check_mode.py)

| Test | Holds |
| --- | --- |
| `test_the_notes_say_why_and_give_the_form` | The notes quote Ansible's message and give both forms (FR-001, FR-002) |
| `test_no_example_gives_async_as_a_plain_number` | No `async:` or `poll:` as a plain number in `spack_env`'s `EXAMPLES`, `README.md` or `roles/setup/README.md`; the `EXAMPLES` hold both forms (FR-003, FR-004) |
| `test_the_form_previews_without_building` | With `--check`: succeeds, not refused, no `install` call, no `spack.lock` (FR-005, US1 scenario 1) |
| `test_the_form_builds_asynchronously_when_not_previewing` | Without `--check`: one `install` call (FR-005, US1 scenario 2) |
| `test_a_plain_number_cannot_be_previewed` | `async: 86400`, `poll: 60` with `--check` fails with Ansible's message (FR-005, US1 scenario 3; research R1) |

A plain number is found with `^\s*(async|poll):\s*\d+\s*$`, line by line.
The plays run the collection as installed for the unit tests (`COLLECTIONS`
in `tests/unit/runner.py`), with the stand-in `spack` on `PATH`.

**Alternative rejected:** checking the examples by eye in review. That is how
0.1.0 to 0.3.0 shipped with plain numbers.

### The release

Kept on `develop` by decision (spec, Clarifications); then, the same day,
released as 0.3.1 with the `spack_config` fix and the Cloud Sandbox's pin
moved to it. The release, its tag and the pin are history: 0.3.1 was
withdrawn on 2026-11-18, and the collection is now released from 0.0.1 on
Ansible Galaxy ([specs/001-galaxy-publish/](../001-galaxy-publish/spec.md)).

## Project Structure

### Documentation (this feature)

```text
specs/011-preview-long-builds/
├── spec.md
├── plan.md              # This file
├── research.md          # What Ansible does with async in check mode
├── tasks.md
└── checklists/
    └── requirements.md
```

No `data-model.md`, `contracts/` or `quickstart.md`: the change is two
keywords' documentation, and the test file is its own quickstart.

### Source Code (repository root)

```text
plugins/modules/spack_env.py               # notes and EXAMPLES
README.md                                  # the example in the form; both examples neutral
tests/unit/test_async_and_check_mode.py    # new: the documentation and the claim
CHANGELOG.md                               # the change (now under 0.0.1, "Building an environment")
```

Released with it, and not this spec's design:

```text
plugins/module_utils/spack.py              # plan_absent, highest_emptied: the spack_config fix
tests/unit/test_spack_config.py            # its unit tests
tests/integration/test_real_setup.py       # its test against the real Spack
```

**Structure Decision**: the collection's existing layout; one test file is
added, nothing else.
