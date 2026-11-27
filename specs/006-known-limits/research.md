# Research: Two known limits, said where a site reads them, or removed

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Tried on 2026-11-27 on the operator's local machine against the real Spack
1.0.0, 1.1.0 and 1.2.0 in `.tmp/` (each with its own user configuration and
caches, as the integration tests set them), in a scratch directory.

## R1. A push with nothing to push leaves the mirror's index alone

The limit recorded on 2026-11-14 (spec 008, Out of Scope) was that
`spack_buildcache_push` with `update_index: true` rebuilds the mirror's index
on every run. Tried: an environment of `zlib`, installed with `--fake` into a
store of its own, pushed `--unsigned --update-index` to a mirror in a
directory, then pushed again the same way.

| Spack | The second push printed | The index (`v3/manifests/index/index.manifest.json`) |
| --- | --- | --- |
| 1.0.0 | `All specs are already in the buildcache. Use --force to overwrite them.` | not rewritten: same time, same contents |
| 1.1.0 | the same | not rewritten |
| 1.2.0 | the same | not rewritten; `spack buildcache update-index` by hand does rewrite it (its time changed) |

So Spack itself rebuilds the index only when the push sent something. The
limit, as recorded, is not true of any Spack the collection supports; the
behaviour the operator chose (spec, Clarifications) is Spack's already. (The
2026-11-14 note may have been read from the code, which passes
`--update-index` to every push it runs, rather than from what Spack does with
it.) The module does run `spack buildcache push` on every run; with nothing
to push, that is a second or two and changes nothing.

**Decision:** no change to what `spack_buildcache_push` runs. Its
documentation of `update_index` says that the index is rebuilt only after a
push that sent something, and that an index changed by other means is not
put right by a run with nothing to push (FR-001, FR-002). An integration
test holds it against the three versions (FR-005).

## R2. What a preview from a copy misses

`spack_env`'s check mode copies the environment's whole directory (all but
`.spack-env/` and `log.*`) into a temporary directory and concretizes the
copy. Tried with an environment whose `spack.yaml` has
`include: [./extra.yaml, ../shared.yaml]`, with `build_jobs: 3` in the first
and `5` in the second:

- The real environment reads `build_jobs: 3`.
- The copy: `==> Error: Required path (../shared.yaml) does not exist at
  (<scratch>/copy/shared.yaml)`. `./extra.yaml` was found: it is inside the
  environment's directory, so it was copied with it.

So an `include:` path inside the environment already works in a preview.
One that leads above it makes the preview fail; it cannot be "made without
it" (the clarified answer), because Spack refuses a required include that is
not there.

## R3. A `develop:` path changes the lock

An environment with `develop: {zlib: {spec: zlib@=1.3.1, path:
../zlib-src}}`, copied the same way, concretized without error and made
nothing beside the copy. But Spack records a develop package's path in the
lock as an absolute `dev_path` variant: in the copy it was
`<scratch>/copy2/zlib-src`, not the real `<site>/zlib-src`. The variant is
part of the spec's hash, so the copy's `spack.lock` differs from what the
real environment would write, and the preview says "would concretize" when a
real run would not. That holds for **any** relative `develop:` path, inside
the environment's directory or above it.

## R4. The copy's paths rewritten to the originals'

The copy's `spack.yaml` was rewritten so that each relative `include:` entry
(a string, or the `path` of a mapping) and each `develop:` entry's `path`
became the absolute path it names from the real environment's directory.
Absolute paths, and paths with a `$` (Spack's own variables), were left as
they were. The rewrite was done by Spack's own Python, `spack python
<script> <copy's spack.yaml> <real environment's directory>`, with
`spack.util.spack_yaml` to read and write the file:

| Spack | The copy afterwards |
| --- | --- |
| 1.0.0 | reads `build_jobs: 3`, as the real environment; the develop path is the real `<site>/zlib-src` |
| 1.1.0 | the same |
| 1.2.0 | the same |

`spack python -c` takes neither arguments nor more than one statement
(spec 003, research), so the script is a file the module writes into its own
temporary directory beside the copy. The files the paths name are read where
they are; nothing of the real environment, or around it, is written.

**Decision:** in check mode, after copying and before concretizing,
`spack_env` rewrites the copy's relative `include:` and `develop:` paths to
the originals' absolute paths, with Spack's own Python, so that the preview
reads and records what a real run would. This goes beyond the clarified
answer (copy the files inside the environment, name the ones above it),
which R2 and R3 show cannot work: Spack refuses a missing include, and any
relative develop path already gives the wrong lock. It is put to the
operator in the plan.

## R5. Where `spack.yaml` is read

The module has never read `spack.yaml` itself (it only checks that it is
there), and PyYAML is not sure to be on a node (ansible-core needs it on the
controller only). Spack carries its own YAML (`spack.util.spack_yaml`), the
one it reads `spack.yaml` with.

**Decision:** the rewrite runs in Spack's Python, not the module's. This is
"Spack's own commands" in principle III's sense; `spack python` is already
used for Spack 1.0's configuration (spec 003).

## Decisions

| # | Decision | Alternatives considered |
| --- | --- | --- |
| 1 | No change to the push; document and test what Spack does (R1) | Skip the push when the mirror lacks nothing: saves a second or two, changes nothing a site sees |
| 2 | Rewrite every relative `include:` and `develop:` path in the copy to the original's absolute path (R4) | The clarified answer, name the ones above the environment: Spack fails on them (R2), and develop paths inside it give a wrong lock (R3); symbolic links beside the copy: fix includes, not `dev_path` |
| 3 | The rewrite in `spack python` with a script file (R4, R5) | PyYAML in the module: not sure to be on the node; `spack config add` on the copy: cannot rewrite a list's entries in place |
