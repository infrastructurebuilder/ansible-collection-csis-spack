# Coverage: `ATTIC/COLL-INPROGRESS/COLL-STAGE-5.md` into spec 001

For the operator; not part of the spec. Every paragraph, bullet, table row
and block of the source, in its order, and where it is now carried. The
source's lines in `ATTIC/PLAN.md` follow it. Line numbers are those of the
files on 2026-11-28 (the source has 140 lines).

The spec was made from this stage on 2026-11-17 ("Converted … from
collection stage 5", [spec.md](../../001-galaxy-publish/spec.md), Input).
"spec", "plan" and "tasks" below are the files of
[specs/001-galaxy-publish/](../../001-galaxy-publish/spec.md).

## The source file

| Lines | Source | Carried in |
| --- | --- | --- |
| 1 | Title: "Collection stage 5: Ansible Galaxy, or not" | spec: Input, which quotes it |
| 3–8 | Status: planned 2026-11-14 on `feature/remaining-plans`; begun 2026-11-16 on "do coll 5", on `feature/galaxy-publish`; items 2 and 3 prepared; the upload and item 4 waiting for the namespace, which the operator began claiming on 2026-11-16 | spec: Input (planned 2026-11-14, begun 2026-11-16), Feature Branch, Assumptions (the namespace); tasks: T011 ("requested 2026-11-16"). The branch `feature/remaining-plans` is **not carried**: a branch removed by the history reset of 2026-11-18 |
| 8–12 | Its place in the Cloud Sandbox's order of work: after the live proof and before any relocation, because a relocated `sandbox-provisioning` names the collection's source in its `requirements.yml` | **Not carried**: the Cloud Sandbox's work, recorded in that repository (its `PLAN.md`) |
| 14 | Heading "Why" | spec: User Story 1, "Why this priority" |
| 16–20 | The Cloud Sandbox installs from git at a tag, by the operator's decision, "until we decide if we are going to migrate to Ansible Galaxy" (sandbox stage 10); it works, because the repository is public | spec: User Story 1, "Why this priority" (only from git at one tag); User Story 4. The quotation and "sandbox stage 10" are **not carried**: the Cloud Sandbox's record |
| 22–23 | The table's head: git tag (today) against Ansible Galaxy | spec: User Story 1, "Why this priority" |
| 24 | How a playbook names it: the URL, `type: git` and one version, against the name and a range | spec: User Story 1 (by name with a range), FR-001 |
| 25 | What is installed: built from the files at the tag, against the tarball made by `just build` | spec: FR-002, Key Entities ("Release tarball") |
| 26 | Version ranges: no, against yes | spec: User Story 1, FR-001; Outcome ("A range picks up a later release") |
| 27 | Found by others: no, against yes, by search | spec: User Story 1, "Why this priority" ("not found by search") |
| 28 | What Galaxy needs: the namespace, owned by an account of the operator's choosing; an API key kept as a secret; a release step that publishes | spec: Key Entities (Namespace, API token), FR-003, FR-005 |
| 29 | On a node with no access to GitHub: fails, against works if Galaxy is reachable | spec: User Story 1, "Why this priority" ("it fails on a node that cannot reach GitHub"), SC-001 |
| 31–40 | The decision, with its three choices: stay on the git tag (the default; both repositories record why), publish to Galaxy, or a private Automation Hub | spec: Clarifications, Session 2026-11-16, first question, with the three choices. The form of the prompt (**YOUR DECISION**, which is the default) is **not carried**: the form of a decision prompt |
| 42 | Heading "Work, if the collection is published" | plan: "What remains, and its order"; tasks: the phases |
| 44–47 | Item 1, the namespace: the operator claims `infrastructurebuilder` (tied to a GitHub organisation or user; only its owner can claim it) and makes an API key; nothing here can do that for them | spec: Key Entities (Namespace), Assumptions (first bullet); tasks: T011 |
| 48–52 | Item 2, publishing: a step after the tarball runs `ansible-galaxy collection publish` with the key read from the environment, never from a file; only when the key is set; refusing a version already there | spec: FR-003, FR-004, FR-005, FR-006; plan: "How it works" (`tools/publish.py`) |
| 53–55 | Item 2's decision: where it runs, the operator's machine (the default) or a workflow on a tag with the key as a secret | spec: Clarifications, Session 2026-11-16, second question. The default is **not carried**: the form of a decision prompt |
| 56–58 | Item 3, the first upload: 0.3.1 (or 0.3.0), with `galaxy.yml`'s `documentation` and `homepage` pointing at the repository | `documentation` and `homepage`: spec FR-009; tasks T002. The version is **not carried**: a withdrawn version number; the first upload became 0.0.1 (spec FR-013, Assumptions) |
| 59–64 | Item 4, in the Cloud Sandbox: `requirements.yml` by name with a range; `units.toml` keeping the version; its `tools` test reading the range; a container run from Galaxy; the first-boot template unchanged | spec: User Story 4, SC-006, Outcome ("The Cloud Sandbox installs from Galaxy"); plan: "What remains", item 5; tasks: T017. The first-boot template is **not carried**: the Cloud Sandbox's work, recorded in that repository |
| 66–68 | Heading "Decisions taken", asked 2026-11-16, one at a time | spec: Clarifications, Session 2026-11-16 |
| 70 | Decision 1: publish to Galaxy | spec: Clarifications, Session 2026-11-16, first answer; tasks: T001 |
| 71–74 | Decision 2: both, the operator's machine and a workflow (the operator's own answer, beside the two offered); both run `just publish`, which leaves a version Galaxy has alone, so one published both ways is uploaded once | spec: Clarifications, Session 2026-11-16, second answer (in the same words); SC-003; Edge Cases (published both ways) |
| 76–83 | A change to the plan: the first upload cannot be 0.3.1, because the metadata changes `galaxy.yml`, which is in the tarball, and a published version should be what its tag holds; the first version on Galaxy is the next release (0.3.2), from `develop` | spec: FR-002 (each published version exactly the tarball from its tag); Assumptions ("Before that the plan was 0.3.2, the version after the development tag 0.3.1"). The numbers 0.3.1 and 0.3.2 are carried there as history; the decision of 2026-11-18 made it 0.0.1 (FR-013) |
| 85 | Heading "Outcome so far" | spec: Outcome; plan: Summary ("Built and merged into `develop`") |
| 87–89 | `galaxy.yml`: `homepage`, and `documentation` (the README on `main`, which holds what was released); `tools` and `.github` kept out of the tarball | spec: FR-009 ("the README of what was released"), FR-010; tasks: T002 |
| 90–92 | `just import-check` runs galaxy-importer (0.4.44 then) on the tarball: `ansible-doc` on every plugin, and ansible-lint; 0.3.1's tarball passed it; `just full-test` runs it | spec: FR-008; plan: "How it works" (`just import-check`, "The tarball of the development version 0.3.1 passed it unchanged"), Technical Context (galaxy-importer); tasks: T003 |
| 93–99 | `just publish` runs `tools/publish.py`: it refuses without `GALAXY_API_KEY`, unless HEAD is tagged with `galaxy.yml`'s version, and with changes in the tree; it asks the server's published index (200 has it, 404 not, anything else fails); it runs `ansible-galaxy collection publish` with the key in its environment, never on its command line; `GALAXY_SERVER` names another server | spec: FR-003 to FR-006, FR-012; plan: "How it works", in the same terms; tasks: T005–T007 |
| 100–105 | `.github/workflows/publish.yml`: on a pushed tag such as `0.3.2`, or by hand; `just init`, `just test`, `just publish` with the secret, in the `galaxy` environment (which can be given required reviewers); without the secret it fails, it does not skip; it had not run yet | spec: FR-007, Key Entities (API token); plan: "How it works", in the same terms (the tag pattern `[0-9]+.[0-9]+.[0-9]+`); tasks: T009, T012. Its first run is in spec, Outcome (run 44508677571, by hand on the tag) |
| 106–108 | `tests/unit/test_publish.py` (22 tests then): every refusal, the key off the command line, a version already there, another server, the workflow's trigger and secret, the tags' form | tasks: T005, T010; plan: Testing. The count of 22 is **not carried**: the tests themselves hold what they test, and their number has changed since |
| 109–116 | Ruff checks what `ansible-test sanity`'s pylint checks, as far as it can (the operator's request, 2026-11-16, after a full run stopped on five pylint findings ruff had passed); `pyproject.toml` adds the 73 ruff rules whose pylint code ansible-test 2.16's `collection.cfg` enables; ruff has no rule for `disallowed-name` and `dangerous-default-value`, which only the full test finds | plan: "How it works" ("Ruff mirrors `ansible-test sanity`'s pylint", the two rules ruff lacks); tasks: T004. The count of 73, the five findings and the date of the request are **not carried**: the rules are listed in `pyproject.toml` itself, which is the record of them |
| 117–118 | README: installing (from Galaxy and from a tag) and publishing (both ways); CHANGELOG: an Unreleased section | spec: FR-011; tasks: T008 |
| 120 | Heading "Still to do" | plan: "What remains, and its order" |
| 122–124 | 1. The operator: the namespace granted, an API token, and for the workflow the secret `GALAXY_API_KEY` in the repository or its `galaxy` environment | plan: "What remains", item 1; tasks: T011, T012 (done: an organisation secret, spec Outcome) |
| 125–126 | 2. Release the next version (0.3.2) on the operator's word, and publish it from the tag, one way or the other | spec: FR-014; plan: "What remains", items 2 and 3; tasks: T013, T014. The number 0.3.2 is **not carried** here: a withdrawn plan, replaced by 0.0.1 (spec, Assumptions) |
| 127–129 | 3. Item 4, in the Cloud Sandbox: by name with a range, the `tools` test reading the range, a container run from Galaxy | plan: "What remains", item 5; tasks: T017, T018 |
| 131–133 | Out of scope: publishing anything of the Cloud Sandbox's own | spec: Assumptions, last bullet ("Publishing anything of the Cloud Sandbox's own is out of scope") |
| 135–140 | Acceptance: with "stay", the decision recorded in both repositories; with "publish", `ansible-galaxy collection install infrastructurebuilder.csis_spack` works on a clean machine, and the sandbox's container test passes installing from there | "publish": spec, User Story 1's Independent Test, SC-001, SC-006, Outcome (T015, and the Cloud Sandbox's run). "stay" is **not carried**: the choice not taken |

## Its lines in `ATTIC/PLAN.md`

| Lines | Source | Carried in |
| --- | --- | --- |
| 13–15 | The section's Status: "stage 5 begun 2026-11-16 and carried on as the spec specs/001-galaxy-publish/" | spec: Input ("begun on 2026-11-16", "Converted on 2026-11-17") |
| 40–44 | Stage 5's bullet: Ansible Galaxy, decided 2026-11-16 to publish from the operator's machine and from a workflow on a tag; publishing ready, the first upload waiting for the namespace; carried on as spec 001 | spec: Clarifications, Session 2026-11-16; Assumptions (the namespace); Status and Outcome (since done: 0.0.1 published 2026-11-19) |

## Where the source and the code disagree

- **The first version.** The source has the first upload as 0.3.1, then
  0.3.2 (lines 56, 82, 125). It was 0.0.1, on the operator's decision of
  2026-11-18 (spec, Clarifications, Session 2026-11-18; FR-013).
- **The workflow's tag.** The source's example tag is `0.3.2` (line 101).
  The workflow matches any bare version (plan, "How it works"), and the
  first one it published was 0.0.1, started by hand (spec, Outcome).
- **"It has not run"** (line 104). It has, since 2026-11-19: spec, Outcome.

Each is carried as built, and the spec says how it came to be.

## Could not place

Nothing. Every paragraph, bullet and table row of the source is carried
above, or left out for one of the reasons in
[../data-model.md](../data-model.md).
