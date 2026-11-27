# Implementation Plan: The Cloud Sandbox replaces its Spack set-up shell with the `setup` role

**Branch**: `feature/coll-stage-3` here (the plan only), until the history was reset on 2026-11-18; Cloud-Sandbox's `feature/stage-11-csis-spack-0.3.0` (the work) | **Date**: 2026-11-14, written 2026-11-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/010-sandbox-adopts-setup/spec.md`

**Note**: This plan is a retrospective. The work was planned and done on
2026-11-14, before this repository adopted Spec Kit, and the plan is written
down from the collection's stage file. Nothing in it remains to be done.

## Summary

The Cloud Sandbox's `sandbox-provisioning` moved from the collection's
development version 0.1.0 to 0.3.0. It named `refresh_modules` on its
`spack_env` task, and replaced the shell that set Spack up (one task in its
`spack` role, three in its `intel_oneapi` role) with inclusions of the
`setup` role and three lists of steps: the base, the Intel part, and a site
mirror off by default. Its container test, with the real oneAPI, proved the
lists leave what the shell left, as data, but for the one difference the
operator chose.

Almost all the work was in Cloud-Sandbox. The collection's part was to say
what 0.3.0 can do (a step's scope, the kinds the lists need), to be proved
by the move, and to fix a defect if one was found. None was:
0.3.0 needed no change. What the move found about the collection is in
[research.md](research.md); the one finding that needed work here, how to
preview a build under `async`, became collection [stage 4](../011-preview-long-builds/spec.md).

## Technical Context

**Language/Version**: YAML and Jinja2 (the sandbox's roles and lists); Python (Cloud-Sandbox's tests)

**Primary Dependencies**: the collection at 0.3.0, installed from its git tag; ansible-core; Spack v1.2.0 ([stage 2](../009-setup-role/spec.md)'s trials); Intel oneAPI from dnf

**Storage**: N/A

**Testing**: in Cloud-Sandbox: its root `just test` and `just full-test`, its parity and traceability tests, and its container test (`tests/container/converge.sh`, `verify.yml`) with the real oneAPI. In this repository: none was needed, as nothing changed

**Target Platform**: the Cloud Sandbox's head node, as its container test builds it

**Project Type**: an Ansible collection, here proved by its first user; the change is in that user's playbooks

**Performance Goals**: N/A

**Constraints**: the collection changes only to fix a defect the move finds; Cloud-Sandbox's copies stay byte-identical, its translations keep their traceability to `funcs-setup-instance.sh`, and nothing is pushed to IOOS; nothing merged or pushed in either repository without the operator's word

**Scale/Scope**: in Cloud-Sandbox, four roles' tasks files, `group_vars/all.yml`, the pin in two files, three tests, the container test, and its records; in this repository, the stage file only

## Constitution Check

The constitution was ratified on 2026-11-17, after this work. The check is
made against it as it stands today (1.0.1), after the fact.

| Principle | Check | Result |
| --- | --- | --- |
| I. A Site's Choices Are Configuration, Not Code | The sandbox's lists, paths, compilers and mirrors stay in Cloud-Sandbox. The collection's copy is the example `docs/examples/cloud-sandbox.yml`, from which `tests/unit/test_no_site_knowledge.py` takes the names it keeps out of `plugins/` and `roles/`. Nothing entered the collection. | Pass |
| II. A Repeat Run Changes Nothing, and Says So | First application 55 changes, second 0, check mode afterwards 0. The `async` finding (R10) led to the principle's last bullet, which 0.3.0's documentation did not yet meet. | Pass; the documentation gap was closed by the next stage |
| III. Written to What Spack Does | The Spack behaviour the lists rely on (detection never removes; `config add` without `--scope` writes the user scope; `external find` misses the dnf MKL and MPI) was tried against the real Spack v1.2.0 in stage 2. It is recorded in a spec's research only now (R6 to R8). | Pass, recorded after the fact |
| IV. Acceptance Tests Run Through the Justfile | The acceptance tests that applied were Cloud-Sandbox's root `just test` and `just full-test`. No file of this repository changed, so none of its acceptance tests was needed; the stage file does not record running them. | Pass, in Cloud-Sandbox |
| V. The Operator Decides | Six decisions were asked one at a time before any work, and the answers are in the spec's Clarifications; one was not the default offered. Committed locally in both repositories; nothing merged or pushed. | Pass |
| The ATTIC | Written on the operator's instruction from the stage file in the ATTIC, which the operator named for this task. This spec stands without it. | Pass |
| Development Workflow | There was no spec at the time: the work predates Spec Kit here. The branch `feature/coll-stage-3` held only the plan, and was removed with every other branch when the history was reset on 2026-11-18. | Recorded, not a violation |

No violations; Complexity Tracking is not needed.

## What was done where

### In this repository

- The plan, as collection stage 3, on `feature/coll-stage-3`; the six
  decisions asked of the operator and recorded; after the work, its
  outcome.
- The answer to the operator's question whether 0.3.0 can set a step's
  scope (R2).
- No change to the collection. The finding about `async` was left for the
  next version (R10).

### In Cloud-Sandbox (handed off; recorded in its `INPROGRESS/STAGE-11.md` and `exportit/MAP.md`)

Where the work was, as the stage file found it in
`exportit/sandbox-provisioning/` before the change:

| What | Where | Then |
| --- | --- | --- |
| The pin | `requirements.yml`; `exportit/cloud-sandbox/units.toml`; a test in `exportit/tools` holds the two together | `0.1.0` |
| The environment | `roles/spack_environment/tasks/main.yml`: one `spack_env` task | no `refresh_modules` |
| Setting Spack up | `roles/spack/tasks/main.yml` L92-L119: one shell task (`funcs-setup-instance.sh` L661-L700) | bash, `spack_fingerprint` |
| The Intel part | `roles/intel_oneapi/tasks/main.yml`: "Let Spack find the Intel compilers" (L919, L928-L937), "Tell Spack that MKL and MPI are installed outside it" (L709-L732, L941-L949), "Make the Intel libraries Spack's providers" (L951-L955, L959) | bash, a here-document, `spack_fingerprint` |
| The fingerprint | `group_vars/all.yml`: `spack_config_json`, `spack_fingerprint`; also used by `tests/container/verify.yml` | `spack python -c` |
| Parity tests | `tests/test_parity.py`: `test_the_spack_role_runs_the_scripts_commands_in_order` reads the `$spack` lines of the shell task; `test_spack_is_told_about_the_same_externals_and_providers` reads two role variables | tied to the shell's text |
| Traceability | `tests/test_traceability.py`: every task names its lines; every line that does something is replaced or in `tests/not_carried.yml` | one comment per task |
| The container test | `tests/container/converge.sh` applies `spack` and `intel_oneapi` twice, with the real oneAPI; `verify.yml` greps Spack's configuration | the second run must change nothing |
| The site mirror's key, by hand | `exportit/sandbox-ops/bin/spack-pubkey.sh`, a byte-identical copy marked in use; the setup has these steps commented out | a script |

What changed there is the spec's FR-009 to FR-018, and the tasks in
[tasks.md](tasks.md). The container and the first-boot template already
installed `requirements.yml` before the plays, so moving the pin needed
nothing more there.

**The third list, as planned.** The key's fingerprint is the name of the
public key file the sandbox already keeps,
`sandbox-ops/keys/22DC0120263F329AE5C9DA08F525C05B06DCA266.pub`, given as
the new variable `spack_key_fingerprint`. `spack_key`, the path the script
downloads the key to, was to go, since the module fetches the key itself.
`spack-pubkey.sh` was to move to the attic as superseded: its row from
`sandbox-ops/CATALOGUE.tsv` to the attic's catalogue; its line from
`sandbox-ops.map` to `cloud-sandbox.map` under `attic/superseded/`; the
counts in `sandbox-ops/README.md`, the attic's README and `MAP.md` to
follow (15 files in use, the key among them, and 27 superseded); its
shellcheck count out of `sandbox-ops/tests/shellcheck.counts`; the copy
byte-identical. The public key file stays in `sandbox-ops/keys/`, since the
mirror tools there still sign with that key.

**What was done instead** (Cloud-Sandbox's `STAGE-11.md`):
`spack-pubkey.sh` went to `sandbox-provisioning/legacy/`, not to the attic;
`spack_key` stays; the scope decision is said on the step and in `MAP.md`,
not in `tests/not_carried.yml`; the site mirror goes to the site scope
too; the side-by-side proof compares externals by package name.

## Project Structure

### Documentation (this feature)

```text
specs/010-sandbox-adopts-setup/
├── spec.md              # What was asked and decided, and the outcome
├── plan.md              # This file
├── research.md          # What the move found about the collection
├── tasks.md             # The work, as a record, all done
└── checklists/
    └── requirements.md  # The spec's quality checklist
```

No `data-model.md`, `contracts/` or `quickstart.md`: the collection's
interface did not change.

### Source Code (repository root)

Nothing was changed. These are the collection's files the move relied on,
and against which this spec's collection-side claims were checked on
2026-11-27:

```text
roles/setup/
├── defaults/main.yml            # spack_setup_scope: site; the executable (spack_setup_spack at 0.3.0)
├── tasks/main.yml               # the list checked, then each step included
├── tasks/step.yml               # one step: its kind's tasks, then its result
├── tasks/kinds/*.yml            # one file per kind; scope from the step or spack_setup_scope
└── README.md                    # the kinds and their options
plugins/modules/spack_env.py     # refresh_modules; the notes on async and check mode (since 0.3.1)
plugins/modules/spack_detect.py  # require
docs/examples/cloud-sandbox.yml  # the sandbox's first two lists, as the script has them
tests/unit/test_examples.py      # the example held to the script's commands, and a repeat run changing nothing
tests/unit/test_no_site_knowledge.py   # nothing the example names is in plugins/ or roles/
tests/unit/test_async_and_check_mode.py   # the async form (from collection stage 4)
```

Cloud-Sandbox's files are named in the table above and in the spec; they
are that repository's, and are not listed here.

**Structure Decision**: no change to the collection's layout.
