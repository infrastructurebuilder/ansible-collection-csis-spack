---

description: "Task list (a record) for setting Spack up from one piece of configuration"
---

# Tasks: Set Spack up from one piece of configuration

**Input**: Design documents from `/specs/009-setup-role/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/interface.md](contracts/interface.md)

**A record, not a plan.** This work was planned and done on 2026-11-14,
before this repository used Spec Kit. These tasks were written on
2026-11-27 from the stage plan it was carried out from, to record what was
done and in what order. Every task is ticked because it was done then; none
is to be done again. The file paths are those of the code as it is now,
where the work lives.

**Tests**: included; the plan asked for them (spec, SC-005). Within each
story the tests are listed before the code, in the template's order; the
stage plan does not record which was written first.

**Branch**: `feature/coll-stage-2`, from `develop`. Merged into `develop`,
released and pushed on the operator's word.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: could run in parallel (different files, no dependency on an
  unfinished task)
- **[Story]**: the user story the task belongs to (US1 to US5)

---

## Phase 1: Setup — the plan and its decisions

- [X] T001 Plan the stage, then revise it at the operator's request so that the collection prescribes nothing about what is installed: drop the list of workflows, one per kind of compiler, for one list of steps a site writes; record the revision in `specs/009-setup-role/spec.md` (Clarifications)
- [X] T002 Ask the operator the four decisions one at a time (the plain command kind, the shape of the configuration, environments, the version) and record each answer in `specs/009-setup-role/spec.md` (Clarifications)
- [X] T003 Start `feature/coll-stage-2` from `develop` on the operator's "do coll 2"

---

## Phase 2: Foundational — what Spack does, the shared code, the stand-in

**Purpose**: Principle III's practice, before it was a principle: what the
modules rely on is tried first, and the stand-in follows it.

- [X] T004 Read Spack v1.2.0's `--help` for `config`, `compiler`, `external`, `mirror`, `gpg` and `buildcache keys`, and the order of its scopes; record it in `specs/009-setup-role/research.md` (R1 to R6)
- [X] T005 Try configuration against the real Spack v1.2.0 on the local machine: `config add -f` with one and two sections, a list added over a list, `config remove` of a missing path and of a mapping's last key, a value of the wrong type; record it in `specs/009-setup-role/research.md` (R7 to R10)
- [X] T006 Try mirrors and keys against the real Spack v1.2.0: a mirror added with and without flags, a name added twice, `gpg trust` of a key and of a file with no key, `gpg list --trusted --fmt keys` and `--fmt colons`, a keyring deep in a temporary directory; record it in `specs/009-setup-role/research.md` (R12 to R15)
- [X] T007 Try detection with the real oneAPI in the Cloud Sandbox's test container (AlmaLinux 10, oneAPI 2024.2.1 from dnf, Spack v1.2.0): `compiler find` with and without the Intel modules, `external find` for MKL and MPI by name and with `--all`, the order `packages.yaml` is written back in, `compiler remove`; record it in `specs/009-setup-role/research.md` (R16 to R19)
- [X] T008 Run the sandbox's own `config add` lines and see where they write; record it in `specs/009-setup-role/research.md` (R20)
- [X] T009 Write the shared code in `plugins/module_utils/spack.py`: the `Spack` runner (arguments as a list, never a shell; `spack --version` and the floor of 1.0), `Configuration` (`get` through `config get --json`, `add` through one JSON file per section, `remove`), the planning functions (`plan_merge`, `plan_replace`, `plan_absent`, `merged`, `nest`, `without`, `path_text`) and the readers (`fingerprints`, `external_specs`, `satisfies`, `mirror_record`, `scope_args`), with tests in `tests/unit/test_module_utils.py`
- [X] T010 Extend the stand-in `spack` in `tests/unit/fake_spack_setup.py` (called from `tests/unit/fake_spack.py`) to keep configuration per scope, mirrors, trusted keys, and a "machine" of compilers and externals a test can change between runs, each seen only in the environment or the paths it needs; make it behave as T005 to T008 found: one section per file, lists merged, a missing path removed without error, a bare-URL mirror, detection that only adds and reorders `packages`, `gpg trust` exiting 0 for a file with no key

**Checkpoint**: the modules can be written to what Spack does, and tested
against a stand-in that does the same.

---

## Phase 3: User Story 4 — each kind is a module usable on its own (Priority: P3, built first)

**Goal**: the six modules (FR-001 to FR-007). The role in Phase 4 is built
on them, so they come first, although US1 is the priority.

**Independent Test**: each module as a single task, twice, and in check mode.

### Tests for User Story 4

- [X] T011 [P] [US4] Write `tests/unit/test_spack_config.py`: settings written to the site scope and named; a second run writes nothing; one file per section; a changed list set exactly; an external whose version changed corrected; `merge` leaving other keys; `replace` making a section exact; `absent` removing only what is named; another scope; check mode naming the paths and writing nothing; a value Spack refuses leaving the scope as it was; a section that is not a mapping and a key with a colon refused; a Spack below 1.0 refused; a scope not made yet read as empty and written
- [X] T012 [P] [US4] Write `tests/unit/test_spack_mirror.py`: a missing mirror added; a second run changes nothing; a changed URL corrected; `type` and `signed` reaching Spack and compared; properties not given not compared; a bare mirror holding both kinds; `absent` removing it once; `present` needing a URL; check mode saying what it would do and doing nothing; another scope
- [X] T013 [P] [US4] Write `tests/unit/test_spack_gpg_key.py`: a key file trusted and its fingerprint reported; a second run not asking Spack to trust again; with a fingerprint, a trusted key not read; a fingerprint with spaces and in lower case; a file holding another key refused; a file holding no key refused though Spack would exit 0; a missing file and a bad fingerprint refused; one of `key` and `from_mirrors` needed; the mirrors' keys trusted; `from_mirrors` with no binary mirror failing as Spack does; check mode for a key file and for `from_mirrors`
- [X] T014 [P] [US4] Write `tests/unit/test_spack_detect.py`: compilers on the path recorded in the site scope; a second run reporting no change though Spack reorders the section; `externals: true` and a list of names; `not_buildable`, `exclude` and `paths` reaching Spack; what is only seen in an environment found with it; `require` failing without the environment, passing with it and with a more exact version, not met by another version, and looking in every scope; detection never removing what it no longer sees (the removed-compiler accident, reproduced and caught); check mode running nothing; something must be looked for; `externals` taking true, false or names
- [X] T015 [P] [US4] Write `tests/unit/test_spack_command.py`: `changes: config` reporting a change only when the named sections of the scope differ; `always` and `never`; `creates` running only while the path is missing and required with `changes: creates`; a command run in a Spack environment (`env`); a failing command failing with its output; check mode not running and reporting a possible change
- [X] T016 [P] [US4] Write `tests/unit/test_shell_environment.py`: what the lines set returned and nothing else; a changed variable returned with its new value; a removed variable named; output of the lines not in the way; shell functions and the shell's own variables left out; running in check mode; a failing shell failing the task; a failing line not stopping the rest unless the lines say so; another shell named

### Implementation for User Story 4

- [X] T017 [P] [US4] Write `plugins/modules/spack_config.py` as plan.md "The modules" and contracts/interface.md say, with `DOCUMENTATION`, `EXAMPLES` and `RETURN`
- [X] T018 [P] [US4] Write `plugins/modules/spack_mirror.py`, with its documentation: added when missing, removed and added again when different, removed for `absent`
- [X] T019 [P] [US4] Write `plugins/modules/spack_gpg_key.py`, with its documentation: public keys only, trust told from `gpg list --trusted --fmt colons` before and after
- [X] T020 [P] [US4] Write `plugins/modules/spack_detect.py`, with its documentation: discovery said to be discovery, `require` checked against every scope merged
- [X] T021 [P] [US4] Write `plugins/modules/spack_command.py`, with its documentation: prefer the other modules where they apply
- [X] T022 [P] [US4] Write `plugins/modules/shell_environment.py`, with its documentation: the only module that runs a shell, and only the caller's lines
- [X] T023 [US4] Run `just test`: T011 to T016 pass

**Checkpoint**: every kind can be used as a task on its own.

---

## Phase 4: User Story 1 — a site's set-up script becomes one list of steps (Priority: P1) 🎯 MVP

**Goal**: the role and its filters (FR-008 to FR-014, FR-020).

**Independent Test**: a list of one step of each kind applied, then applied
again with no change.

### Tests for User Story 1

- [X] T024 [P] [US1] Write `tests/unit/test_setup_filter.py`: a good list has no problems; the list must be a list of mappings; an unknown or missing kind named with the step's number; an option of another kind refused; required options asked for; an environment captured before it is named; an environment step cannot itself run in one; every problem reported, not only the first; each kind's options are its module's options; labels
- [X] T025 [P] [US1] Write `tests/unit/test_setup_role.py`: the role's defaults are empty and name no site; with no steps it does nothing; every step carried out in the order written; a second application changes nothing; the results name each step; a bad list refused before anything is changed; a failing step stops the rest; the executable and the default scope are the role's variables; without the variable the role runs `spack` from `PATH`

### Implementation for User Story 1

- [X] T026 [US1] Write `plugins/filter/setup_problems.py`: `KINDS` (each kind's module and its required and optional options), `setup_problems` and `setup_label`, registered by `FilterModule`, with `DOCUMENTATION`, `EXAMPLES` and `RETURN` for `setup_problems`; and `plugins/filter/setup_label.yml` for `setup_label`
- [X] T027 [US1] Write `roles/setup/defaults/main.yml` (`spack_setup: []`, the executable `spack`, `spack_setup_scope: site`) and `roles/setup/meta/main.yml`; do not add `roles/setup/meta/argument_specs.yml`, after seeing ansible-core 2.16.20 warn on every use with one (research R21)
- [X] T028 [US1] Write `roles/setup/tasks/main.yml`: the `assert` on `setup_problems` before any step, the empty environments and results, and the loop over `step.yml` with each step's label and environment
- [X] T029 [US1] Write `roles/setup/tasks/step.yml` (include the kind's file, record the step's entry in `spack_setup_results`) and the five kind files that run Spack: `roles/setup/tasks/kinds/config.yml`, `mirror.yml`, `gpg_key.yml`, `detect.yml`, `command.yml`, each one module call with the step's options and `default(omit)` for those it may leave out
- [X] T030 [US1] Name a step's label `label`, not `name`, in `plugins/filter/setup_problems.py` and the role, since `mirror` and `environment` steps already have a `name`
- [X] T031 [US1] Run `just test`: T024 and T025 pass

**Checkpoint**: a list of steps is carried out in order, and refused whole
when it is wrong.

---

## Phase 5: User Story 2 — a detection that ran without its environment fails (Priority: P1)

**Goal**: the `environment` kind and the two forms of a step's environment
(FR-013).

- [X] T032 [US2] In `tests/unit/test_setup_role.py`, add: a captured environment reaches only the steps that name it; a step may give its environment as a mapping
- [X] T033 [US2] Write `roles/setup/tasks/kinds/environment.yml`: run `shell_environment` with the step's `shell` and `executable`, and keep its `environment` under the step's `name` in `spack_setup_environments`
- [X] T034 [US2] In `roles/setup/tasks/main.yml`, give each step the environment it names: none, a mapping as given, or a captured one by name
- [X] T035 [US2] Run `just test`: T032's tests pass

---

## Phase 6: User Story 3 — check mode previews what is declared (Priority: P2)

- [X] T036 [US3] In `tests/unit/test_setup_role.py`, add a test that check mode previews what is declared, runs no discovery, and changes nothing in the stand-in's scopes or keys
- [X] T037 [US3] Run `just test`: it passes, from the modules' own check mode (T017 to T022)

---

## Phase 7: User Story 5 — the collection carries no site's choices (Priority: P2)

**Goal**: the examples, held by tests, and the test for site knowledge
(FR-015 to FR-018).

- [X] T038 [P] [US5] Write the seven examples, the sandbox's with its own names and the rest with neutral ones: `docs/examples/system-compiler.yml`, `compiler-in-environment-modules.yml`, `compiler-built-by-spack.yml`, `compiler-toolset.yml`, `unwanted-compilers.yml`, `site-mirror-with-key.yml`, and `cloud-sandbox.yml` (two lists, `spack_setup_base` and `spack_setup_intel`; `scope: user` on its settings step, research R20; its oneAPI MKL and MPI declared, research R18)
- [X] T039 [US5] Write `tests/unit/test_examples.py`: every example is a list that `setup_problems` accepts; there is one for each situation the plan names; each is carried out against a stand-in machine made for it and does what its comments say
- [X] T040 [US5] In `tests/unit/test_examples.py`, hold the sandbox's example to its shell: run the sandbox's own Spack commands against a second stand-in and require the same scopes, the same trusted keys, and the discovery commands in the same order, and a second application of both lists changing nothing; and see its second list fail, naming the Intel compiler, when its environment is not loaded
- [X] T041 [US5] Write `tests/unit/test_no_site_knowledge.py`: take every package, mirror, path and module name out of `docs/examples/cloud-sandbox.yml` and fail if one is in a `.py`, `.yml`, `.md` or `.j2` file of `plugins/` or `roles/`; run it, and remove the one site name it caught on its first run
- [X] T042 [US5] Make the examples in the documentation of `plugins/modules/spack_env.py` and `plugins/modules/spack_buildcache_push.py` neutral, which T041's test now covers

---

## Phase 8: Polish, acceptance and the release

- [X] T043 [P] Write `roles/setup/README.md`: the three variables, a step, the kinds and their options, what the role does with the list, declared and discovered, the examples
- [X] T044 [P] In `README.md`, describe the role and the six modules under "Setting a Spack up", and the principle at the top
- [X] T045 [P] Record 0.3.0 in `CHANGELOG.md` (its content is now under 0.0.1)
- [X] T046 Write `tests/integration/test_real_setup.py`: a list of every kind through the role against the real Spack v1.2.0, in a user scope and a keyring of the test's own (a short path, research R15): check mode writes nothing; the first application changes, the second does not; a list set exactly; a changed mirror corrected; `absent` removing only what is named; a value Spack's schema refuses failing with the scope as it was. Make `Configuration.get` in `plugins/module_utils/spack.py` read a scope with no directory as empty, which this test found (research R11)
- [X] T047 Run `just test` (193 tests, two to three minutes) and see it pass
- [X] T048 Run `just full-test` (the integration tests against the real Spack v1.2.0, and `ansible-test sanity`) and see it pass
- [X] T049 Check the acceptance of the plan: the role's defaults empty and the test for site knowledge passing (SC-001); the sandbox's example against its shell (SC-002); against the real Spack v1.2.0, the first example applied twice changing nothing the second time, and check mode before the first run naming every declared change and making none (SC-003)
- [X] T050 Merge `feature/coll-stage-2` into `develop` on the operator's word
- [X] T051 Build the 0.3.0 tarball; in the Cloud Sandbox's test container, with the real oneAPI, dump and wipe what the sandbox's shell had written to the site and user scopes, apply `docs/examples/cloud-sandbox.yml`'s two lists through the role from that tarball, and see 7 changes, then 0, then 0 in check mode, and the scopes the same as the shell's as data but for an `id` on three compiler entries from an earlier `spack compiler remove` (spec, SC-004; research R19)
- [X] T052 Release 0.3.0 and push it, on the operator's word (withdrawn 2026-11-18, with every development version; its content is in 0.0.1, `CHANGELOG.md`)

---

## Dependencies & Execution Order

- **Phase 1** first; **Phase 2** (T004–T010) before any module: the
  research is what the modules and the stand-in are written to.
- **Phase 3** (the modules) before **Phase 4** (the role), which calls them.
- **Phases 5 to 7** after Phase 4. Phase 7's test for site knowledge (T041)
  needs the sandbox's example (T038).
- **Phase 8** last. T046's finding (R11) changed the shared code after the
  modules were written.
- The stage plan records the merge (T050), the trial with the real oneAPI
  (T051) and the release (T052), but not the order of the last two; the
  trial was made from the built 0.3.0 tarball.

## Notes

- Later specs changed this work: 002 renamed the executable's variable; 003
  added `yes_to_all` and support for Spack 1.0 and 1.1; 004 added the
  `spack` kind; 005 gave it `move`. 0.3.1
  ([spec 011](../011-preview-long-builds/spec.md)) corrected research R9.
  None of that is a task here.
