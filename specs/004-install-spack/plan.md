# Implementation Plan: A `setup` step that installs Spack

**Branch**: `feature/install-spack` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-install-spack/spec.md`

## Summary

A new module, `spack_checkout`, puts a Spack at a path at the version a site
names, by the shallow `git clone` Spack's own documentation uses, and leaves
a Spack already there alone when it is at that version. A Spack at another
version, or something that is not a Spack, fails the step with nothing
changed. The `setup` role gets a step kind for it, `spack`, which must be the
list's first step; the steps after it run `<path>/bin/spack`.

What was tried first is in [research.md](research.md): which form of `git`
fetches a tag, a branch and a commit (R2); how a later run tells, with no
network, whether the Spack there is at the version named (R3); what
`spack --version` says (R5); and how a stopped install is kept from leaving
something that looks like a Spack (R6).

**Names proposed, for the operator to confirm** before `/speckit-tasks`: the
kind `spack`, the module `spack_checkout`, the options `version`, `path` and
`source`, and `version_added: 0.0.4`. See "Names" below.

## Technical Context

**Language/Version**: Python 3.12 (the module, the filters, the tests); YAML
and Jinja2 (the role)

**Primary Dependencies**: ansible-core 2.16; `git` on the managed node (R8);
Spack 1.0 or later, which this step now installs

**Storage**: N/A

**Testing**: pytest through `just test`: the module's unit tests run real
`git` against small source repositories made in the test, whose `bin/spack`
answers `--version` as the stand-in does; the role's tests use the stand-in
`spack`. `just full-test`: integration tests that install from the local
clones of the real Spack 1.0.0, 1.1.0 and 1.2.0 the integration tests
already keep, so no network is needed.

**Target Platform**: the managed node, as today (Linux; the local machine
for the tests)

**Project Type**: an Ansible collection; this adds one module, one step kind
and two filter rules, and changes which executable the role's later steps run

**Performance Goals**: a repeat run costs one `git` call or two and one
`spack --version`, about 1 second (R5); an install from Spack's public
repository is one fetch of about 6 MB (R2)

**Constraints**: a repeat run needs no network; nothing runs through a
shell; a list with no `spack` step behaves exactly as today; nothing at the
destination is changed except by an install into a destination that is
absent or empty

**Scale/Scope**: 1 new module; `plugins/filter/setup_problems.py`; the
role's `main.yml`, `step.yml`, the 5 kind files that pass the executable,
1 new kind file and its README; 1 new example; unit tests for the module,
the filter and the role; integration tests for the module and the role;
`CHANGELOG.md`; the README

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Result |
| --- | --- | --- |
| I. A Site's Choices Are Configuration, Not Code | The version and the path are required, with no default (FR-002). The default source is Spack's own public repository, Spack's and not a site's, as the default executable `spack` is. The role still has no step of its own. `test_no_site_knowledge.py` is not loosened. | Pass |
| II. A Repeat Run Changes Nothing, and Says So | A Spack at the version named is left alone and no change is reported (FR-005, R3); the check needs no network, so a moved branch is not a change. Check mode changes nothing and contacts no source (R9, decision 6). A change is reported only for an install. | Pass |
| III. Written to What Spack Does | Installing Spack has no Spack command: Spack's documentation installs it with `git clone`, which the module runs, as an argument list, never through a shell (R1, R2). Everything the module relies on was tried first against the real Spack clones and against GitHub (R2 to R6). After an install it asks the installed Spack itself for its version (R5). The pin stays 1.2.0. | Pass |
| IV. Acceptance Tests Run Through the Justfile | Tests first, seen to fail: the module's against real `git`, the filter's, the role's against the stand-in; integration tests against the real 1.0.0, 1.1.0 and 1.2.0. The example is run by `tests/unit/test_examples.py`. `just test` after each change, `just full-test` before done. | Pass |
| V. The Operator Decides | Three answers are in the spec's Clarifications. The public names and `version_added` are proposed here and asked before tasks are made. Committed locally; merged, pushed and released only on the operator's word. | Pass |
| The ATTIC | Not consulted. | Pass |

No violations; Complexity Tracking is not needed.

**Re-checked after the design below:** unchanged. One point was weighed
under Principle II: in check mode on a new node, the steps after a `spack`
step are not carried out (they would run a Spack that is not there yet), and
each says so in the results. Nothing is changed, and nothing is reported as
changed that would not be.

## Design

### Names

| Thing | Proposed | Why | Weighed |
| --- | --- | --- | --- |
| The step's kind | `spack` | A step about the Spack itself, beside `config`, `mirror` and the rest, which are about what is in it | `install`: reads as `spack install`, which installs packages |
| The module | `spack_checkout` | Says what it makes: a checkout of Spack at a version. The other kinds' modules are `spack_<kind>`, but `spack_spack` says nothing | `spack_install`: the same confusion as `install` |
| The options | `version`, `path`, `source` | `path` is the collection's word for a directory (`spack_env`); `version` and `source` are the spec's words | `dest` and `repo`, as `ansible.builtin.git` has them |
| `version_added` | `0.0.4` | The next release, by the numbering the operator chose for 0.0.3 | `0.1.0`, a new feature under semantic versioning |

### The module, `plugins/modules/spack_checkout.py`

Options:

- `version` (str, required): a tag or a branch of Spack's repository, or a
  commit written as its full 40-digit hash. A shorter hexadecimal string is
  refused before anything is fetched (R2).
- `path` (path, required, absolute): the directory Spack is installed in.
- `source` (str, default `https://github.com/spack/spack.git`): the git
  repository to fetch from.

