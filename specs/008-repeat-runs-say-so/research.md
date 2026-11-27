# Research: Repeat runs that do nothing, and say so

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Principle III asks that the behaviour a module relies on is tried first, and
what was found is written down. This work was done on 2026-11-14, before the
constitution was ratified, but it was tried first all the same: R1 to R4
against the real Spack v1.2.0 before the modules were changed, and R5 found
while writing the change. The record kept at the time does not say which
machine or which `git` was used; this file does not guess.

## Before this work

What the modules of 0.1.0 did, and what this work started from:

- `spack_env`'s `apply()` concretized, installed, then, for each system in
  `modules`, took a digest of the module tree (`module_tree_digest`), ran
  `spack module <system> refresh -y [--delete-tree]`, and took a digest
  again. The digest leaves out the line in which Spack writes the time into
  each module file (`## Module file created by spack (...) on <date> <time>`),
  so a regeneration that wrote the same files was not reported as a change.
  It ran on every run.
- `spack_buildcache_push`'s check mode asked `spack buildcache check -m <url>
  -o <file>` what the mirror lacked. A real run ran `spack buildcache push`
  and read its output with `pushed_specs()`, which looked for Spack
  v1.2.0's `==> [n/m] Pushed <spec>/<hash>` lines.
- The stand-in `spack` (`tests/unit/fake_spack.py`) answered both commands;
  `tests/integration/test_real_spack.py` ran both modules twice against the
  real Spack v1.2.0.

## R1. Reading the module roots from Spack

`spack -e <env> config get --json modules` prints the `modules`
configuration with every scope merged, Spack's default roots included
(`"lmod": "$spack/share/spack/lmod"`).

**Decision:** the module roots, and the configuration whose digest goes into
the stamp, are read from that one command. `$spack` is replaced by what
`spack location -r` prints. PyYAML is no longer needed to read the roots.

*Later:* Spack 1.0 has no `config get --json`. Spec 003 found that this
failed there, and since 0.0.3 the same merged configuration is read on 1.0
through Spack's own `spack python -c` (`BEHAVIOUR`, `config_json`, in
[plugins/module_utils/spack.py](../../plugins/module_utils/spack.py)). Where
the configuration names no root for a system, the code falls back to
Spack's own defaults as `etc/spack/defaults/base/modules.yaml` gives them
(`DEFAULT_MODULE_ROOTS`).

## R2. The environment's `.spack-env/` directory

An environment has a `.spack-env/` directory as soon as it has been
concretized, with or without a view.

**Decision:** the two files of the module's own, the stamp and the
`force: once` record, are kept there, beside the environment they describe.
The code also makes the directory if it is missing, so the file can always
be written.

## R3. `spack buildcache check` right after a push

`spack buildcache check` sees a package pushed a moment before with no
`--update-index`: it looks for the package on the mirror, not in the index.

**Decision:** asking the mirror before and after the push is sound without
rebuilding the index. What was pushed is what the mirror lacked before and
has after; the printed lines are only shown, not relied on.

## R4. Overwriting a chosen set of packages

`spack buildcache push --force --only package <mirror> /<hash>...` pushes
exactly the packages named, a root or a dependency alike, and not their
dependencies. With one package, Spack prints `==> Pushed ...` without the
`[n/m]` counter.

**Decision:** `force: once` overwrites the packages it has not overwritten
on that mirror before with exactly that command, then pushes normally. The
form of the printed line changing with the number of packages is one more
reason not to read those lines (R3).

## R5. One module root shared by several environments (found while writing it)

Spack's default module root is shared by every environment of a Spack, and
`--delete-tree` removes all of it. With two environments and one root, each
run would undo the other's, and the stamp would never match: every run of
each would regenerate.

**Decision:** not detected in code. The `delete_tree` option's
documentation and the README ("One module tree, several environments") say
to give each environment a root of its own (`modules:default:roots` in its
`spack.yaml`) or to set `delete_tree: false`.

## Decisions

| # | Decision | Alternatives considered |
| --- | --- | --- |
| 1 | `refresh_modules: when_needed` by default (Clarifications) | `always` by default, keeping 0.1.0's behaviour unless a task asks |
| 2 | "Needed" is read from a stamp: the lock, the merged modules configuration, the module trees | Only "concretized, installed, or a root missing": no file of the module's own, but a configuration change with nothing to install, or a module file deleted or edited by hand, would be missed |
| 3 | `force: once`, recorded per mirror URL; `force: true` warns | A warning only; documentation only |
| 4 | What was pushed is read from the mirror, before and after (R3) | Keep reading the printed lines, and warn when the check before found something missing and the lines name nothing |
| 5 | The roots are read from `config get --json modules` (R1) | Reading them with PyYAML, as before (the record says only that PyYAML was no longer needed for it) |
| 6 | The shared root is documented, not detected (R5) | None recorded |
