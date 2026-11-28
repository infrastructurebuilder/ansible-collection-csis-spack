# Implementation Plan: The first modules: an environment, and a build cache

**Branch**: `feature/spack-env-module`, until the history was reset on 2026-11-18 | **Date**: 2026-11-13 (written as a spec 2026-11-27) | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-first-modules/spec.md`

This plan records the design as it was built on 2026-11-13, from
`ATTIC/PLAN.md` and the code as it stands. It was not made with
`/speckit-plan`: Spec Kit was not used here until 2026-11-17.

## Summary

Two modules, `spack_env` and `spack_buildcache_push`, replace the Cloud
Sandbox's shell tasks around Spack. `spack_env` concretizes an environment,
installs it and regenerates its module files, reporting each kind of change
on its own, with a check mode that concretizes a copy. `spack_buildcache_push`
pushes an environment's packages to a mirror and reports what the mirror
gained, with a check mode that asks the mirror what it lacks. Both run Spack
through one shared runner, `plugins/module_utils/spack.py`, never through a
shell. The unit tests run them through Ansible against a stand-in `spack`;
the integration tests against the real Spack v1.2.0.

What was tried first is in [research.md](research.md): what `find --json`
and `spack.lock` give (R3), what a push prints (R5), what `buildcache check`
answers (R6), and the time Spack writes into each module file, found by the
integration test (R7).

## Technical Context

**Language/Version**: Python 3.12 (the modules, the shared runner, the
tests)

**Primary Dependencies**: ansible-core 2.16; Spack 1.0 or later on the
managed node

**Storage**: N/A. (Since 0.2.0 each module keeps a small file in the
environment's `.spack-env/` directory; 0.1.0 kept none.)

**Testing**: pytest through `just test`: unit tests running each module
through `ansible` itself against the stand-in `spack`
([tests/unit/fake_spack.py](../../tests/unit/fake_spack.py)), 45 on
2026-11-13. `just full-test`: the same, then both modules against the real
Spack v1.2.0 cloned into `.tmp/`, then `ansible-test sanity`.

**Target Platform**: the managed node (Linux); the local machine for the
tests

**Project Type**: an Ansible collection; this work made its first two modules
and its shared code

**Performance Goals**: none set. A build runs for as long as Spack takes, under
`async`; a test install with `--fake` takes seconds

**Constraints**: no shell; Spack's machine-readable output where it has one;
check mode touches nothing; the environment's `spack.yaml` is the site's

**Scale/Scope**: 2 modules, 1 shared module, 1 stand-in `spack`, unit and
integration tests, the README, `CHANGELOG.md`, `galaxy.yml`

## Constitution Check

*The constitution was ratified on 2026-11-17, four days after this work. This
check holds the work, as it was released in 0.1.0, to today's principles
after the fact. Where it would not have passed, that is said, with what
later work closed the gap.*

| Principle | Check | Result |
| --- | --- | --- |
| I. A Site's Choices Are Configuration, Not Code | The modules name no package, compiler or mirror; the environment, the executable, the mirror and the key are options. But the modules' `EXAMPLES` used the Cloud Sandbox's paths and names, and no test held the collection to the principle. 0.3.0 (2026-11-14) made the examples neutral and added `tests/unit/test_no_site_knowledge.py`. | Would not have passed until 0.3.0 |
| II. A Repeat Run Changes Nothing, and Says So | A second run with the same input reports no change, proved against the real Spack. Both modules support check mode, which installs, writes and pushes nothing. But `spack_env` regenerated the module files on every run, removing the tree first by default: reported rightly, not a no-op. `force: true` reported a change on every run and nothing said so. The note on `async` with check mode was not written. 0.2.0 and 0.3.1 (both 2026-11-14) closed these. | Partly: change reporting and check mode passed; the rest closed by 0.2.0 and 0.3.1 |
| III. Written to What Spack Does | Spack's own commands, as argument lists, never through a shell; `spack.lock`, `find --json` and `buildcache check -o` read as data. What they rely on was tried by hand against the real v1.2.0 first, and the stand-in follows it (research). But a real push was told apart from a no-op by Spack's printed lines, not by data (R5), which 0.2.0 replaced by asking the mirror. The findings were written in the plan of the time, not a spec's research; they are here now. 1.0 or later was accepted, and only v1.2.0 tested, which is what the principle asks of the pin. | Passed, but for the printed lines, closed by 0.2.0 |
| IV. Acceptance Tests Run Through the Justfile | `just test` (ruff, pyright with 0 errors, the unit tests, a build that installs) and `just full-test` (the integration tests, `ansible-test sanity`) passed. Unit tests cover every option, the change reporting both ways, check mode and failure; an integration test makes the claims about the real Spack. Galaxy's import checks were not yet part of `full-test`; spec 001 added them. | Passed for the targets of the time |
| V. The Operator Decides | Five decisions were asked one at a time and recorded before work depended on them (spec, Clarifications). The work began on the operator's "do the module plan". The record says it was released and pushed the same day; it does not record the operator's word for that apart from the plan's own "until the operator says so". Nothing went to Galaxy. No secret was handled: the signing key stays in the node's keyring. | Passed, as far as the record shows |
| The ATTIC | There was no ATTIC then. This retrospective was written from `ATTIC/PLAN.md` on the operator's word, for this task only. | N/A |

No Complexity Tracking: nothing was built against a principle on purpose.
The gaps above were found and closed by the work that followed, and are
recorded here so that the record stands without the ATTIC.

## Design, as built

### The shared runner, `plugins/module_utils/spack.py`

- **`Spack`**, one executable run on behalf of a module. A name without a
  path separator is looked up with `get_bin_path` (`spack` on `PATH` by
  default). `run(args, env_path=None, log_file=None, ok=(0,))` builds
  `[spack, "-e", env_path, *args]` and gives it to `run_command` as a list,
  never through a shell. With `log_file`, the output is written there. An
  exit code outside `ok` raises `SpackError`, carrying the command and the
  end of the output (today its last 50 lines), which the module turns into
  `fail_json`.
- **`version()`** and **`require_version()`**: `spack --version`, read as
  major, minor and patch; below 1.0 is refused, naming the version.
- **`installed(env_path)`**: `find --json`, as a mapping of hash to record.
- **`mirrors()`**: `mirror list`, as a mapping of name to URL.
- **Functions**: `file_digest` (SHA-256 of a file, or none);
  `tree_digest` and `module_tree_digest` (one digest of every file's name
  and contents under a root, the latter with Spack's time line, `CREATED_ON`,
  left out; research R7); `parse_version`; `lock_specs` (the concrete specs
  by hash and the roots, from `spack.lock`); `mirror_url` (a name, path or
  URL to a URL).

*Added later, and not part of this work:* `read_state`, `write_state` and
`data_digest`, `modules_config` and `module_roots` from `config get --json`
(0.2.0); the configuration planning and the `Configuration` class (0.3.0
and 0.3.1); `BEHAVIOUR`, `answered` and the reading of Spack's help (spec
003).

### `plugins/modules/spack_env.py`

1. Refuse a `path` with no `spack.yaml`; require Spack 1.0 or later.
2. **A real run:** digest `spack.lock`; `concretize --force -q [--fresh]`;
   `concretized` is the digest differing. For `state: installed`: the hashes
   `find --json` gives; `install <install_args>`, its output to `log_file`;
   `installed` is the hashes new afterwards, externals left out. For each
   system in `modules`: digest the module tree; `module <system> refresh -y
   [--delete-tree]`; digest again; the system is in `modules_refreshed` when
   the digests differ. In 0.1.0 this was done on every run.
3. **Check mode:** copy the environment's directory into a temporary one;
   concretize the copy; `concretized` is its `spack.lock` differing from
   the environment's; `installed` is the copy's concrete specs that
   `find --json` does not list, externals left out. The copy is removed. The
   environment is not touched.
4. `changed` is `concretized or installed or modules_refreshed`. Returned
   too: `roots` and `spack_version`, and `log_file` after an install.

### `plugins/modules/spack_buildcache_push.py`

1. Refuse an `env` with no `spack.yaml`, and `key` with `unsigned`; require
   Spack 1.0 or later. Turn `mirror` into a URL (`mirror_url`, from
   `mirror list` for a name).
2. **The selection:** the environment's installed packages
   (`find --json`), externals left out, cut to the roots or to their
   dependencies by `only`.
3. **Check mode:** `buildcache check -m <url> -o <file>`, exit 0 or 1; what
   would be pushed is the selection's packages under `rebuildSpecs`.
4. **A real run (0.1.0):** `buildcache push [--unsigned | --key K]
   [--update-index] [--only O] [--force] <mirror>` in the environment; what
   was pushed was read from the `Pushed <spec>/<short hash>` lines.
5. `pushed` lists them (name and hash); `changed` is `pushed` not empty.
   Returned too: `mirror_url` and `spack_version`.

*Changed later:* since 0.2.0 a real run asks `buildcache check` before and
after the push, and reports what the mirror lacked before and has after, plus
what `force` overwrote; `force: once` overwrites by hash, with
`--only package --force <mirror> /<hash>...`, one time.

### What surrounds Spack

Nothing in the modules. A site gives what Spack needs (loaded environment
modules, a compiler's variables) with the task's `environment:` keyword
(spec, Clarifications). 0.3.0 later gave the collection its own way to work
that environment out once: the `shell_environment` module, and the `setup`
role's `environment` step kind.

### Tests

- **The stand-in `spack`**, [tests/unit/fake_spack.py](../../tests/unit/fake_spack.py):
  a small program put first on `PATH` that answers `--version`,
  `concretize`, `install`, `find --json`, `module ... refresh`,
  `mirror list`, `buildcache push` and `buildcache check` from a JSON state
  file, as the real v1.2.0 answered them (research), and records every call
  in that file. It can be told to fail a subcommand.
- **Unit tests**, run through `ansible` itself
  ([tests/unit/conftest.py](../../tests/unit/conftest.py),
  [tests/unit/runner.py](../../tests/unit/runner.py)), for every option,
  the change reporting both ways, check mode and failure:
  [tests/unit/test_spack_env.py](../../tests/unit/test_spack_env.py),
  [tests/unit/test_spack_buildcache_push.py](../../tests/unit/test_spack_buildcache_push.py),
  and the shared runner's functions in
  [tests/unit/test_module_utils.py](../../tests/unit/test_module_utils.py).
- **The integration test**,
  [tests/integration/test_real_spack.py](../../tests/integration/test_real_spack.py)
  (`test_both_modules_against_the_real_spack`): the real Spack v1.2.0,
  cloned once into `.tmp/`; an environment of one small package installed
  with `install_args: [--fake]`; check mode first, changing nothing; each
  module run twice, the second run changing nothing; a push to a mirror in a
  local directory with `unsigned: true`, reported once. Today the same test
  also holds what 0.2.0 added, and runs against 1.0.0 and 1.1.0 too
  (spec 003).
- **`ansible-test sanity`** on both modules, in `just full-test`.

### Documentation

Each module's `DOCUMENTATION`, `EXAMPLES` and `RETURN`; the README's "What
it holds"; `CHANGELOG.md` with 0.1.0; `galaxy.yml` at 0.1.0.

## Project Structure

### Documentation (this feature)

```text
specs/007-first-modules/
├── spec.md
├── plan.md              # This file
├── research.md          # What Spack v1.2.0 did, read and tried first
├── tasks.md             # The work, as a record
└── checklists/
    └── requirements.md