It finds `git` with `get_bin_path("git", required=True)` (R8), and decides
from what is at `path`:

| At `path` | What it does | `changed` | In check mode |
| --- | --- | --- | --- |
| Nothing | Makes the parent if needed; clones into a temporary directory beside `path`; checks the version there; renames it to `path` (R6) | true | reports the install; nothing is made |
| An empty directory | Clones into it directly, keeping its ownership and mode; checks the version (R6) | true | reports the install |
| A Spack at the version named (R3, R4) | Checks the version (FR-006) | false | the same, with no `git` call that changes anything |
| A Spack at another version | Fails: the version found (`spack --version`, and the tag, branch or commit HEAD is at) and the version named | — | fails the same way |
| Anything else (not empty, not the top of a git repository with `bin/spack`) | Fails, saying what it found | — | fails the same way |

"Checks the version" runs `<path>/bin/spack --version` (R5) and fails unless
its first word is a version of 1.0 or later. For an install into a new
directory, the check runs before the rename, so a version below 1.0 leaves
nothing at `path`.

A failed `git` command fails the step with git's own message (a version not
found, a source not reached). Every command is an argument list given to
`run_command`; the module never runs a shell. The module does not use
`module_utils/spack.py`'s `Spack` runner, which runs a Spack that is already
there; it runs `bin/spack --version` itself, once, the same way.

Returns: `path`; `spack`, the executable (`<path>/bin/spack`); `version`, as
named; `spack_version`, what `spack --version` printed; `found`, one of
`nothing`, `empty` or `spack`.

### The role

- **`plugins/filter/setup_problems.py`**: `KINDS["spack"]`, carried out by
  `spack_checkout`, requires `version` and `path`, and may have `source`
  (and `label` and `environment`, as every step may: an environment can set
  a proxy or a certificate for `git`). It has no `yes_to_all` and no
  `scope`. New rules, each a problem found before any step runs (FR-008):
  - a `spack` step that is not the first step, or a second one;
  - a `spack` step whose `path` is not absolute;
  - a `spack` step when `spack_setup_executable` is set to something other
    than `spack` (its default) and other than `<path>/bin/spack`. For this
    the filter takes the executable as an optional argument:
    `spack_setup | setup_problems(spack_setup_executable)`.
- **A new filter, `setup_executable`**, in the same file: given the list and
  `spack_setup_executable`, it returns `<path>/bin/spack` when the first step
  is a `spack` step, and the executable otherwise.
- **`roles/setup/tasks/main.yml`** passes the executable to the check, and
  sets `spack_setup_program` from `setup_executable` for the loop.
- **The five kind files** (`command`, `config`, `detect`, `gpg_key`,
  `mirror`) pass `spack_setup_program` where they now pass
  `spack_setup_executable`. With no `spack` step the two are the same, so
  every list written for 0.0.3 runs exactly as it did.
- **`roles/setup/tasks/kinds/spack.yml`**: runs `spack_checkout` with the
  step's options. Afterwards, if this is check mode and it reported an
  install, it sets `spack_setup_not_installed: true` (R9).
