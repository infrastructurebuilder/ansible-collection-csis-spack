# Quickstart: seeing it work

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Everything runs on your local machine, from the repository root, on the
branch `feature/move-spack-version`.

## 1. The acceptance tests

```sh
just unit -k move          # the new unit tests alone, while working
just integration -k move   # the move against the real Spack 1.0.0, 1.1.0 and 1.2.0, from the local clones
just test                  # lint, type-check, all unit tests, build and install
just full-test             # everything, about 55 minutes
```

Write the tests first: `just unit -k move` fails because `spack_checkout`
has no option `move`.

## 2. A play, as a site writes it

On a node whose `/opt/spack` holds Spack v1.1.0, installed by the role:

```yaml
spack_setup:
  - kind: spack
    version: v1.2.0
    path: /opt/spack
    move: true
  - kind: config
    settings:
      config:
        build_jobs: 8
```

| Run | The `spack` step | The `config` step |
| --- | --- | --- |
| `--check` | changed: would move from tag v1.1.0 | not previewed, with the reason |
| first | changed: moved, `moved_from` names v1.1.0, `spack_version` 1.2.0 | runs `/opt/spack/bin/spack`, now 1.2.0 |
| second | not changed | not changed |

Without `move: true`, the first run fails as spec 004 says, and `/opt/spack`
is unchanged. With a file of the site's in `/opt/spack/etc/spack/site/`
that v1.2.0 tracks (`README.md`), the move is refused and names it.

Packages and environments built by v1.1.0 are left as they are: concretize
and install them again with steps of your own after this one if they need
it.
