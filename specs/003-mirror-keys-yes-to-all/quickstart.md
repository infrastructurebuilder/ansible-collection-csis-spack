# Quickstart: seeing it work

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Everything runs on your local machine, from the repository root, on the
branch `feature/mirror-keys-yes-to-all`.

## 1. The acceptance tests

```sh
just test          # lint, type-check (0 errors), unit tests, build and install
just full-test     # also the real Spack v1.2.0, ansible-test sanity, Galaxy's checks
```

Expected:

- `just test` passes, including the new unit tests: `spack_gpg_key`'s two
  trusts against a stand-in that behaves as 1.2 and one that behaves as 1.0
  and 1.1 (FR-004, SC-004), and `yes_to_all` on and off for each module and
  for the role (FR-007).
- `just full-test` passes, including the two integration tests of
  `from_mirrors` (FR-003): the module test trusts one key (a change), then
  none (no change), then the second key only; the role test reports a
  change, then none.

## 2. The new tests fail on 0.0.2 (SC-002)

Write the tests first, before the fix, and run `just full-test`. Both
integration tests fail at the `from_mirrors` step with
`Trust key: <fingerprint> [y/N] ==> Error: EOF when reading a line` (exit 3),
the head node's failure ([research.md](research.md), R4).

## 3. Spack 1.0, 1.1 and 1.2 (SC-004, FR-010)

The integration tests run once for each version in
`tests/integration/real_spack.py`'s `SPACK_VERSIONS`, each cloned into
`.tmp/` the first time (the network is needed then, and each version's
first concretization bootstraps its solver):

```sh
just integration   # the integration tests alone, about 35 minutes for the three
just full-test     # everything, about 45 minutes
```

Expected: every test passes on each version, with the same changes
reported. On 1.1 the tests make the user scope's directory first, as a site
must (Spack 1.1 has no scope whose directory is missing; research.md, R8).
0.0.2's modules fail on 1.0 and 1.1 (research.md, R6).

## 4. A play, as a site writes it

```yaml
- hosts: head
  roles:
    - role: infrastructurebuilder.csis_spack.setup
      vars:
        spack_setup:
          - kind: mirror
            name: site
            url: file:///srv/spack-mirror
            type: [binary]
          - kind: gpg_key
            from_mirrors: true       # trusted with no prompt, whatever yes_to_all says
          - kind: command
            yes_to_all: true         # this step only
            args: [gc]
            changes: always
```

The first run reports a change for the `gpg_key` step; a second reports
none. With `yes_to_all` left out, the `gc` step would fail at Spack's
confirmation; with it, Spack is run as `spack gc --yes-to-all`.
