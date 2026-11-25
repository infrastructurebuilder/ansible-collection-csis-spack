# Implementation Plan: `spack_gpg_key` trusts the mirrors' keys without a prompt

**Branch**: `feature/mirror-keys-yes-to-all` | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-mirror-keys-yes-to-all/spec.md`

## Summary

Spack 1.2 asks `Trust key: … [y/N]` for every key that `gpg trust` and
`buildcache keys --trust` handle, and fails under Ansible, which gives it no
terminal. Spack 1.0 and 1.1 never ask, and reject `-y`. So:

- `spack_gpg_key` passes `--yes-to-all` to both of its trust commands where
  the installed Spack's help lists it, and leaves it out where it does not.
  That fixes the head node's `from_mirrors` failure on 1.2, and the released
  defect that a key file cannot be trusted on 1.0 and 1.1.
- Every module that runs Spack gains `yes_to_all` (default off), and the
  `setup` role gains `spack_setup_yes_to_all` with a per-step override. When
  it is on, a command that changes something is given `--yes-to-all` where its
  help lists it.

Both rest on one check in the shared code: read `spack <command> --help`, and
add the option only when it is listed ([research.md](research.md), R1 to R5).

## Technical Context

**Language/Version**: Python 3.12 (modules, module_utils, tests); YAML and
Jinja2 (the role)

**Primary Dependencies**: ansible-core 2.16; Spack 1.0 or later on the node

**Storage**: N/A

**Testing**: pytest through `just test` (unit tests against the stand-in
`spack`); `just full-test` (integration against the real Spack v1.2.0,
`ansible-test sanity`, Galaxy's import checks)

**Target Platform**: the managed node, as today (Linux; the local machine for
the tests)

**Project Type**: an Ansible collection; this changes seven modules' options,
one module's commands, the shared runner and one role's interface

**Performance Goals**: a help call is about 0.9 s on the local machine. With
`yes_to_all` off, no module reads any help; `spack_gpg_key`'s trusts read
none either, since the version table decides (User Story 3). `just full-test`
takes about 45 minutes, the integration tests running once per Spack version

**Constraints**: a playbook written for 0.0.2 runs unchanged and does what it
did, except that the two trust commands now succeed where they failed;
nothing is ever answered on stdin; Spack is never run through a shell

**Scale/Scope**: `plugins/module_utils/spack.py`; 7 modules; the role's
defaults, 5 kind files, its filter and README; the stand-in `spack`; unit
tests; the integration tests, now run against three Spack versions, and 3
new ones; `CHANGELOG.md`; the README

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Result |
| --- | --- | --- |
| I. A Site's Choices Are Configuration, Not Code | `yes_to_all` is a site's choice, given as a module option or a role variable; its default is off. No command list of any site is built in. | Pass |
| II. A Repeat Run Changes Nothing, and Says So | Change reporting is untouched: `spack_gpg_key` still compares `gpg list --trusted` before and after (FR-002); R4 shows a second run trusts nothing new. Check mode runs no command that changes anything; a help call changes nothing. | Pass |
| III. Written to What Spack Does | Tried against the real 1.0.0, 1.1.0 and 1.2.0 before design (R1 to R4), and the integration tests now run against all three (FR-010, R8). The version table holds only what those three did; the help check, for `yes_to_all`, reads Spack's own help. `spack python -c` is used only where 1.0 has no machine-readable command (weighed under "The version table"). The stand-in follows what the real ones printed. The pin stays 1.2.0. | Pass |
| IV. Acceptance Tests Run Through the Justfile | Unit tests first, seen to fail; two integration tests that fail on 0.0.2 (SC-002); `just test` after each change, `just full-test` before done. No new tool is called outside the `Justfile`. | Pass |
| V. The Operator Decides | Six answers are in the spec's Clarifications, one of them changed during planning on the operator's word. The release is 0.0.3 (operator); when to cut it is asked then. Committed locally. | Pass |
| The ATTIC | Not consulted. (`plugins/module_utils/spack.py` has a comment pointing into the ATTIC; it was not followed.) | Pass |

No violations; Complexity Tracking is not needed.

**Re-checked after the design below:** unchanged. One point was weighed under
Principle II: `spack_command` may be given `--yes-to-all` in a real run, but
in check mode it runs nothing, as today, so the flag cannot make a preview
act. Re-checked again on 2026-11-25 after User Story 3's design (the version
table, `spack python -c` on 1.0, the tests on three versions): unchanged.

## Design

### The check, in `plugins/module_utils/spack.py`

`Spack(module, executable, yes_to_all=False)` keeps the flag, and a cache of
the help it has read in this run. One new method, for `yes_to_all`:

```text
answered(args, words=None) -> args
```

- Adds `--yes-to-all` only when `self.yes_to_all`, and the
  arguments have neither `-y` nor `--yes-to-all` already, and the help of the
  command lists the option (the `-y, --yes-to-all` line, R1).
- `words` is how many of `args` are the command (`["gpg", "trust", path]` is
  2). When it is not given (`spack_command`), the words are found by walking
  the help from the first word, R3 and R5. A help is never asked for after a
  word that is not known to be a command.
- The option goes straight after the command's words, before anything else.
- A help that fails counts as "does not take it".

`run()` is unchanged: a module passes `spack.run(spack.answered([...]))` for
each command that changes something, and nothing changes for its queries
(R1: none of them takes the option).

### The version table (User Story 3, added 2026-11-25)

`BEHAVIOUR` in `plugins/module_utils/spack.py`, keyed by (major, minor),
says how each supported Spack does what the collection's own commands rely
on and that differs between versions; a Spack newer than the last row is
read as the last row. Every module already runs `spack --version` first, so
`Spack.does(name)` needs no further call. The rows come from what the real
1.0.0, 1.1.0 and 1.2.0 did (research.md R2, R7, R8):

| Behaviour | 1.0 | 1.1 | 1.2 | Without it |
| --- | --- | --- | --- | --- |
| `config_json` | no | yes | yes | `spack python -c` prints the section as JSON (`spack.config.get`, or `CONFIG.get_config` for one scope) |
| `gpg_colons` | no | no | yes | the fingerprints are read from `gpg list --trusted`'s own listing |
| `trust_answers` | no | no | yes | `gpg trust` and `buildcache keys --trust` run without `--yes-to-all` |

A missing scope is read as empty in 1.2's and 1.1's words; 1.0 prints it
empty. The help check (`answered()`) stays only for `yes_to_all`.

**Constitution, Principle III:** `spack python -c` is Spack's own command,
and prints JSON; but what it runs is Spack's Python API, which the shared
code otherwise does not use. It is used only where Spack 1.0 has no
machine-readable command for the same data, is held by the integration
tests against the real 1.0.0, and goes with the 1.0 row when the floor moves.

### The modules

| Module | Commands answered | How |
| --- | --- | --- |
| `spack_gpg_key` | `gpg trust <file>` (the hard-coded `-y` goes), `buildcache keys --install --trust` | `trusting()`, by the version table, whatever `yes_to_all` says: asking for the key, or for `from_mirrors`, is the consent |
| `spack_env` | `concretize`, `install`, `module <system> refresh` (keeps its own `-y`) | `answered()`, when `yes_to_all` |
| `spack_buildcache_push` | `buildcache push` | the same |
| `spack_mirror` | `mirror add`, `mirror remove` | the same |
| `spack_config` | `config add`, `config remove`, through the shared `Configuration` (words 1: `config`'s help decides) | the same |
| `spack_detect` | `compiler find`, `external find` | the same |
| `spack_command` | the site's `args`, words found by walking | the same |

Each takes `yes_to_all` (bool, default false), passed to `Spack(...)`.
`spack_gpg_key` takes it too, for one shape across the modules, and says that
it changes nothing there. `shell_environment` runs a shell, not Spack, and
does not take it. The option's documentation is written once per module, as
`spack` is today (there are no doc fragments in this collection).

### The role

- `roles/setup/defaults/main.yml`: `spack_setup_yes_to_all: false`.
- `roles/setup/tasks/kinds/{config,mirror,gpg_key,detect,command}.yml`:
  `yes_to_all: "{{ spack_setup_step.yes_to_all | default(spack_setup_yes_to_all) }}"`,
  as `scope` is passed.
- `plugins/filter/setup_problems.py`: `yes_to_all` is an option of those five
  kinds, not of `environment`.
- `roles/setup/README.md`: the variable, the step option, and the warning
  (FR-007).

### The stand-in `spack`

`tests/unit/fake_spack.py` and `fake_spack_setup.py` answer `--help` from
texts as 1.2.0 prints them, for the commands the modules run. Its `version`
state makes it play 1.0 or 1.1 where they differ (User Story 3): no
`--yes-to-all` on the trusts (`unrecognized arguments: -y`, exit 1), no
trust question, no `gpg list --fmt`, no `config get --json` on 1.0 (with
`spack python -c` read as the `config get` it stands for), and 1.1's
refusal of a scope whose directory is missing. `gpg trust`
is accepted with `--yes-to-all`, `-y` or neither. Every call is recorded, so
a test can see which helps were read.

### The integration tests

- `tests/integration/test_real_spack.py`: after the zlib install, two keys
  made with `spack gpg create` in a signing keyring; zlib pushed signed with
  the first, the key index written (`buildcache update-index --keys`, R4);
  the mirror added in a user scope of the test's own; `spack_gpg_key`
  `from_mirrors` into an empty keyring: a change, then none; zlib pushed again
  with `--force` and the second key, the index again; a change for the second
  key only. A third test shows the help check reading the real Spack's help:
  `install` (has it), `mirror add` (has not), `module tcl refresh` (walked
  to), `config --scope user add` (only `config` read).
- `tests/integration/test_real_setup.py`: a fake install and a signed push of
  its own, and one `gpg_key` step of `from_mirrors: true`, run twice; its
  docstring says what it now builds and pushes.

Both fail on 0.0.2 with `EOF when reading a line`, exit 3 (R4, item 2).

## Project Structure

### Documentation (this feature)

```text
specs/003-mirror-keys-yes-to-all/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0: what Spack 1.0, 1.1 and 1.2 do
├── data-model.md        # Phase 1: the flag, its sources, the help cache
├── quickstart.md        # Phase 1: how to see it work
├── contracts/
│   └── interface.md     # Phase 1: options, variable, commands run
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks; not made here)
```

### Source Code (repository root)

```text
plugins/module_utils/spack.py        # Spack(yes_to_all=...), answered(), the help cache
plugins/modules/
├── spack_gpg_key.py                 # both trusts through trusting(), by version; docs (FR-005)
├── spack_env.py                     # yes_to_all; answered()
├── spack_buildcache_push.py         # yes_to_all; answered()
├── spack_mirror.py                  # yes_to_all; answered()
├── spack_config.py                  # yes_to_all; answered() through Configuration
├── spack_detect.py                  # yes_to_all; answered()
└── spack_command.py                 # yes_to_all; answered(), words walked
plugins/filter/setup_problems.py     # yes_to_all allowed on five kinds
roles/setup/
├── defaults/main.yml                # spack_setup_yes_to_all: false
├── tasks/kinds/{command,config,detect,gpg_key,mirror}.yml
└── README.md
tests/unit/
├── fake_spack.py, fake_spack_setup.py   # --help, the 1.0/1.1 behaviour
├── fake_spack_help.json                 # new: help texts as Spack 1.2.0 prints them
├── test_module_utils.py                 # answered()
├── test_spack_gpg_key.py                # new forms (FR-004)
├── test_spack_*.py                      # yes_to_all on and off, per module
├── test_setup_filter.py, test_setup_role.py
tests/integration/test_real_spack.py, test_real_setup.py
CHANGELOG.md                             # Unreleased
```

**Structure Decision**: the collection's existing layout. One file is added
outside `specs/`: `tests/unit/fake_spack_help.json`, the stand-in's help texts,
kept apart because they are long and copied from the real Spack (as data, so
that the help's own long lines are not held to the code's line length).
Two targets are added to the `Justfile` during implementation:
`just integration`, the integration tests alone, so that a new one can be
seen to fail before the change it tests (`full-test` runs `test` first,
which the fix's unit tests fail), and `just format`, ruff's formatter, which
`just lint` checks.
