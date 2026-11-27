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

| # | Spec | Converged | Serves | Ends in | State | Needs first | Branch | Tasks | Released in | Last converge check |
| ---: | --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| 1 | [002 The setup role's Spack executable is named `spack_setup_executable`](002-setup-executable-rename/spec.md) | ✅ | whoever reads or writes a site's configuration for the `setup` role | a playbook written for 0.3.1 running unchanged, and each of the three cases (new name, old name, both) held by a test | complete 2026-11-17, released in 0.0.1 ([tasks](002-setup-executable-rename/tasks.md)) | nothing | `feature/setup-executable-rename` (until the history reset of 2026-11-18) | 14 | 0.0.1 | 2026-11-25 |
| 2 | [001 The collection is published to Ansible Galaxy](001-galaxy-publish/spec.md) | ✅ | someone writing a playbook; the operator who releases; the Cloud Sandbox | one command installing the collection by name on a clean machine, and a release reaching Galaxy by one action of the operator's | complete 2026-11-19: 0.0.1 published, and the Cloud Sandbox installs it from Galaxy; 0.0.2 proved the last two checks ([tasks](001-galaxy-publish/tasks.md)) | nothing | `feature/galaxy-publish` (until the history reset of 2026-11-18) | 22 | 0.0.1, 0.0.2 | 2026-11-25 |
| 3 | [003 `spack_gpg_key` trusts the mirrors' keys without a prompt](003-mirror-keys-yes-to-all/spec.md) | ✅ | a site whose play trusts its mirrors' keys; a site on Spack 1.0 or 1.1; a site whose Spack commands ask before acting | a `from_mirrors` step finishing with no prompt and reporting no change the second time, and the integration tests passing against the real Spack 1.0.0, 1.1.0 and 1.2.0 | complete 2026-11-25: merged (`058744b`), released in 0.0.3 on Ansible Galaxy, converged; also the version table for Spack 1.0 and 1.1, and `yes_to_all` ([tasks](003-mirror-keys-yes-to-all/tasks.md)) | nothing | `feature/mirror-keys-yes-to-all` | 45 | 0.0.3 | 2026-11-25 |
| 4 | [004 A `setup` step that installs Spack](004-install-spack/spec.md) | ✅ | a site whose nodes have no Spack yet; a site whose nodes already have one; a site whose nodes cannot reach the internet | one application of the role, with an install step first, leaving a working Spack at the version named and every later step applied, and a second application reporting no change | complete 2026-11-26: merged (`83c76d3`), converged; not released ([tasks](004-install-spack/tasks.md)) | nothing | `feature/install-spack` | 34 | | 2026-11-26 |
| 5 | [005 The install step moves a Spack to another version, when a site asks](005-move-spack-version/spec.md) | ✅ | a site moving its nodes to a new Spack | one changed version, with the move allowed, moving a node's Spack in one application, a second reporting no change, and nothing a site added or edited lost | complete 2026-11-27: merged (`0b7babe`), converged; not released ([tasks](005-move-spack-version/tasks.md)) | 004 | `feature/move-spack-version` | 24 | | 2026-11-27 |
| 11 | [011 Previewing a long build: `async` and check mode (retrospective)](011-preview-long-builds/spec.md) | ✅ | a site that previews a long build in check mode | every example of `async` in the form that previews, held by a test | complete 2026-11-14, retrospective written 2026-11-27; released as 0.3.1 (withdrawn), its work in 0.0.1; converged ([tasks](011-preview-long-builds/tasks.md)) | 010 | `feature/preview-long-builds` | 19 | 0.0.1 | 2026-11-27 |

Specs 001 and 002 were finished before `/speckit-converge` was used here,
and were first checked with it on 2026-11-25, after the fact.

## Standing beside them

- The Cloud Sandbox (`Cloud-Sandbox`, its own workspace) installs the
  collection from Ansible Galaxy and plans its own work in its own `specs/`.
  Its move to 0.0.3 and back to `from_mirrors` is its work, not a spec here.
- Spec 005 changes spec 004's step, which is merged. Pinning Spack's package
  recipes is to be a spec of its own, not yet written.
- New work starts with `/speckit-specify`.
