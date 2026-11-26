# Interface contract: the `spack` step and `spack_checkout`

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)

Names as confirmed by the operator on 2026-11-26.

## Module `infrastructurebuilder.csis_spack.spack_checkout`

```yaml
- name: Put Spack v1.2.0 at /opt/spack
  infrastructurebuilder.csis_spack.spack_checkout:
    version: v1.2.0                      # required: tag, branch, or full commit hash
    path: /opt/spack                     # required, absolute
    source: https://github.com/spack/spack.git   # the default
```

Fails with nothing changed when: the version is a short hash; `path` holds a
Spack at another version; `path` exists, is not empty, and is not a Spack;
`git` is not found; `git` fails (the version is not in the source, the
source cannot be reached); the Spack installed reports a version below 1.0
or none.

## The step, in the `setup` role

```yaml
spack_setup:
  - kind: spack                # only as the first step
    version: v1.2.0
    path: /opt/spack
    # source: https://git.example.org/mirrors/spack.git
  - kind: config               # runs /opt/spack/bin/spack
    settings:
      config:
        build_jobs: 8
```

`spack_setup_executable` is not needed with a `spack` step. Set to anything
but `spack` or `/opt/spack/bin/spack`, it makes the role refuse the list.

## What is run on the node

All as argument lists; no shell.

| Case | Commands |
| --- | --- |
| Finding the state | `git -C <path> rev-parse --show-toplevel`; `git -C <path> rev-parse HEAD`; `git -C <path> symbolic-ref -q --short HEAD`; `git -C <path> rev-parse -q --verify refs/tags/<version>^{commit}` |
| Install, tag or branch | `git clone --quiet --depth 1 --branch <version> <source> <target>` |
| Install, full hash | `git init --quiet <target>`; `git -C <target> fetch --quiet --depth 1 <source> <hash>`; `git -C <target> checkout --quiet --detach FETCH_HEAD`; `git -C <target> remote add origin <source>` |
| The version check, every run | `<target>/bin/spack --version` |

`<target>` is `path` when it was an empty directory, and otherwise a new
temporary directory in `path`'s parent, renamed to `path` after the check.

## Results recorded by the role

Each step's entry in `spack_setup_results`, as today. A step not carried out
in check mode after an install that has not happened:

```yaml
- step: 2
  kind: config
  label: "config: config"
  changed: false
  result:
    changed: false
    previewed: false
    msg: "Spack is not installed yet: check mode does not install it, so this step cannot be previewed"
```
