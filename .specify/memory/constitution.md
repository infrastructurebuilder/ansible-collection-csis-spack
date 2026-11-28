# infrastructurebuilder.csis_spack Constitution

This is the constitution of the Ansible collection
`infrastructurebuilder.csis_spack`, which manages Spack from Ansible. It says
what every specification, plan and change in this repository is held to. "The
operator" is the person who owns this repository and directs the work. "An
agent" is any coding agent working in it.

## Core Principles

### I. A Site's Choices Are Configuration, Not Code

The collection can set Spack up for any site. What a particular site wants
(its packages, compilers, versions, paths, mirrors and module names) is given
to the collection as configuration. None of it is built into the plugins or
the role.

"Site" here means an installation that uses the collection, such as the Cloud
Sandbox. It does not mean Spack's `site` configuration scope, which the
collection supports like any other scope.

- No package, compiler, version, path, mirror or module name of any site
  appears in `plugins/` or in a role. The `setup` role's list of steps is
  empty by default: the role has no step of its own built in.
- What a site wants is passed in as configuration: options of a module, or the
  list of steps given to the `setup` role.
- A site's choices appear only in `docs/examples/` and in tests, as examples.
- `tests/unit/test_no_site_knowledge.py` holds the collection to this. A change
  that needs that test loosened needs an amendment here first.

**Why:** a collection that carries one site's choices has to be changed for
every other site.

### II. A Repeat Run Changes Nothing, and Says So

- A module reports `changed` only when it changed something on the node.
- A second run with the same input changes nothing and reports no change.
- Every module supports check mode. In check mode it reports what would change
  and touches nothing: not the environment, not Spack's configuration, not a
  mirror.
- Where an option makes a repeat run do work on purpose (`force`, `always`),
  its documentation says so.
- A task that builds for hours runs under `async`. Ansible refuses `async`
  together with check mode, so every example gives `async` and `poll` in the
  form that previews: `"{{ 0 if ansible_check_mode else <seconds> }}"`.

**Why:** a playbook is run again and again. A run that reports a change that
did not happen, or changes something in a preview, cannot be trusted.

### III. Written to What Spack Does

- A module calls Spack's own commands, and uses their machine-readable output
  where Spack has one. It does not read or write Spack's files behind Spack's
  back where a command exists.
- A module never runs Spack through a shell.
- Before a module is written or changed, the Spack behaviour it relies on is
  tried against the real Spack, and what was found is recorded in the spec's
  research. The stand-in `spack` used by the unit tests follows what the real
  one did, not what its help text suggests.
- The collection supports Spack 1.0 or later and is tested against the pinned
  version (v1.2.0 when this was ratified). Moving the pin is a change with a
  spec of its own.

**Why:** Spack's command line and output change between versions. A module
written from memory or from documentation reports wrongly without failing.

### IV. Acceptance Tests Run Through the Justfile

This repository's acceptance tests are two `Justfile` targets, `just test` and
`just full-test`. A change is accepted when they pass, and not before.

- Every check is run through the `Justfile`, never by calling the tool under
  it directly. A check the `Justfile` lacks is added to it.
- `just test` passes after every change: lint, type-check with 0 errors, the
  unit tests, and a build that installs.
- `just full-test` passes before a spec is called done and before any release:
  the integration tests against the real Spack, `ansible-test sanity`, and
  Galaxy's own import checks.
- New behaviour comes with tests at the level that proves it: unit tests
  against the stand-in `spack` for every option, for change reporting both
  ways, for check mode and for failure; an integration test where the claim is
  about the real Spack.
- What the documentation promises is held by a test where it can be: examples
  are run or read by the tests.
- A failure caused by an expired credential or an unreachable service is
  reported as environmental, apart from a failure of the code.

**Why:** acceptance tests that are named targets stay the same between runs
and between people.

### V. The Operator Decides

- A choice that is the operator's to make is asked of the operator before work
  depends on it, and the answer is recorded in the spec. An agent does not pick
  for them, and follows the answer given even when it is none of the options
  offered.
