# Implementation Plan: Set Spack up from one piece of configuration

**Branch**: `feature/coll-stage-2`, until the history was reset on 2026-11-18 | **Date**: 2026-11-14 (written 2026-11-27, retrospectively) | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/009-setup-role/spec.md`

## Summary

Six modules, one per kind of step, each usable on its own: `spack_config`
(settings in a scope), `spack_mirror` (one mirror), `spack_gpg_key` (public
keys), `spack_detect` (compiler and package discovery), `spack_command`
(any Spack command, with a stated rule for change) and `shell_environment`
(the environment some shell lines produce). Their shared code is in
`plugins/module_utils/spack.py`. A role, `setup`, carries out one variable,
`spack_setup`, an ordered list of steps, with one module call per kind; its
defaults are empty. Two filters serve the role: `setup_problems`, the check
of the whole list before any step runs, and `setup_label`. Seven examples
under `docs/examples/` are carried out by the tests, and a test holds the
plugins and the role to carrying no site's names.

What was tried first against the real Spack v1.2.0, and in the Cloud
Sandbox's container with the real oneAPI, is in [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12 (the modules, the filters, the tests);
YAML and Jinja2 (the role)

**Primary Dependencies**: ansible-core 2.16 (2.16.20 at the time); Spack
v1.2.0 on the managed node; `gpg` on the node, optionally, to read a key
file's fingerprint

**Storage**: N/A. The modules keep nothing of their own; what they change is
Spack's configuration scopes and its keyring.

**Testing**: pytest through `just test`: 193 unit tests, each running the
modules or the role through `ansible` and `ansible-playbook` against the
stand-in `spack`, extended to keep configuration per scope, mirrors,
trusted keys, and a "machine" of compilers and packages a test can change
between runs. `just full-test`: the integration tests against the real Spack
v1.2.0 on the local machine, in a user scope and a keyring of the test's
own, and `ansible-test sanity`.

**Target Platform**: the managed node (Linux; EL 10 in the role's
`meta/main.yml`); the local machine for the tests

**Project Type**: an Ansible collection; this adds six modules, a role and
two filters

**Performance Goals**: N/A. `just test` takes two to three minutes.

**Constraints**: no module runs Spack through a shell; configuration is read
and written only through `spack config`; the role and the plugins name
nothing of any site

**Scale/Scope**: 6 modules and their shared code; 1 role (defaults, meta,
`main.yml`, `step.yml`, 6 kind files, README); 2 filters; 7 examples; unit
tests for each module, the filters, the role, the examples and the absence
of site knowledge; integration tests through the role

## Constitution Check

*The constitution was ratified on 2026-11-17, three days after this work.
The check is made after the fact, against version 1.0.1.*

| Principle | Check | Result |
| --- | --- | --- |
| I. A Site's Choices Are Configuration, Not Code | This work is where the principle comes from: its "principle" ("the collection knows how to do each kind of thing to Spack, and nothing about what any site wants done") became Principle I. The role's list is empty by default; a site's choices are in `docs/examples/` and in tests only; `tests/unit/test_no_site_knowledge.py`, which Principle I names, was written here. | Pass |
| II. A Repeat Run Changes Nothing, and Says So | Each module reports a change only when it made one, told from Spack's own data before and after (R1, R13, R17); a second application is held to no change by unit and integration tests. Every module supports check mode: declared state is previewed exactly, discovery and `from_mirrors` say they cannot be (`previewed: false`), a command is not run. `changes: always` is documented as a change on every run. No module here builds for hours, so `async` does not arise. | Pass |
| III. Written to What Spack Does | Configuration through `config get --json`, `config add -f` and `config remove`, replacing `spack python -c` (R1, R2); keys read with `gpg list --fmt colons` (R14). No module runs Spack through a shell. `shell_environment` runs a shell, but only the site's own lines, never Spack; that is the decision recorded in the spec's Clarifications. The behaviour relied on was tried against the real Spack v1.2.0, and in the sandbox's container for oneAPI, before the modules were written, and the stand-in follows what was found (R16, R17), not the sandbox's own account. One finding was wrong (R9) and was corrected in 0.3.1. | Pass |
| IV. Acceptance Tests Run Through the Justfile | `just test` (lint, type-check, the unit tests, a build) and `just full-test` (integration against the real Spack, `ansible-test sanity`) passed. Every option of every kind, change both ways, check mode and failure have unit tests; the claims about the real Spack have integration tests; every example is carried out by the tests. (`just full-test` did not yet include Galaxy's import checks; spec 001 added them.) | Pass |
| V. The Operator Decides | The revision and the four decisions were asked of the operator one at a time and recorded (spec, Clarifications). Merging, pushing and the release of 0.3.0 each waited for the operator's word. | Pass |
| The ATTIC | This retrospective was written from `ATTIC/COLL-INPROGRESS/COLL-STAGE-2.md` on the operator's explicit permission, for this task only. The spec stands without it. | Pass |

No violations; Complexity Tracking is not needed.

## Design, as built

### The modules

Each is a file under `plugins/modules/`, with `DOCUMENTATION`, `EXAMPLES`
and `RETURN`. The options and what each runs are in
[contracts/interface.md](contracts/interface.md).

- **`spack_config`**: for each section given, read the scope's section as
  data (R1), plan the change (`plan_merge`, `plan_replace` or, for
  `absent`, the paths named), remove the paths whose value differs, add the
  rest in one file per section (R7, R8), then read the section back and fail
  if it is not what was intended. A refusal by Spack's schema puts back what
  was removed (R10). Returns the paths changed; diff mode shows the sections
  before and after.
- **`spack_mirror`**: read the scope's `mirrors`; compare only the
  properties given (R12); `mirror add` when missing, `mirror remove` then
  `mirror add` when different, `mirror remove` for `absent`; read it back.
- **`spack_gpg_key`**: read the trusted fingerprints before; for a key, fetch
  it if it is a URL, read its fingerprint with `gpg` where there is one,
  refuse a file with no key or another key, and trust it unless it is
  trusted already; for `from_mirrors`, run `buildcache keys --install
  --trust`; read the trusted fingerprints after, and fail if an expected one
  is missing (R13).
- **`spack_detect`**: read the scope's `packages`; run the detections;
  read it again, and compare as data (R17); then check `require` against
  every scope merged. Check mode runs nothing (R16).
- **`spack_command`**: for `changes: config`, read the named sections of the
  scope before and after; for `creates`, do nothing while the path exists.
  Check mode runs nothing.
- **`shell_environment`**: run the lines, then print the environment as
  JSON after a marker, with the Python that runs the module; return what
  differs from the module's own environment.

**Shared code**, `plugins/module_utils/spack.py`: the `Spack` runner (an
argument list to `run_command`, never a shell; the version check), the
`Configuration` class (one scope: `get`, which reads a scope with no
directory as empty (R11), `add`, `remove`), the planning functions
(`plan_merge`, `plan_replace`, `plan_absent`, `merged`, `nest`, `without`),
and the readers (`fingerprints`, `external_specs`, `satisfies`,
`mirror_record`). Spack's Python internals are never imported.

### The role

- `roles/setup/defaults/main.yml`: `spack_setup: []`, the executable
  (`spack`), `spack_setup_scope: site`.
- `roles/setup/tasks/main.yml`: first, an `assert` that
  `spack_setup | setup_problems` is empty, naming every problem; then an
  empty map of captured environments and an empty list of results; then
  `step.yml` for each step, in order, with the step's environment worked out
  (none, a mapping, or a captured one by name) and its label.
- `roles/setup/tasks/step.yml`: include `kinds/<kind>.yml`, then add the
  step's entry to `spack_setup_results`.
- `roles/setup/tasks/kinds/<kind>.yml`: the one module call of each kind,
  each option taken from the step, `default(omit)` where the step may leave
  it out, and `scope` defaulting to `spack_setup_scope`. The `environment`
  kind's file also keeps the result under the step's `name`.
- `roles/setup/meta/main.yml`: Galaxy information only; no
  `meta/argument_specs.yml` (R21).

### The filters, `plugins/filter/setup_problems.py`

One file holds the table of kinds (`KINDS`: each kind's module, and its
required and optional options), `setup_problems` and `setup_label`, both
registered by its `FilterModule`. `setup_label`'s documentation is in
`plugins/filter/setup_label.yml`.

### What changed from the plan while building

- **A step's label is `label`, not `name`.** A `mirror` step and an
  `environment` step already have a `name` with another meaning.
- **`mode: replace` works a key of a section at a time**: a key that is not
  given, or differs, is removed, and the given ones are added. (The plan
  said each section named becomes exactly what is given; this is how.)
- **A step's `environment` may also be a mapping of variables**, as well as
  the name of a captured one. This is the alternative weighed in the
  decision on environments, kept beside the `environment` kind; the plan
  records no further reason.
- **No `meta/argument_specs.yml` for the role.** With one, ansible-core
  2.16.20 prints a deprecation warning of its own on every use (its implicit
  validation task uses a form of `action` that the same release
  deprecates). The role's own first task checks the list instead, and the
  role's README documents its three variables.
- **The examples in the documentation of 0.1.0's two modules**
  (`spack_env`, `spack_buildcache_push`) used the sandbox's paths and names;
  they were made neutral, and the test for site knowledge covers them.
- **`just test` takes two to three minutes**, not one: 193 tests, each
  running Ansible.
- **A different mirror is removed and added again**, where the plan said
  `mirror set` (research R4). The plan does not record why.
- **The sandbox's example has two variables**, `spack_setup_base` and
  `spack_setup_intel`, for its two lists, and its settings step says
  `scope: user` (research R20). The plan wrote both lists as `spack_setup`.

### Tests

- **Unit**, against the stand-in `spack` (`tests/unit/fake_spack.py`,
  `tests/unit/fake_spack_setup.py`, run through `tests/unit/runner.py` and
  `tests/unit/conftest.py`): one file per module; `test_setup_filter.py`;
  `test_setup_role.py` (the order, a second application, the results, the
  environments, a bad list refused before anything changes, a failing step
  stopping the rest, check mode, the defaults empty); `test_examples.py`
  (each example, on a machine made for it; the sandbox's example against
  its shell, on a second stand-in; the sandbox's second list failing loudly
  without its environment); `test_no_site_knowledge.py`.
- **Integration**, against the real Spack v1.2.0
  (`tests/integration/test_real_setup.py`): a list of every kind through the
  role, in a user scope and a keyring of the test's own: check mode writes
  nothing; the first application changes, the second does not; a list is
  set exactly; a changed mirror is corrected; `absent` removes only what is
  named; a value Spack's schema refuses fails and leaves the scope as it
  was. Its mirror is a directory. The plan said "a key generated for the
  test"; as released in 0.0.1 the key is a throwaway public key kept for
  the tests (`tests/fixtures/throwaway-mirror-key.pub`).
- **With the real oneAPI**, by hand, in the Cloud Sandbox's container: what
  the sandbox's shell had written to the site and user scopes was dumped and
  wiped, and the example's two lists were applied through the role from the
  built 0.3.0 tarball (spec, SC-004). Not a kept test; the sandbox's own
  container test holds it since the sandbox adopted the role.

### Documentation

- Each module's `DOCUMENTATION`, `EXAMPLES` and `RETURN`.
- `roles/setup/README.md`: the variables, a step, the kinds and their
  options, what the role does with the list, declared and discovered, the
  examples.
- `README.md`: "Setting a Spack up", with the modules.
- `CHANGELOG.md`: 0.3.0. (Since the withdrawal of 2026-11-18 its content is
  under 0.0.1, "Setting a Spack up".)

## Project Structure

### Documentation (this feature)

```text
specs/009-setup-role/
├── spec.md
├── plan.md              # This file
├── research.md          # What Spack v1.2.0 does, tried first
├── data-model.md        # The list, a step, the kinds, the results, the examples
├── contracts/
│   └── interface.md     # The role, each kind's options, the filters
├── checklists/
│   └── requirements.md
└── tasks.md             # A record of the work, made after it
```

### Source Code (repository root)

```text
plugins/modules/spack_config.py
plugins/modules/spack_mirror.py
plugins/modules/spack_gpg_key.py
plugins/modules/spack_detect.py
plugins/modules/spack_command.py
plugins/modules/shell_environment.py
plugins/modules/spack_env.py, spack_buildcache_push.py   # 0.1.0's; their examples made neutral
plugins/module_utils/spack.py                            # Spack, Configuration, the planning and reading functions
plugins/filter/setup_problems.py                         # KINDS, setup_problems, setup_label
plugins/filter/setup_label.yml
roles/setup/
├── defaults/main.yml
├── meta/main.yml
├── tasks/main.yml
├── tasks/step.yml
├── tasks/kinds/{config,mirror,gpg_key,detect,command,environment}.yml
└── README.md
docs/examples/
├── system-compiler.yml
├── compiler-in-environment-modules.yml
├── compiler-built-by-spack.yml
├── compiler-toolset.yml
├── unwanted-compilers.yml
├── site-mirror-with-key.yml
└── cloud-sandbox.yml
tests/unit/
├── fake_spack.py, fake_spack_setup.py, runner.py, conftest.py
├── test_spack_config.py, test_spack_mirror.py, test_spack_gpg_key.py,
│   test_spack_detect.py, test_spack_command.py, test_shell_environment.py
├── test_module_utils.py
├── test_setup_filter.py, test_setup_role.py
├── test_examples.py
└── test_no_site_knowledge.py
tests/integration/test_real_setup.py
tests/fixtures/throwaway-mirror-key.pub
README.md, CHANGELOG.md
```

**Structure Decision**: the collection's existing layout. The role is the
collection's first, under `roles/setup/`; the filters are in one file under
`plugins/filter/`. Later specs added to these files:
`plugins/modules/spack_checkout.py`, `roles/setup/tasks/kinds/spack.yml`,
`plugins/filter/setup_executable.yml` and
`docs/examples/spack-installed-by-the-role.yml` (spec 004), and changed
others (specs 002, 003, 005); this spec's list is of what it made.
