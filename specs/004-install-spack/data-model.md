# Data Model: A `setup` step that installs Spack

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

The names below are the ones the plan proposes (kind `spack`, module
`spack_checkout`), for the operator to confirm.

## The step

A mapping in `spack_setup`:

| Field | Required | Type | Rule |
| --- | --- | --- | --- |
| `kind` | yes | `spack` | |
| `version` | yes | string | A tag or a branch of the source, or a commit's full 40-digit hash. A hexadecimal string of 7 to 39 digits is refused: "give the commit's full hash". |
| `path` | yes | string | Absolute. Its parent is made if it is missing. |
| `source` | no | string | A git repository's address. Default `https://github.com/spack/spack.git`. |
| `label` | no | string | As every step. |
| `environment` | no | name or mapping | As every step: what `git` and `spack --version` run in (a proxy, a certificate). |

Not allowed: `yes_to_all`, `scope`, and every other kind's options.

## Where the step may be (checked before any step runs)

- At most one `spack` step in a list, and only as its first step.
- `spack_setup_executable` is `spack` (its default, also when the old name
  `spack_setup_spack` is not set), or exactly `<path>/bin/spack` after
  normalising both; anything else is refused, naming both.

## The executable the later steps run

`setup_executable(steps, executable)`:

- the first step is a `spack` step: `<path>/bin/spack`;
- otherwise: `executable` (`spack_setup_executable`), as today.

## The states of the path

Read in this order; the first that holds decides.

| State | How it is told (research R3, R4) |
| --- | --- |
| `nothing` | `path` does not exist |
| `empty` | `path` is a directory with no entries |
| `spack` at the version | `git -C path rev-parse --show-toplevel` is `path`, `path/bin/spack` exists, and: for a full hash, `rev-parse HEAD` is it; otherwise `symbolic-ref --short HEAD` is the version, or `refs/tags/<version>` exists and its commit is HEAD |
| `spack` at another version | as above, but the last test fails |
| not a Spack | anything else |

## What happens, by state

```text
nothing  --install beside, check, rename-->  spack at the version   changed
empty    --install in place, check------->  spack at the version   changed
spack at the version  --check------------>  (the same)             not changed
spack at another version  --------------->  failure, nothing changed
not a Spack  ---------------------------->  failure, nothing changed
```

"Check" is `path/bin/spack --version`: its first word must be a version of
1.0 or later. In check mode the arrows that install are reported and not
taken.

## The role's flag for check mode

`spack_setup_not_installed`: false at the start; set true by the `spack`
step when it runs in check mode and reports an install. While it is true,
later steps are not carried out and are recorded with `changed: false`,
`previewed: false` and the reason.

## What the module returns

| Key | Value |
| --- | --- |
| `changed` | true only for an install |
| `path` | as given |
| `spack` | `<path>/bin/spack` |
| `version` | as given |
| `spack_version` | what `spack --version` printed (absent in check mode before an install) |
| `found` | `nothing`, `empty` or `spack` |