- **`roles/setup/tasks/step.yml`**: when `spack_setup_not_installed` is true,
  a step is not carried out; its result is recorded as not changed, with
  `previewed: false` and the reason: "Spack is not installed yet: check mode
  does not install it, so this step cannot be previewed".
- **`setup_label`**: a `spack` step is labelled `spack: <version> at <path>`.

### Tests

- **`tests/unit/test_spack_checkout.py`** (new), the module through Ansible
  as the other modules' tests run, with real `git`. A fixture makes a
  source repository in the test's directory with tags `v0.23.0`, `v1.0.0`
  and `v1.2.0`, a branch `releases/v1.2`, and at each a `bin/spack` that
  prints that version as Spack does. Cases: an install by tag, by branch and
  by full hash, each a change and then no change; check mode, nothing made;
  into an empty directory, its mode kept; into a missing parent; another
  version there, nothing changed; not a Spack (files; a git repository with
  no `bin/spack`; a subdirectory of another repository), nothing changed; a
  version not in the source, nothing left at `path`; a short hash refused
  with no `git` run; a version below 1.0, nothing left at `path`; a source
  that cannot be reached; no `git` on `PATH`; a Spack cloned by hand with
  `git clone --depth 1 --branch`, no change; and that no command was run
  through a shell.
- **`tests/unit/test_setup_filter.py`**: the new kind's options; each new
  rule; `setup_executable` with and without a `spack` step; the label.
- **`tests/unit/test_setup_role.py`**: a `spack` step then a `config` step,
  with a source whose `bin/spack` runs the stand-in, leaves a mark and
  holds the setting: the later step ran the Spack the step installed; a
  second run, no change; check mode, one change, the later step not
  previewed, nothing made; a conflicting `spack_setup_executable` refused
  before any step.
- **`tests/unit/test_examples.py`**: the new example is carried out with its
  `source` replaced by a local repository, since the unit tests have no
  network.
- **`tests/integration/test_real_spack.py`**: for each of 1.0.0, 1.1.0 and
  1.2.0, `spack_checkout` from the local clone as `file://` source into a new
  path: a change, `spack_version` the version asked for, then no change;
  the local clone itself, named as `path` with its tag, no change; another
  version named over it, a failure with nothing changed.
- **`tests/integration/test_real_setup.py`**: a `spack` step then a `config`
  step against the real Spack installed by it.

### Documentation

- The module's `DOCUMENTATION`, `EXAMPLES` and `RETURN`: what it does with
  each state of `path`; that `git` is needed; that Spack's package recipes
  are left to Spack, and that a site without the network sets a recipe
  repository of its own with a `config` step (FR-012); that a Spack at
  another version fails the step.
- `roles/setup/README.md`: the kind in the table; a section "Installing
  Spack: the `spack` step", with the first-step rule, which executable the
  later steps run, and check mode on a new node.
- `docs/examples/spack-installed-by-the-role.yml` (new): a `spack` step, a
  `config` step and a `mirror` step.
- `README.md`: Requirements say that Spack is needed on the node only when
  the list has no `spack` step, and that the step needs `git` (FR-013).
- `CHANGELOG.md`: an Unreleased section.

## Project Structure

### Documentation (this feature)

```text
specs/004-install-spack/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0: what git and Spack do
├── data-model.md        # Phase 1: the step, the states of the path, the rules
├── quickstart.md        # Phase 1: how to see it work
├── contracts/
│   └── interface.md     # Phase 1: the module, the step, what is run
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks; not made here)
```

### Source Code (repository root)

```text
plugins/modules/spack_checkout.py        # new
plugins/filter/setup_problems.py         # the kind, its rules, setup_executable, the label
roles/setup/
├── tasks/main.yml                       # the executable to the check; spack_setup_program
├── tasks/step.yml                       # steps not previewed after a check-mode install
├── tasks/kinds/spack.yml                # new
├── tasks/kinds/{command,config,detect,gpg_key,mirror}.yml   # spack_setup_program
└── README.md
docs/examples/spack-installed-by-the-role.yml   # new
tests/unit/
├── test_spack_checkout.py               # new
├── test_setup_filter.py, test_setup_role.py, test_examples.py
tests/integration/test_real_spack.py, test_real_setup.py
README.md, CHANGELOG.md
```

**Structure Decision**: the collection's existing layout. The one new module
sits beside the others; no new directory is added, and nothing is added to
the `Justfile`.