- An agent commits locally. Merging into `develop`, pushing a branch or a tag,
  cutting a release and publishing each happen only on the operator's word, and
  one approval does not carry over to the next.
- Pushing a release tag publishes to Ansible Galaxy. An agent says so before
  any tag is pushed.
- No secret is ever in the repository or on a command line. Keys and tokens are
  read from the environment or from a repository secret.
- When work finds a defect in a released version, it is fixed here, and the
  operator is asked whether to release it as a patch version.

**Why:** the operator reviews each plan and owns each decision before work is
spent on it; and a push, a release or an upload cannot be taken back.

## Technical Constraints

- **What is shipped:** an Ansible collection, namespace `infrastructurebuilder`,
  name `csis_spack`, under GPL-3.0-or-later.
- **Runs on:** ansible-core 2.16 or later, tested with the 2.16 series on
  Python 3.12, because RHEL 10 ships 2.16. Spack 1.0 or later on the managed
  node.
- **Tools:** `uv` for the tool environment, `ruff`, `pyright`, `pytest`,
  `ansible-test`, `galaxy-importer`, all behind `just`.
- **The tarball** holds what a user of the collection needs and nothing else.
  Development material is listed in `galaxy.yml`'s `build_ignore`: the tools,
  the workflows, `specs/`, `.specify/`, `.claude/`.
- **Versions** follow semantic versioning. A release tag is the bare version,
  as `0.0.1`, never `v0.0.1`. A published version is exactly what its tag
  holds, and a version already published is never uploaded again.
- **Documentation** is part of a change: each module's `DOCUMENTATION`,
  `EXAMPLES` and `RETURN`, the README, and `CHANGELOG.md`. In documentation,
  choose a little more explanation over a little less.

## Development Workflow

This repository uses Spec Kit, and nothing else, to plan and track work.

- **Every change larger than a small fix has a spec** under
  `specs/<number>-<short-name>/`: `spec.md` (what and why), `plan.md` (how),
  `tasks.md` (the steps, ticked as they are done). They are made with
  `/speckit-specify`, `/speckit-plan` and `/speckit-tasks`, and carried out
  with `/speckit-implement`.
- **Open questions are settled before planning**, with `/speckit-clarify` or
  by asking the operator, and recorded in the spec under Clarifications
  (principle V).
- **`plan.md` checks the plan against this constitution** before any work, and
  again after the design. A plan that breaks a principle says so and why under
  Complexity Tracking, or is changed.
- **There is no `PLAN.md`.** The one this repository had was closed on
  2026-11-17; the work it planned is recorded in the specs 007 to 011 and
  001, and none is created again. A rule elsewhere that says plans go in
  `PLAN.md` is met in this repository by a spec.
- **Branches:** one git-flow feature branch per spec, `feature/<short-name>`,
  from `develop`. It is finished with a squash-merge into `develop` and kept,
  never deleted. After a finish, `git diff develop feature/<short-name>` is
  empty. Spec Kit's own numbered branches are not used: a spec's directory
  name and its branch's name are independent.
- **A spec is done** when its tasks are ticked, `just full-test` passes, and
  its `spec.md` says so in its Status line.

## Governance

- This constitution is above every other practice in this repository. Where a
  spec, a plan, a template or a habit disagrees with it, this document is
  right, or it is amended.
- **Amending it:** only the operator amends it, or an agent on the operator's
  instruction, with `/speckit-constitution`. An amendment says what changed and
  why, and changes whatever in the open specs it makes untrue.
- **Its version** follows semantic versioning: MAJOR when a principle is
  removed or redefined so that earlier work would break it; MINOR when a
  principle or section is added or materially widened; PATCH for wording.
- **Compliance:** every `plan.md` carries a Constitution Check. A review of a
  change checks it against the principles. `/speckit-analyze` is run when a
  spec, its plan and its tasks may have drifted apart.
- **Guidance for a session** is in [CLAUDE.md](../../CLAUDE.md), which points
  here and adds nothing of its own.

**Version**: 1.1.0 | **Ratified**: 2026-11-17 | **Last Amended**: 2026-11-28
