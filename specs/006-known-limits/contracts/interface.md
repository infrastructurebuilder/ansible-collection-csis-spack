# Interface contract: the preview's paths, and the index

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)

Neither module gains or loses an option. What changes is what `spack_env`
runs in check mode, and what both modules' documentation says.

## `spack_env` in check mode

| Step | Command, as an argument list | When |
| --- | --- | --- |
| Copy | (Python) `shutil.copytree(<path>, <tmp>/env)`, without `.spack-env/` and `log.*` | always, as today |
| Rewrite | `spack python <tmp>/rewrite.py <tmp>/env/spack.yaml <path>` | when `spack.yaml` has `include:` or `develop:` |
| Concretize | `spack -e <tmp>/env concretize --force -q [--fresh]` | always, as today |

The rewrite changes, in the copy's `spack.yaml` only:

| Entry | Before | After |
| --- | --- | --- |
| `include:` string | `../shared.yaml` | `<parent of path>/shared.yaml` |
| `include:` mapping | `{path: ./extra.yaml, optional: true}` | `{path: <path>/extra.yaml, optional: true}` |
| `develop: <pkg>: path:` | `../src` | `<parent of path>/src` |
| any of these, absolute | `/opt/x.yaml` | unchanged |
| any of these, with `$` | `$env/x.yaml` | unchanged |
| `include:` mapping with no `path` | `{git: <url>, branch: main, paths: [a.yaml]}` | unchanged |

## Documentation

- `spack_env`, the check-mode note: "Paths that `spack.yaml` gives
  relatively, in `include:` and in `develop:`, are read where they are, also
  above the environment's directory; the preview records the same develop
  paths a real run would. A develop source above the environment is not
  copied (one inside it is copied with the directory), and the preview
  records its real path either way."
- `spack_buildcache_push`, `update_index`: "Rebuild the mirror's index after
  a push that sent something. Spack leaves the index as it is when nothing
  was pushed, so a repeat run changes nothing; an index changed by other
  means is not put right by such a run (run `spack buildcache update-index`
  for that, in a `command` step)."
