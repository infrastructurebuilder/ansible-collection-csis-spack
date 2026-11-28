# Research: The first modules: an environment, and a build cache

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Principle III asks that the behaviour a module relies on is tried first, and
what was found is written down in the spec's research. This work came before
the constitution, and what was found was written in the plan of the time
(`ATTIC/PLAN.md`, now retired). It is carried here.

It was found in two ways, on 2026-11-13, against Spack v1.2.0, the version
the Cloud Sandbox pins:

- **Read from Spack's `--help`**, while planning (R1 to R5).
- **Tried by hand on the operator's local machine**, before the modules were
  written: concretize, `install --fake`, `find --json`, `module tcl
  refresh`, `buildcache push` twice, and `buildcache check -o` (R3, R5, R6).
  The modules, and the stand-in `spack` the unit tests use
  ([tests/unit/fake_spack.py](../../tests/unit/fake_spack.py)), follow what
  that showed, not what the help suggested.

One more finding came from the integration test, after the modules were
written (R7).

## R1. Concretizing

`spack -e <env> concretize [-f] [-U|--fresh] [--reuse] [-q]` writes the
environment's `spack.lock`. `-f` (`--force`) concretizes again even when
the environment is already concrete; `--fresh` picks the newest
configuration rather than reusing what is installed.

**Decision:** `spack_env` runs `concretize --force -q`, adding `--fresh`
when the option `fresh` is true (the default, as the Cloud Sandbox ran it).
A change is `spack.lock` differing, by SHA-256, from what it was before the
run.

## R2. Installing, and installing in seconds

`spack -e <env> install [--fake] [--cache-only] [--use-buildcache ...]
[-j N] [--only-concrete]`. `--fake` installs without building: the package
is recorded as installed, and nothing is compiled.

**Decision:** `spack_env` passes `install_args` to `spack install` as they
are, so a site keeps what the Cloud Sandbox kept in `spack_opts`. The
integration test installs with `install_args: [--fake]`, which makes a test
of a real install take seconds.

## R3. What is installed: `find --json`

`spack -e <env> find --json` prints the environment's installed specs as
JSON, each with its hash. An external is marked as one. The hashes are the
same ones `spack.lock` gives under `concrete_specs`.

**Decision:** "newly installed" is the set of hashes `find --json` gives
after the install less those it gave before, with externals left out. In
check mode, what would be installed is the specs of the copy's new
`spack.lock` that `find --json` does not list, externals left out. Because
the two agree on hashes, no spec has to be matched by name.

## R4. Regenerating module files

`spack -e <env> module tcl refresh --delete-tree -y` regenerates the Tcl
module files of the environment's specs. `-y` answers Spack's confirmation;
`--delete-tree` removes the module tree first. Spack's default roots are
`$spack/share/spack/modules` for Tcl and `$spack/share/spack/lmod` for Lmod,
where `$spack` is Spack's own directory.

**Decision:** for each system in `modules`, `spack_env` runs `module
<system> refresh -y`, with `--delete-tree` when `delete_tree` is true (the
default, as the Cloud Sandbox ran it), and compares the module tree before
and after (R7).

*Later:* in 0.2.0 (2026-11-14) the roots were read from `spack config get
--json modules`, which gives every scope merged with Spack's defaults; the
record of that stage says 0.1.0 read them in a way that needed PyYAML, and
does not say more. The same stage found that the default root is shared by
every environment of a Spack, so `--delete-tree` for one removes the others'
files; the option's documentation says so.

## R5. Pushing: the command and what it prints

`spack buildcache push [--unsigned|--signed|--key KEY] [--update-index]
[--only package|dependencies] [-f] <mirror> [specs]`. In an environment
(`-e <env>`), with no specs named, it pushes the environment's packages.

Tried by hand, twice: the first push printed one `Pushed <spec>/<short
hash>` line for each package; the second, with nothing new, printed "All
specs are already in the buildcache".

**Decision (0.1.0):** `spack_buildcache_push` runs the push in the
environment with no specs named. `--unsigned`, `--key`, `--update-index`,
`--only` and `--force` follow its options. What was pushed is read from the
`Pushed` lines, so a second push reports no change.

