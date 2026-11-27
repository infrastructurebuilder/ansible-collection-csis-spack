# Feature Specification: Say how to preview a long build

**Feature Branch**: `feature/coll-stage-4`, until the history was reset on 2026-11-18

**Created**: 2026-11-14, planned on `feature/remaining-plans` and carried out the same day on `feature/coll-stage-4`

**Status**: Done 2026-11-14 (retrospective, written 2026-11-27 from
`ATTIC/COLL-INPROGRESS/COLL-STAGE-4.md`): merged into `develop`, and
released as the development version 0.3.1 the same day, together with a fix
to `spack_config` found by the Cloud Sandbox's stage 12; withdrawn
2026-11-18; its work is in 0.0.1, the first release (see `CHANGELOG.md`).
The source names `just test` and `just full-test` as its acceptance and
records the work as done; it does not quote their output.

**Input**: A finding of the Cloud Sandbox's move to 0.3.0 (collection stage 3,
2026-11-14), made in its container test: Ansible refuses a task that is both
asynchronous and in check mode ("check mode and async cannot be used on same
task"). A `spack_env` task that builds wants `async`, since a build takes
hours, and the module claims check mode. Its notes said only "Run the task
with `async` and `poll`", and its example and the README's did exactly that:
copied as they were, a playbook could not be previewed.

## Clarifications

### Session 2026-11-14

- Q: The release: cut 0.3.1 and push it, so that the documentation people
  read is the released one (the default offered), or keep the change on
  `develop` until the next change that needs a release? → A: Keep it on
  `develop`. No tag; the version stayed 0.3.0 in `galaxy.yml`, and the
  changelog named the change "Unreleased (to be 0.3.1)".
- Q: The Cloud Sandbox's pin: leave it at 0.3.0 (the default offered: nothing
  it runs changes, and its role already uses the form), or move it to 0.3.1,
  which is one line in each of `sandbox-provisioning/requirements.yml` and
  `exportit/cloud-sandbox/units.toml` and a container run? → A: Move it to
  0.3.1.
- Q: (Asked again, because the first two answers cannot both hold: the
  sandbox installs the collection from a tag, and keeping the change on
  `develop` means there is no 0.3.1 tag.) Tag 0.3.1 now so that the pin can
  move, or tag nothing now and move the pin later? → A: No tag now; the pin
  moves when 0.3.1 is cut. That was to be the first thing done at the release
  that followed: tag 0.3.1, move the two files to it, and run the sandbox's
  container test.
