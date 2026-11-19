# Collection stage 1: repeat runs that do nothing and say so

*Status:* planned 2026-11-14 on `feature/coll-stage-1`, and executed the
same day on "do coll 1". Merged into `develop`, released as 0.2.0 and
pushed on the operator's word, 2026-11-14. The decisions are under
[Decisions taken](#decisions-taken), the result under
[Outcome](#outcome).

## Why

Asked whether the modules of 0.1.0 are idempotent every time, the answer
was "mostly". A repeat run with nothing to do reports no change (proved
against the real Spack v1.2.0, and in the Cloud Sandbox's container
test), but:

1. **`spack_env` regenerates the module files on every run**, and with
   `delete_tree: true` (the default) deletes the tree first. The result is
   reported correctly, since the time Spack writes into each file is left
   out of the comparison, but the run is not a no-op: for a moment the
   module files are missing, and a user loading one then finds nothing.
2. **`spack_buildcache_push` with `force: true` pushes everything and
   reports a change on every run.** That is what `--force` means, but
   nothing says so when it is left on.
3. **`spack_buildcache_push` learns what it pushed by reading Spack's
   output**: the `==> [n/m] Pushed <spec>/<hash>` lines of Spack v1.2.0.
   The module accepts any Spack from 1.0. If a later Spack prints those
   lines differently, the module still pushes, but reports no change.

## What exists

- [plugins/modules/spack_env.py](../../plugins/modules/spack_env.py):
  `apply()` concretizes, installs, then, for each system in `modules`,
  hashes the module tree (`module_tree_digest`), runs `spack module
  <system> refresh -y [--delete-tree]`, and hashes it again.
- [plugins/modules/spack_buildcache_push.py](../../plugins/modules/spack_buildcache_push.py):
  check mode asks `spack buildcache check -m <url> -o <file>` what the
  mirror lacks; a real run runs `spack buildcache push` and reads its
  output with `pushed_specs()`.
- Tests: the stand-in `spack` (`tests/unit/fake_spack.py`) answers both
  commands; `tests/integration/test_real_spack.py` runs both modules
  twice against the real Spack v1.2.0.

## Items

1. **Module files regenerated only when they need to be** (`spack_env`).
   A new option, `refresh_modules`:
   - `always`: as in 0.1.0, every run;
   - `when_needed`: only when this run concretized something new or
     installed something, or when a module root is missing, or when what
     the module files are written from has changed since the last
     regeneration, or when the module files themselves have changed since
     then. Those last two parts are a stamp: after regenerating, the module
     writes, in the environment's `.spack-env/` directory, a digest of
     `spack.lock`, of the environment's `modules` configuration
     (`spack config get modules`), and of each module tree as it left it
     (`module_tree_digest`, which leaves out the time Spack writes into
     each file). A run whose digests all match the stamp, with every root
     present, does not regenerate. So a module file deleted or edited by
     hand is put back on the next run, as `always` would do.
   - The stamp is a file of the module's own in a directory that belongs
     to Spack. Spack leaves files it does not know there alone, and
     removes them with the environment (`spack env rm`). The README says
     so.

   The result says why it regenerated (`modules_reason`), or that it did
   not.

   **YOUR DECISION (the default):** `when_needed` (default), which
   changes what 0.1.0 does by default and makes a repeat run touch
   nothing; or `always`, which keeps 0.1.0's behaviour unless a task asks
   for the new one.

   **YOUR DECISION (what counts as "needed"):** the stamp as above
   (default), which also catches a change to the module configuration
   made with nothing new to install, and module files deleted or edited
   by hand; or only "this run concretized or installed something, or a
   root is missing", which needs no file of the module's own but misses
   both.

2. **Saying so when `force` is left on** (`spack_buildcache_push`).

   **YOUR DECISION (`force`):** a warning in the task's output on every
   run with `force: true`, that it pushes every package and reports a
   change every time (default); or a new value, `force: once`, which
   forces only the packages pushed by no earlier run of the module on
   this node (kept in a stamp file beside the environment), with
   `true` still forcing all and warning; or no change, only the
   documentation.

3. **Knowing what was pushed without reading Spack's messages**
   (`spack_buildcache_push`).

   **YOUR DECISION (how):** ask the mirror. Run `spack buildcache check`
   before and after the push, and report as pushed what the mirror
   lacked before and has after, the externals and `only` applied as in
   check mode (default). The printed lines are then only shown, not
   relied on. Costs two reads of the mirror's index per run, which on S3
   is a few seconds. Or keep reading the printed lines, and only warn
   when the check before the push said something was missing and the
   lines name nothing.

   With `force: true` the mirror lacks nothing afterwards either way, so
   "pushed" is what was selected and pushed, as now.

4. **Tests.**
   - Unit tests against the stand-in `spack`: `refresh_modules` both ways
     and every reason it gives; the stamp written, read, and outdated by
     a lock change, by a module-configuration change, and by a module
     file deleted or edited by hand (but not by Spack's time line alone); the `force`
     warning (or `force: once`); the push reported from the mirror, also
     when the stand-in prints its lines in another form.
   - Integration against the real Spack v1.2.0: a second run with
     `when_needed` leaves every module file untouched (same files, same
     modification times); enabling a second module naming scheme in
     `spack.yaml` regenerates; deleting one module file regenerates; the push is reported once, from the
     mirror.
   - `ansible-test sanity` on both modules.

5. **The release:** 0.2.0 (a new option and a changed default are a
   minor version), with `CHANGELOG.md`, the modules' `version_added` for
   the new options, and the README. Tagged locally; pushed only on the
   operator's word. Moving the Cloud Sandbox to 0.2.0 (one line in
   `sandbox-provisioning/requirements.yml`, and its `units.toml`) is a
   stage of the Cloud Sandbox's own.

## Decisions taken

Asked one at a time on 2026-11-14.

1. **The default:** `refresh_modules: when_needed`.
2. **What counts as "needed":** the stamp (the lock, the modules
   configuration, and the module trees).
3. **`force`:** the new value `once`; `true` still overwrites everything,
   and warns.
4. **What was pushed:** ask the mirror, before and after.

## Tried against Spack v1.2.0 first

- `spack -e <env> config get --json modules` prints the configuration
  with every scope merged, Spack's default roots included
  (`"lmod": "$spack/share/spack/lmod"`). The module roots are read from
  it, so PyYAML is no longer needed for that.
- An environment has a `.spack-env/` directory as soon as it has been
  concretized, with or without a view.
- `spack buildcache check` sees a package pushed a moment before with
  no `--update-index`: it looks for the package on the mirror, not in the
  index. So asking before and after is sound without rebuilding the
  index.
- `spack buildcache push --force --only package <mirror> /<hash>...`
  pushes exactly the packages named, a root or a dependency alike, and
  not their dependencies. That is how `force: once` overwrites a chosen
  set. With one package Spack prints `==> Pushed ...` without the
  `[n/m]` counter: one more reason not to read those lines.

## Out of scope

- **Moving the Cloud Sandbox to 0.2.0.** That is a stage of the Cloud
  Sandbox's own, and it must not take the new behaviour by default
  without saying so: its `spack_environment` role passes `modules: [tcl]`
  and nothing else, so whichever default 0.2.0 has would change what the
  role does without a line changing there. That stage sets
  `refresh_modules` explicitly in the role's `spack_env` task, notes
  beside it where it differs from the script (which regenerates on every
  run), and updates the role's traceability and the sandbox's MAP.md.

- `update_index: true` rebuilding the mirror's index on every run without
  reporting it.
- Check mode's copy of the environment not finding files that
  `spack.yaml` names by a relative path (`include:`, `develop:`).
- Testing against Spack versions other than v1.2.0.

## Acceptance

- `just test` and `just full-test` pass.
- Against the real Spack v1.2.0, a second run of `spack_env` with the
  default `refresh_modules` changes no file under the module roots, and
  `spack_buildcache_push` reports exactly the packages the mirror gained.

## Outcome

- **`spack_env`:** `refresh_modules` (`when_needed` by default, or
  `always`) and the return value `modules_reason`. The stamp is
  `.spack-env/csis_spack.modules.json`: digests of `spack.lock`, of the
  merged `modules` configuration, and of each module tree with Spack's
  time line left out. Check mode gives the reason, and reports the
  module files as changing only where that is certain (a missing root,
  a file changed by hand).
- **`spack_buildcache_push`:** the packages reported are those the
  mirror lacked before the push and has after it, plus those `force`
  overwrote. `force: once` keeps `.spack-env/csis_spack.pushed.json`,
  per mirror URL; it overwrites the packages it has not yet, by hash,
  then pushes normally. `force: true` warns on every run. The printed
  lines are no longer read; the stand-in can word them differently and a
  test does.
- **Found while writing it:** Spack's default module root is shared by
  every environment of a Spack, and `--delete-tree` removes all of it.
  With two environments and one root, each run would undo the other's and
  the stamp would never match. The option's documentation and the README
  say to give each environment its own root or set `delete_tree: false`.
- **Tests:** 72 unit tests through `ansible` against the stand-in (45
  before). The integration test against the real Spack v1.2.0 now also
  holds that a repeat run leaves every module file's modification time
  as it was, that `always` rewrites them without reporting a change,
  that a deleted module file is put back, that a changed modules
  configuration regenerates with nothing to install, and that
  `force: once` overwrites one time. `just test` and `just full-test`
  pass, `ansible-test sanity` included.
- **Release:** 0.2.0, tagged and pushed 2026-11-14.

