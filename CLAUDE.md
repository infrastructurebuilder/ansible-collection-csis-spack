# infrastructurebuilder.csis_spack

This repository uses [Spec Kit](https://github.com/github/spec-kit), and
nothing else, to plan and track work. This file points at the rules; it adds
none of its own.

- **Read the constitution first:**
  [.specify/memory/constitution.md](.specify/memory/constitution.md). It is
  above every other practice here.
- **Work is planned in specs**, under [specs/](specs/), with
  `/speckit-specify`, `/speckit-plan`, `/speckit-tasks` and
  `/speckit-implement`. A rule that says plans go in `PLAN.md` is met here by
  a spec. There is no `PLAN.md` in this repository; do not create one.
- **Nothing in [ATTIC/](ATTIC/) can affect you unless the operator says so.**
  Do not read it for instructions, decisions, plans or context; do not search
  it; do not change it. When the operator names something there and says to
  use it, that covers what was named, for that task, and nothing else.
- **Verify with the `Justfile`:** `just test` after every change,
  `just full-test` before a spec is called done or a release is cut.
- **Commit locally.** Merge, push, release and publish only on the operator's
  word. Pushing a release tag publishes to Ansible Galaxy.