- Q: (Later the same day, after the Cloud Sandbox's stage 12 found a defect
  in `spack_config`.) Fix it here and release it? → A: Fix it, release the fix
  and this change together as 0.3.1, and move the sandbox's pin to 0.3.1 in
  that stage. (The source records the answer, not the question's words.)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A playbook that builds can be previewed (Priority: P1)

A site copies `spack_env`'s example, or the README's, into its playbook. The
task builds an environment, which takes hours, so it runs under `async`. The
site runs the playbook with `--check` to see what it would do. The preview
runs, builds nothing, and says what would change. Run for real, the same task
builds under `async` as before.

**Why this priority**: it is the whole of the change. The module supports
check mode (constitution, principle II), and a site that follows its own
documentation could not use it.

**Independent Test**: run a play holding the documented task with `--check`
against the stand-in `spack`, and see it pass with nothing installed; run it
without `--check` and see it install.

**Acceptance Scenarios**:

1. **Given** a play with a `spack_env` task written as the documentation
   writes it, **When** it is run with `--check`, **Then** it succeeds, Ansible
   does not refuse it, and nothing is installed and no `spack.lock` is
   written.
2. **Given** the same play, **When** it is run without `--check`, **Then** the
   environment is installed.
3. **Given** the same task with `async` and `poll` as plain numbers, **When**
   it is run with `--check`, **Then** it fails with Ansible's own message,
   "check mode and async cannot be used on same task". (This is why the form
   is needed; the test keeps that reason true.)

---

### User Story 2 - The documentation stays previewable (Priority: P2)

Someone later edits an example, or adds one, and writes `async: 86400`. A
test fails and says where.

**Why this priority**: without it, the next edit can bring the problem back
without anyone noticing, as the first version did.

**Independent Test**: put `async: 86400` in the README's example and see the
unit test fail, naming the file.

**Acceptance Scenarios**:

1. **Given** `spack_env`'s `DOCUMENTATION`, **When** its notes are read,
   **Then** they quote Ansible's message and give the form for both `async`
   and `poll`.
2. **Given** `spack_env`'s `EXAMPLES`, `README.md` and `roles/setup/README.md`,
   **When** any of them gives `async:` or `poll:` as a plain number, **Then**
   the unit test fails and names the file.
3. **Given** `spack_env`'s `EXAMPLES`, **When** it is read, **Then** it holds
   the form for `async` and for `poll`.

---

### User Story 3 - The README's examples belong to no site (Priority: P3)

Someone reading the README sees examples they can adapt, with neutral paths
and names, not those of one site.

**Why this priority**: found while changing the examples, and small. The
README's two examples used one site's paths and names; the test for site
knowledge looks only at `plugins/` and `roles/`, so nothing had caught it.

**Independent Test**: read the README's examples and find no name of the
Cloud Sandbox's configuration (`docs/examples/cloud-sandbox.yml`) in them.

**Acceptance Scenarios**:

1. **Given** the README's examples, **When** they are read, **Then** their
   paths, mirror and environment names are placeholders any site could use
   (`/opt/spack-environments/base`, `site-cache`, `mycompiler_environment`).

---

### Edge Cases

- **A plain number in check mode:** Ansible refuses the task before the
  module runs, with "check mode and async cannot be used on same task"
  (research R1). The module cannot prevent this; only the way the task is
  written can.
- **`async` of 0:** the task runs as an ordinary task; Ansible does not
  consult `poll` (research R1). `poll` is written in the same form all the
  same, so that the two keywords read as a pair and neither is left as a
  plain number.
- **The length of a preview:** in check mode `spack_env` concretizes a copy of
  the environment and installs nothing, so the preview needs no `async`. The
  numbers in the form (86400 seconds, 60 seconds) are the examples', not a
  rule; a site sets its own.
- **A task that sets `check_mode: true` itself**, rather than a play run with
  `--check`: not tried in this work. `spack_env`'s own check-mode example
  sets `check_mode: true` and has no `async`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `spack_env`'s notes MUST say that Ansible refuses a task that is
  both asynchronous and in check mode, quoting Ansible's message.
- **FR-002**: The notes MUST give the form that previews:
  `async: "{{ 0 if ansible_check_mode else 86400 }}"` and
  `poll: "{{ 0 if ansible_check_mode else 60 }}"`, with the reason: a preview
  builds nothing and is over in a minute, so it does not need `async`.
- **FR-003**: `spack_env`'s `EXAMPLES` and the README's example MUST use that
  form.
- **FR-004**: A unit test MUST fail when any of `spack_env`'s `EXAMPLES`,
  `README.md` or `roles/setup/README.md` gives `async:` or `poll:` as a plain
  number, and when the notes or `EXAMPLES` lack the form.
- **FR-005**: A unit test MUST run the form through `ansible-playbook`
  against the stand-in `spack`: with `--check` it passes and builds nothing;
  without, it builds; and the same task with plain numbers fails in check
  mode with Ansible's message.
- **FR-006**: The README's examples MUST use no site's paths and names.
- **FR-007**: No module's behaviour changes.
- **FR-008**: `CHANGELOG.md` MUST record the change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A play copied from `spack_env`'s example or the README's runs
  with `--check` without being refused, and builds nothing.
- **SC-002**: The same play, run without `--check`, builds.
- **SC-003**: Every example the test reads that gives `async` or `poll` uses
  the form, and an example with a plain number fails the unit tests.
- **SC-004**: `ansible-doc infrastructurebuilder.csis_spack.spack_env` shows
  the note.

## Assumptions

- The form is the site's to write: Ansible decides about `async` before the
  module runs, so nothing in the module can make a plain number previewable.
- The constitution, ratified later (2026-11-17), now carries this rule in
  principle II: every example gives `async` and `poll` in the form that
  previews.
- The test reads three texts: `spack_env`'s `EXAMPLES`, `README.md` and
  `roles/setup/README.md`. It does not read `docs/examples/` or the other
  modules' `EXAMPLES`; none of them gives `async` today.
- It depended on nothing and nothing waited for it. Of the work that
  remained on 2026-11-14 (the order was kept in the Cloud Sandbox's own plan),
  it was done first because it was the smallest.
- **The release and the pin, as history.** The source's instruction for the
  release that followed, "tag 0.3.1, then move
  `sandbox-provisioning/requirements.yml` and
  `exportit/cloud-sandbox/units.toml` to it, and run the container test", was
  carried out on 2026-11-14, and is superseded. On 2026-11-18 the development
  versions 0.1.0 to 0.3.1 were withdrawn and their tags deleted
  ([specs/001-galaxy-publish/](../001-galaxy-publish/spec.md), Assumptions);
  the first release became 0.0.1, and the Cloud Sandbox now installs the
  collection from Ansible Galaxy by a range (`>=0.0.1,<0.1.0`, spec 001,
  Outcome). Nothing in this spec is still to be done.
- **The fix released with it.** 0.3.1's tag message was "removing a setting
  removes the mapping it empties; async with check mode documented" (spec
  001, Assumptions). The Cloud Sandbox's stage 12 found that Spack v1.2.0,
  when the last key of a mapping is removed, leaves the mapping behind,
  empty (`install_tree: {}`), at every level; `spack_config` had assumed the
  opposite. Since then `spack_config` with `state: absent` removes the
  highest mapping a removal would empty. This is recorded in `CHANGELOG.md`
  (0.0.1), in the comment above `plan_absent` in
  [plugins/module_utils/spack.py](../../plugins/module_utils/spack.py), and
  in tests in [tests/unit/test_spack_config.py](../../tests/unit/test_spack_config.py)
  and [tests/integration/test_real_setup.py](../../tests/integration/test_real_setup.py).
  The fix was not planned in the source of this spec, which names it only;
  its requirements are not this spec's.

## Out of Scope

- Any change to what a module does.
- Moving the Cloud Sandbox's pin: that is the Cloud Sandbox's work, in its
  own repository, and has since been replaced by its install from Galaxy.

## Outcome

- `spack_env`'s notes say why `async` and check mode cannot go together and
  give the form; its example and the README's use it. `ansible-doc` shows the
  note.
- The README's two examples are neutral.
- [tests/unit/test_async_and_check_mode.py](../../tests/unit/test_async_and_check_mode.py)
  holds the notes and the examples to the form, and shows against the
  stand-in `spack` that the form previews without building, builds when not
  previewing, and that a plain number fails in check mode with Ansible's own
  message.
- Released as 0.3.1 on 2026-11-14 with the `spack_config` fix; the Cloud
  Sandbox's pin moved to it. 0.3.1 was withdrawn on 2026-11-18, and
  everything it held is in 0.0.1 (`CHANGELOG.md`, 0.0.1, "Building an
  environment").
