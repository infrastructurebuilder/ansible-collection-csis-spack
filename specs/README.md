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
| 1 | [007 The first modules: an environment, and a build cache (retrospective)](007-first-modules/spec.md) | ✅ | a site that builds a Spack environment from a playbook and pushes it to a build cache | `spack_env` and `spack_buildcache_push` against the real Spack: a second run changing nothing, check mode touching nothing | complete 2026-11-13, retrospective written 2026-11-27, merged (`0c2dbb0`); released as 0.1.0 (withdrawn), its work in 0.0.1; converged ([tasks](007-first-modules/tasks.md)) | nothing | `feature/first-modules` | 22 | 0.0.1 | 2026-11-27 |
| 2 | [008 Repeat runs that do nothing and say so (retrospective)](008-repeat-runs-say-so/spec.md) | ✅ | a site that runs its build playbook again and again; a site that pushes to a mirror | a repeat run leaving every module file alone, and a push reporting exactly what the mirror gained | complete 2026-11-14, retrospective written 2026-11-27, merged (`7a48607`); released as 0.2.0 (withdrawn), its work in 0.0.1; converged ([tasks](008-repeat-runs-say-so/tasks.md)) | 007 | `feature/repeat-runs-say-so` | 22 | 0.0.1 | 2026-11-27 |
| 3 | [009 Setting Spack up from one piece of configuration: the `setup` role (retrospective)](009-setup-role/spec.md) | ✅ | a site whose Spack set-up is a shell script; any site, whose choices are configuration | a site's script as one list of steps, applied twice with no change the second time, and no site's names in the collection | complete 2026-11-14, retrospective written 2026-11-27, merged (`06bf139`); released as 0.3.0 (withdrawn), its work in 0.0.1; converged ([tasks](009-setup-role/tasks.md)) | 008 | `feature/setup-role` | 52 | 0.0.1 | 2026-11-27 |
| 4 | [010 The Cloud Sandbox moves to the `setup` role (retrospective)](010-sandbox-adopts-setup/spec.md) | ✅ | the Cloud Sandbox; a site that adopts the role in place of its shell | the sandbox's container test, with the real oneAPI, applying the role twice with no change the second time; the collection unchanged | complete 2026-11-14, retrospective written 2026-11-27, merged (`b290cce`); the work was the Cloud Sandbox's stage 11; T029 and T030 (FR-005 tested and documented) done after converge; converged ([tasks](010-sandbox-adopts-setup/tasks.md)) | 009 | `feature/sandbox-adopts-setup` | 30 |  | 2026-11-27 |
| 5 | [011 Previewing a long build: `async` and check mode (retrospective)](011-preview-long-builds/spec.md) | ✅ | a site that previews a long build in check mode | every example of `async` in the form that previews, held by a test | complete 2026-11-14, retrospective written 2026-11-27, merged (`e16159d`); released as 0.3.1 (withdrawn), its work in 0.0.1; converged ([tasks](011-preview-long-builds/tasks.md)) | 010 | `feature/preview-long-builds` | 19 | 0.0.1 | 2026-11-27 |
| 6 | [002 The setup role's Spack executable is named `spack_setup_executable`](002-setup-executable-rename/spec.md) | ✅ | whoever reads or writes a site's configuration for the `setup` role | a playbook written for 0.3.1 running unchanged, and each of the three cases (new name, old name, both) held by a test | complete 2026-11-17, released in 0.0.1 ([tasks](002-setup-executable-rename/tasks.md)) | nothing | `feature/setup-executable-rename` (until the history reset of 2026-11-18) | 14 | 0.0.1 | 2026-11-25 |
| 7 | [001 The collection is published to Ansible Galaxy](001-galaxy-publish/spec.md) | ✅ | someone writing a playbook; the operator who releases; the Cloud Sandbox | one command installing the collection by name on a clean machine, and a release reaching Galaxy by one action of the operator's | complete 2026-11-19: 0.0.1 published, and the Cloud Sandbox installs it from Galaxy; 0.0.2 proved the last two checks ([tasks](001-galaxy-publish/tasks.md)) | nothing | `feature/galaxy-publish` (until the history reset of 2026-11-18) | 22 | 0.0.1, 0.0.2 | 2026-11-25 |
| 8 | [003 `spack_gpg_key` trusts the mirrors' keys without a prompt](003-mirror-keys-yes-to-all/spec.md) | ✅ | a site whose play trusts its mirrors' keys; a site on Spack 1.0 or 1.1; a site whose Spack commands ask before acting | a `from_mirrors` step finishing with no prompt and reporting no change the second time, and the integration tests passing against the real Spack 1.0.0, 1.1.0 and 1.2.0 | complete 2026-11-25: merged (`058744b`), released in 0.0.3 on Ansible Galaxy, converged; also the version table for Spack 1.0 and 1.1, and `yes_to_all` ([tasks](003-mirror-keys-yes-to-all/tasks.md)) | nothing | `feature/mirror-keys-yes-to-all` | 45 | 0.0.3 | 2026-11-25 |
| 9 | [004 A `setup` step that installs Spack](004-install-spack/spec.md) | ✅ | a site whose nodes have no Spack yet; a site whose nodes already have one; a site whose nodes cannot reach the internet | one application of the role, with an install step first, leaving a working Spack at the version named and every later step applied, and a second application reporting no change | complete 2026-11-26: merged (`83c76d3`), released in 0.0.4 on Ansible Galaxy, converged ([tasks](004-install-spack/tasks.md)) | nothing | `feature/install-spack` | 34 | 0.0.4 | 2026-11-26 |
| 10 | [005 The install step moves a Spack to another version, when a site asks](005-move-spack-version/spec.md) | ✅ | a site moving its nodes to a new Spack | one changed version, with the move allowed, moving a node's Spack in one application, a second reporting no change, and nothing a site added or edited lost | complete 2026-11-27: merged (`0b7babe`), released in 0.0.4 on Ansible Galaxy, converged ([tasks](005-move-spack-version/tasks.md)) | 004 | `feature/move-spack-version` | 24 | 0.0.4 | 2026-11-27 |
| 11 | [006 Two known limits, said where a site reads them, or removed](006-known-limits/spec.md) | ❌ | a site that rebuilds a mirror's index; a site that previews an environment with files beside it | each limit documented where a site reads it, or removed, and held by a test | merged (`fa647f5`) 2026-11-27, not released; converge appended T020–T022, 19 of 22 done: the preview's relative paths rewritten; the index limit found not to be one, documented and tested ([tasks](006-known-limits/tasks.md)) | nothing | `feature/known-limits` | 22 |  | 2026-11-27 |
| 12 | [012 Remove the ATTIC, because the specs hold everything in it](012-remove-attic/spec.md) | ❌ | a reader or a new session that wants to know why the collection is as it is | every paragraph of the ATTIC carried by a spec, `ATTIC/` removed, and `just full-test` passing without it | drafted 2026-11-27; on `develop` as a draft ([spec](012-remove-attic/spec.md)) | 006, 007–011 | `feature/remove-attic` |  |  | never |
| 13 | [013 The documentation covers every case of the collection](013-documentation-covers-every-case/spec.md) | ❌ | someone writing a playbook | every case in the inventory found in the documentation, and a test failing for one added without it | drafted and clarified 2026-11-27; on `develop` as a draft ([spec](013-documentation-covers-every-case/spec.md)) | 006, 012 | `feature/documentation-covers-every-case` |  |  | never |

Specs 007 to 011 are retrospectives: the work they record was done between
2026-11-13 and 2026-11-14, before this repository adopted Spec Kit, and was
planned then in files now in the ATTIC. They were written from those files
on 2026-11-27, so that every piece of the collection's work has a spec, and
checked against the code with `/speckit-converge` the same day. Specs 001
and 002 were finished before `/speckit-converge` was used here, and were
first checked with it on 2026-11-25, after the fact.

## Standing beside them

- The Cloud Sandbox (`Cloud-Sandbox`, its own workspace) installs the
  collection from Ansible Galaxy and plans its own work in its own `specs/`.
  Its move to 0.0.3 and back to `from_mirrors` is its work, not a spec here.
- Spec 005 changes spec 004's step, which is merged. Pinning Spack's package
  recipes is to be a spec of its own, not yet written.
- Specs 006, 012 and 013 are on `develop` as drafts, so that they can be
  read here; their planning and work go on from their own branches.
- New work starts with `/speckit-specify`.
