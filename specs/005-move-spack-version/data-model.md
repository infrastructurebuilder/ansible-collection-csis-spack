# Data Model: The install step moves a Spack to another version, when a site asks

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Names as the plan proposes them, for the operator to confirm. Everything not
named here is spec 004's ([../004-install-spack/data-model.md](../004-install-spack/data-model.md)).

## The option

| Field | Where | Type | Default | Rule |
| --- | --- | --- | --- | --- |
| `move` | `spack_checkout`; the `spack` step | bool | `false` | Only changes what happens when the path holds a Spack at another version |

## The states of the path, with `move: true`

As spec 004's, read in the same order. Only one row changes what it leads to:

| State | `move: false` | `move: true` |
| --- | --- | --- |
| `nothing`, `empty` | install (004) | install (004) |
| `spack` at the version | no change (004) | no change (004) |
| `spack` at another version | failure, nothing changed | the move below |
| not a Spack | failure, nothing changed | failure, nothing changed |

## The move

```text
spack at another version
  --edited files?--------------> failure, nothing changed (names them)
  --stage the version beside---> failure if not in the source, nothing changed
  --staged spack --version-----> failure below 1.0, nothing changed
  --site's files the new
    version tracks?------------> failure, nothing changed (names them)
  --fetch from the stage,
    check out, set origin------> spack at the version named        changed
  --spack --version------------> failure if it does not run (FR-008)
  (the staged copy is removed in every case)
```

A site's files are those at the path that git does not track:
`git ls-files --others`, with ignored ones included. Edited files are
Spack's own files that differ from HEAD: `git status --porcelain
--untracked-files=no`.

## What the module returns, added

| Key | Value |
| --- | --- |
| `moved_from` | after a move (or in check mode, before one): the tag, branch or commit HEAD was at, and what `spack --version` printed then. Absent otherwise |
| `changed` | true for a move too |
| `found` | `spack`, as 004 |

## The role's flag for check mode

`spack_setup_not_installed` (spec 004) is set by a `spack` step in check mode
that would install **or move**: the steps after it are recorded as not
previewed, with "Spack is not installed or moved yet: check mode does not
change it, so this step cannot be previewed".
