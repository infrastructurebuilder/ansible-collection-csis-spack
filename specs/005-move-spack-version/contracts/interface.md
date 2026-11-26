# Interface contract: `move` on `spack_checkout` and the `spack` step

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)

Names as the operator confirmed them on 2026-11-26.

## Module

```yaml
- name: Move the Spack at /opt/spack to v1.2.0
  infrastructurebuilder.csis_spack.spack_checkout:
    version: v1.2.0
    path: /opt/spack
    move: true            # default false: another version at the path fails the task
```

## The step

```yaml
spack_setup:
  - kind: spack
    version: v1.2.0
    path: /opt/spack
    move: true
```

## What a move runs

All as argument lists; no shell. `<stage>` is a new directory
`.<name>.move-*` beside the path, removed afterwards in every case.

| Step | Commands |
| --- | --- |
| Edited files | `git -C <path> status --porcelain --untracked-files=no` |
| Stage | as spec 004's install, into `<stage>` |
| Staged version | `<stage>/bin/spack --version` |
| Compare | `git -C <stage> ls-tree -r --name-only HEAD`; `git -C <path> ls-files --others`; `git -C <path> ls-files --others --ignored --exclude-standard` |
| Kind of version | `git -C <stage> symbolic-ref -q HEAD` (a branch if it succeeds) |
| Fetch, tag | `git -C <path> fetch --quiet --depth 1 file://<stage> refs/tags/<v>:refs/tags/<v>` |
| Fetch, branch | `git -C <path> fetch --quiet --depth 1 file://<stage> refs/heads/<b>:refs/remotes/origin/<b>` |
| Fetch, commit | `git -C <path> fetch --quiet --depth 1 file://<stage> <hash>` |
| Check out | `git -C <path> checkout --quiet --detach '<v>^{commit}'`, or `-B <b> origin/<b>`, or `--detach FETCH_HEAD` |
| Origin | `git -C <path> remote set-url origin <source>` |
| Moved version | `<path>/bin/spack --version` |

In check mode only spec 004's reads run.

## Failures, each with nothing at the path changed

| Case | The message names |
| --- | --- |
| `move` off, another version | as spec 004 |
| Edited files | the files |
| Version not in the source | the version and git's message |
| Staged version below 1.0 | what it printed |
| A site's file the new version tracks | the files |