*Later:* 0.2.0 found that with one package Spack prints `==> Pushed ...`
without the `[n/m]` counter it prints with several, which was one more reason
not to read those lines. Since 0.2.0, what was pushed is learned from the
mirror (R6) before and after, and the printed lines are not read; the
stand-in words them otherwise in a test to hold that.

## R6. What a mirror lacks: `buildcache check -o`

`spack -e <env> buildcache check -m <mirror URL> -o <file>` writes, as JSON,
the environment's specs that the mirror lacks, under `rebuildSpecs`.
Externals are among them. It exits 1 when anything is missing, and 0 when
nothing is.

**Decision:** in check mode `spack_buildcache_push` asks this, once, and
reports as what would be pushed the specs it names, with externals left out
and `only` applied. Exit 1 is not a failure there. A mirror given by name is
turned into its URL from `spack mirror list`; a path becomes a `file://`
URL.

*Later:* 0.2.0 found that `buildcache check` sees a package pushed a moment
before even with no `--update-index`, since it looks for the package and
not in the index. That made asking before and after a push sound.

## R7. The time in every module file (found by the integration test)

Spack stamps every module file it writes with the time it wrote it, on a
line such as:

```text
## Module file created by spack (https://github.com/spack/spack) on 2026-11-13 11:00:30.218360
```

So every refresh changes every file, and comparing the trees as they are
reports a change on every run, even when nothing else differs.

**Decision:** module trees are compared by a digest of every file's name and
contents with that line left out
(`module_tree_digest` in
[plugins/module_utils/spack.py](../../plugins/module_utils/spack.py), with
the pattern `CREATED_ON`). Today the stand-in writes the time into each
file, as Spack does. The same flaw was in the Cloud Sandbox's
`spack_environment` role, which hashed every file under the module root; it
was recorded in that repository's `MAP.md`.

## R8. The real Spack, apart from the local machine's own

The integration test clones Spack v1.2.0 once into `.tmp/spack` and runs
it with its user configuration and caches in `.tmp/` too, so that nothing
of the local machine's own Spack is read or written (Clarifications, the
fourth answer). The first concretization bootstraps Spack's solver and takes
a few minutes.

**Decision:** one environment holding one small package, installed with
`--fake`, each module run twice, check mode run before, and a push to a
mirror in a local directory with `unsigned: true`. Today the package is
`zlib`, with `view: false` and an install tree and a module root of the
test's own, so that every run starts from nothing; the clone and its
environment (`SPACK_USER_CONFIG_PATH`, `SPACK_USER_CACHE_PATH`,
`SPACK_DISABLE_LOCAL_CONFIG`) are made in
[tests/integration/real_spack.py](../../tests/integration/real_spack.py),
which also keeps the clones of 1.0.0 and 1.1.0 that spec 003 added beside
the pin.

## Decisions

| # | Decision | Alternatives considered |
| --- | --- | --- |
| 1 | One module for the environment, `spack_env`, with `state` | Three modules (`spack_concretize`, `spack_install`, `spack_module_refresh`) chained by a role |
| 2 | Pushing is a module of its own, `spack_buildcache_push` | An option of `spack_env`; left out of this work |
| 3 | What surrounds Spack is given with `environment:`; the modules run no shell | A `shell_init` option: lines run in bash before Spack |
| 4 | The integration test runs on the local machine, Spack's configuration and caches in `.tmp/` | An AlmaLinux 10 container, as `sandbox-provisioning`'s test |
| 5 | Spack 1.0 or later, tested with v1.2.0 | Only v1.2.x |
| 6 | Changes are read from `spack.lock`, `find --json` and the module trees, not from what Spack prints, except the push's `Pushed` lines (R5) | Hashing every file before and after, as the shell tasks did |
| 7 | Module trees are compared without Spack's time line (R7) | Comparing them as they are: a change on every run |
| 8 | Check mode concretizes a copy of the environment in a temporary directory | Concretizing the environment itself: that writes its `spack.lock` |

The first five were the operator's, asked on 2026-11-13 (spec,
Clarifications). The rest were the plan's or the build's. The plan had named
`spack buildcache list` against the mirror, before and after, for telling
what was pushed; as built, 0.1.0 read the push's printed lines for a real
run and asked `buildcache check` only in check mode (R5, R6).
