# Implementation Plan: Name the setup role's Spack executable `spack_setup_executable`

**Branch**: `feature/setup-executable-rename`, until the history was reset on 2026-11-18 | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-setup-executable-rename/spec.md`

## Summary

The `setup` role's variable for the Spack executable is renamed from
`spack_setup_spack` to `spack_setup_executable`. The old name keeps working
through the new variable's default, which reads the old one when it is set.
No task is added to the role, and no module changes.

## Technical Context

**Language/Version**: YAML and Jinja2 (the role); Python 3.12 (the tests)

**Primary Dependencies**: ansible-core 2.16

**Storage**: N/A

**Testing**: pytest through `just test` (the role against the stand-in `spack`); `just full-test` (the role against the real Spack v1.2.0)

**Target Platform**: wherever the role runs today

**Project Type**: an Ansible collection; this feature changes one role's interface

**Performance Goals**: N/A

**Constraints**: a playbook written for 0.3.0 or 0.3.1 must run unchanged

**Scale/Scope**: one default, five task files, one README, two examples, two test files, the changelog

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Result |
| --- | --- | --- |
| I. A Site's Choices Are Configuration, Not Code | The executable's path stays a site's configuration. The role's default is still the bare name `spack`. | Pass |
| II. A Repeat Run Changes Nothing, and Says So | No task is added; change reporting and check mode are untouched. | Pass |
| III. Written to What Spack Does | No Spack behaviour is involved. | Pass |
| IV. Acceptance Tests Run Through the Justfile | Three new unit tests, written first and seen to fail; `just test`, then `just full-test`. | Pass |
| V. The Operator Decides | Both decisions were asked and are in the spec's Clarifications. Committed locally; merged only on the operator's word. | Pass |
| The ATTIC | Not consulted. | Pass |

No violations; Complexity Tracking is not needed. Re-checked after the design
below: unchanged.

## Design

One line carries both names, in `roles/setup/defaults/main.yml`:

```yaml
spack_setup_executable: "{{ spack_setup_spack | default('spack') }}"
```

- **Neither set:** `spack_setup_spack` is undefined, so the default is `spack`.
- **Only the old name set:** the default evaluates to its value.
- **The new name set:** a variable a playbook sets always outranks a role
  default, so the default, and with it the old name, is not consulted.

`spack_setup_spack` leaves the defaults file. If it stayed there with the
value `spack`, it would always be defined, and nothing would distinguish a
playbook that set it from one that did not.

The five files under `roles/setup/tasks/kinds/` that pass the executable to a
module pass `spack_setup_executable` instead.

**Alternative rejected:** a first task that sets a fact from whichever name is
defined. It costs a task on every run and a line of output, and it would be
the only way to add a warning, which the operator decided against.

**What the tests must prove.** The stand-in `spack` is on `PATH` in every unit
test, so a role that ignored the variable would still pass a test that only
checks the outcome. The new tests therefore name a second way to the stand-in,
outside `PATH`, which leaves a mark when it is run; a test passes only if the
mark is there.

## Project Structure

### Documentation (this feature)

```text
specs/002-setup-executable-rename/
├── spec.md
├── plan.md              # This file
├── tasks.md
└── checklists/
    └── requirements.md
```

No `research.md`, `data-model.md` or `contracts/`: nothing was unknown, and
the interface is one variable, stated in the spec.

### Source Code (repository root)

```text
roles/setup/
├── defaults/main.yml            # spack_setup_executable, reading the old name
├── tasks/kinds/{command,config,detect,gpg_key,mirror}.yml   # pass the new name
└── README.md                    # the Variables table, a note on the old name, the example
docs/examples/
├── cloud-sandbox.yml            # the new name
└── system-compiler.yml          # the new name
tests/unit/test_setup_role.py    # the defaults; the three cases
tests/integration/test_real_setup.py   # the new name against the real Spack
CHANGELOG.md                     # Unreleased
```

**Structure Decision**: the collection's existing layout; no file is added
outside `specs/`.
