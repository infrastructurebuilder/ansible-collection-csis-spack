# Specs

The work on the collection `infrastructurebuilder.csis_spack` is planned
here, with Spec Kit, one directory per spec: `spec.md` (what and why),
`plan.md` (how) and `tasks.md` (the steps, ticked as they are done). The
rules every spec is held to are in the
[constitution](../.specify/memory/constitution.md). A spec is done when its
tasks are ticked, `just full-test` passes, and its `spec.md` says so in its
Status line.

**Converged** is the result of the last `/speckit-converge` run on a spec:
✅ when it found the code matching the spec, its plan and its tasks; ❌ when
it appended tasks, or when converge has never been run on that spec. **Last
converge check** is the date of that run.

## In the order they were built

| # | Spec | Converged | What | Branch | Tasks | Released in | Last converge check |
| ---: | --- | --- | --- | --- | ---: | --- | --- |
| 1 | [002](002-setup-executable-rename/spec.md) | ❌ | The `setup` role's Spack executable is named `spack_setup_executable`; the old `spack_setup_spack` still works. **Complete**, 2026-11-17 | `feature/setup-executable-rename` (until the history reset of 2026-11-18) | 14 | 0.0.1 | never |
| 2 | [001](001-galaxy-publish/spec.md) | ❌ | The collection is published to Ansible Galaxy, from its tag, by `just publish` or the publish workflow. **Complete**, 2026-11-19 | `feature/galaxy-publish` (until the history reset of 2026-11-18) | 22 | 0.0.1, 0.0.2 | never |
| 3 | [003](003-mirror-keys-yes-to-all/spec.md) | ✅ | `spack_gpg_key`'s `from_mirrors` answers Spack 1.2's trust question; the collection works on Spack 1.0, 1.1 and 1.2 (a version table, tests against all three); `yes_to_all` on every module and the `setup` role. **Complete and released**, 2026-11-25 | `feature/mirror-keys-yes-to-all` | 45 | 0.0.3 | 2026-11-25 |

Specs 001 and 002 were finished before `/speckit-converge` was used here;
running it on them would give them a mark and a date.

## Standing beside them

- The Cloud Sandbox (`Cloud-Sandbox`, its own workspace) installs the
  collection from Ansible Galaxy and plans its own work in its own `specs/`.
  Its move to 0.0.3 and back to `from_mirrors` is its work, not a spec here.
- Nothing else is planned. New work starts with `/speckit-specify`.