```

No `data-model.md`, `contracts/` or `quickstart.md`: the interface is the two
modules' options and return values, stated in the spec and above, and the
modules' own `DOCUMENTATION` and `RETURN` hold them.

### Source Code (repository root)

The files this work made, as they are today; each has changed since, as the
notes above say.

```text
plugins/
├── module_utils/spack.py            # the shared runner and digests
└── modules/
    ├── spack_env.py
    └── spack_buildcache_push.py
tests/
├── unit/
│   ├── fake_spack.py                # the stand-in spack
│   ├── conftest.py, runner.py       # running a module through ansible
│   ├── test_spack_env.py
│   ├── test_spack_buildcache_push.py
│   └── test_module_utils.py
└── integration/
    └── test_real_spack.py           # both modules against the real Spack
README.md                            # "What it holds": Building an environment
CHANGELOG.md                         # 0.1.0 then; 0.0.1 now
galaxy.yml                           # the version
Justfile                             # test, full-test, build
```

**Structure Decision**: the layout of an Ansible collection, `plugins/modules`
and `plugins/module_utils`, with the tests beside it. Whether
`tests/unit/runner.py` and
[tests/integration/real_spack.py](../../tests/integration/real_spack.py)
were files of their own in 0.1.0 is not recorded; they were by spec 003,
which made `real_spack.py` give each test every supported version.
