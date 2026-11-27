# Data Model: Repeat runs that do nothing, and say so

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Both files are the module's own, kept in the environment's `.spack-env/`
directory (research R2), written as JSON with sorted keys, and replaced in
one step (written to `<name>.tmp`, then renamed). A file that is missing,
cannot be read, is not a JSON object, or has another `version` counts as no
record at all. As built in 0.0.1 and unchanged in 0.0.4.

## The module stamp: `.spack-env/csis_spack.modules.json`

Written by `spack_env` after every regeneration, with either value of
`refresh_modules`. Never written in check mode.

| Key | Value |
| --- | --- |
| `version` | `1` |
| `lock` | SHA-256 of `spack.lock` as it was after the regeneration |
| `config` | SHA-256 of the merged `modules` configuration, as JSON with sorted keys |
| `trees` | one entry per module system regenerated: `{"root": <the root's path>, "digest": <the tree's digest>}` |

A tree's digest is one SHA-256 over every file under the root, in sorted
order: each file's path relative to the root, and the SHA-256 of its
contents with Spack's time line (`Module file created by spack ... on
<date> ...`) removed. A root that does not exist has no digest.

## The overwritten record: `.spack-env/csis_spack.pushed.json`

Written by `spack_buildcache_push` after a real run with `force: once` that
overwrote something. Never written in check mode.

| Key | Value |
| --- | --- |
| `version` | `1` |
| `mirrors` | a mapping of mirror URL (a name or a path resolved to its URL first, as `file:///srv/mirror`) to the sorted list of full hashes overwritten there |

For example:

```json
{
 "mirrors": {
  "file:///srv/mirror": [
   "<full hash of gmake>",
   "<full hash of zlib>"
  ]
 },
 "version": 1
}
```

## `modules_reason`

Read in this order by `spack_env`; the first that holds is the reason.

| Value | When | Regenerates | Module files reported as changing in check mode |
| --- | --- | --- | --- |
| `not_requested` | `modules` is empty, or `state: concretized` | no | no |
| `always` | `refresh_modules: always` | yes | no |
| `concretized` | this run changed `spack.lock` | yes | no |
| `installed` | this run installed a spec | yes | no |
| `missing_root` | a module root of `modules` does not exist | yes | yes |
| `no_stamp` | no usable stamp, or it lacks a system of `modules` | yes | no |
| `lock_changed` | `spack.lock` differs from the stamp | yes | no |
| `config_changed` | the merged `modules` configuration differs from the stamp | yes | no |
| `files_changed` | a module tree, or its root's path, differs from the stamp | yes | yes |
| `not_needed` | none of the above | no | no |

"Regenerates" is the real run. Whatever the reason, the module files count
as changed only when a tree's digest differs after regenerating
(`modules_refreshed`).

## `force`

| Value | Pushes | Reported as pushed | Warns | Record |
| --- | --- | --- | --- | --- |
| `false` (default) | what the mirror lacks | what the mirror lacked before and has after | no | untouched |
| `true` | every selected package, with `--force` | every selected package, every run | yes, in a real run | untouched |
| `once` | first each selected package not in the record for this mirror, by hash with `--only package --force`; then what the mirror lacks | those overwritten, and what the mirror gained | no | those overwritten are added |

Any other value is refused before Spack runs. "Selected" is the
environment's installed packages, externals left out, cut down by `only`.
