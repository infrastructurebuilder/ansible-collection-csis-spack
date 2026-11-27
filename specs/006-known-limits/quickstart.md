# Quickstart: seeing it work

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Everything runs on your local machine, from the repository root, on the
branch `feature/known-limits`.

```sh
just unit -k "relative or index"          # the new unit tests, while working
just integration -k "relative or index"   # the same against the real Spack 1.0.0, 1.1.0, 1.2.0
just test
just full-test
```

## The preview

An environment beside a file it includes:

```text
site/
├── shared.yaml          # config: {build_jobs: 5}
└── env/
    ├── extra.yaml       # config: {build_jobs: 3}
    └── spack.yaml       # include: [./extra.yaml, ../shared.yaml]
```

`spack_env` with `path: site/env`, in check mode: before this spec, it
failed with `Required path (../shared.yaml) does not exist`; after, it
previews, and after a real concretize a second preview reports no change.

## The index

`spack_buildcache_push` with `update_index: true`, run twice on the same
environment and mirror: the second run reports no change, and the mirror's
`v3/manifests/index/index.manifest.json` is not rewritten (on Spack 1.0, 1.1
and 1.2, as Spack has always done; research R1).
