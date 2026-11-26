# Quickstart: seeing it work

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Everything runs on your local machine, from the repository root, on the
branch `feature/install-spack`.

## 1. The acceptance tests

```sh
just test          # lint, type-check (0 errors), unit tests, build and install
just full-test     # also the real Spack 1.0.0, 1.1.0 and 1.2.0, ansible-test sanity, Galaxy's checks
```

Expected:

- `just test` passes, including `tests/unit/test_spack_checkout.py`, which
  runs real `git` against source repositories it makes, and the new cases
  in the filter, role and example tests.
- `just full-test` passes, including the integration tests that install
  each of the three real Spack versions from the local clones in `.tmp/`
  (no network is needed: those clones are the sources).

## 2. The new tests fail first

Write the tests before the module and the role's changes, and run
`just test`: the module's tests fail because there is no `spack_checkout`,
and the filter's and role's because `spack` is not a kind.

## 3. A play, as a site writes it

```yaml
- hosts: build_hosts
  roles:
    - role: infrastructurebuilder.csis_spack.setup
      vars:
        spack_setup:
          - kind: spack
            version: v1.2.0
            path: /opt/spack
          - kind: config
            settings:
              config:
                build_jobs: 8
```

On a node with no `/opt/spack`:

| Run | The `spack` step | The `config` step |
| --- | --- | --- |
| `--check` | changed: would install | not previewed, with the reason |
| first | changed: installed, `spack_version` `1.2.0 (63962ed…)` | changed, run by `/opt/spack/bin/spack` |
| second | not changed | not changed |

Then change `version` to `v1.1.0` and run again: the `spack` step fails,
naming `v1.2.0` found and `v1.1.0` asked, and `/opt/spack` is unchanged.
(Moving it is spec 005's.)
