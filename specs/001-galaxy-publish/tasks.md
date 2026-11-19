---

description: "Task list for publishing the collection to Ansible Galaxy"
---

# Tasks: Publish the collection to Ansible Galaxy

**Input**: Design documents from `/specs/001-galaxy-publish/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md)

**Tests**: included; the constitution asks for them (principle IV).

**Organization**: by user story. The tasks ticked below were done on
2026-11-16 (T019 to T022 on 2026-11-18), and what they made is on `develop`.
They are listed so that this file is the whole record; the work that remains starts at
**YOU ARE HERE**.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: the user story the task belongs to (US1 to US4)
- **OPERATOR**: only the operator can do it, or it waits for the operator's word

## Phase 1: Setup

- [X] T001 Record the two decisions (publish to Galaxy; from both places) in `specs/001-galaxy-publish/spec.md` under Clarifications

---

## Phase 2: Foundational (blocks every story)

**Purpose**: a tarball that Galaxy will accept, with the right metadata.

- [X] T002 [P] Name `homepage` and `documentation` in `galaxy.yml`, and keep `tools` and `.github` out of the tarball with `build_ignore`
- [X] T003 [P] Add `just import-check` to `Justfile` (galaxy-importer on the tarball) and make `just full-test` run it
- [X] T004 [P] Enable in `pyproject.toml` the ruff rules that mirror `ansible-test sanity`'s pylint, so `just test` finds what the full test would

**Checkpoint**: `just full-test` passes with the import check in it.

---

## Phase 3: User Story 2 - Publish a release from the operator's machine (Priority: P2)

**Goal**: one command publishes a release, and refuses whenever the upload
might not be what was released.

**Independent Test**: `tests/unit/test_publish.py` against a stand-in server.

(This story was built before user story 1, because user story 1 needs a
published version to exist.)

- [X] T005 [US2] Write the refusals first as tests in `tests/unit/test_publish.py`: no key, HEAD not at the tag, changes in the tree, a version already there, an unclear answer from the server, the key kept off the command line, another server
- [X] T006 [US2] Write `tools/publish.py` to pass them
- [X] T007 [US2] Add `just publish` to `Justfile`, depending on `import-check`; have `just release` say to publish from the tag
- [X] T008 [US2] Document installing (from Galaxy and from a tag) and publishing (both ways) in `README.md`; add an Unreleased section to `CHANGELOG.md`

**Checkpoint**: `just test` passes; nothing has been uploaded.

---

## Phase 4: User Story 3 - Publish by pushing the release tag (Priority: P3)

**Goal**: a pushed release tag publishes that release.

**Independent Test**: the workflow's trigger and secret are held by
`tests/unit/test_publish.py`; its first real run is T014, if the tag is pushed.

- [X] T009 [US3] Write `.github/workflows/publish.yml`: on a bare-version tag or by hand, `just init`, `just test`, `just publish`, with the secret `GALAXY_API_KEY` in the `galaxy` environment
- [X] T010 [US3] Hold the workflow's trigger, its secret and the form of the tags in `tests/unit/test_publish.py`

**Checkpoint**: the preparation is merged into `develop`.

---

## Phase 4b: The first release is 0.0.1 (decided 2026-11-18)

- [X] T019 Record the decisions in `specs/001-galaxy-publish/spec.md` under Clarifications, and the withdrawn tags under Assumptions
- [X] T020 Delete the development tags 0.1.0, 0.2.0, 0.3.0 and 0.3.1, and their `release/*` branches, locally and on GitHub
- [X] T021 Set the version to 0.0.1 in `galaxy.yml` and `pyproject.toml`; every plugin's `version_added` to 0.0.1; and rewrite `CHANGELOG.md` as one 0.0.1 entry, with a note on the withdrawn versions
- [X] T022 Remove the withdrawn version numbers from the README, the `setup` role's README and defaults, the modules' documentation, the tests, the release tools and the constitution's example (amended to 1.0.1)

---

## YOU ARE HERE

T011 and T013 are done (2026-11-18): the namespace is granted, and 0.0.1 is
cut and tagged locally. Next is T014, the upload, on the operator's word.

---

## Phase 5: User Story 1 - Install the collection by name (Priority: P1)

**Goal**: the first version is on Galaxy and installs by name.

**Independent Test**: T015.

- [X] T011 [US1] **OPERATOR**: the namespace `infrastructurebuilder` is granted on galaxy.ansible.com (requested 2026-11-16); make an API token there
- [X] T012 [US3] **OPERATOR**: set the secret `GALAXY_API_KEY` in the repository, or in its `galaxy` environment (and give that environment required reviewers, if a tag should wait for approval). Done as an organisation secret of `infrastructurebuilder`, which the repository can use (2026-11-18)
- [X] T013 [US1] On the operator's word, release 0.0.1 from `develop`: give the 0.0.1 section of `CHANGELOG.md` its date in place of "unreleased", say in `README.md`'s Status that it is released, run `just full-test`, then cut the release with git-flow and tag it `0.0.1` (`galaxy.yml` already says 0.0.1). Tagging it also makes the Cloud Sandbox's install from git work again
- [ ] T014 [US1] On the operator's word, publish 0.0.1 from its tag: `just publish` on the operator's machine with `GALAXY_API_KEY` set, or push the tag (say first that pushing the tag publishes). If both are done, check that the second uploads nothing and succeeds (SC-003)
- [ ] T015 [US1] Prove it on a clean machine: `ansible-galaxy collection install infrastructurebuilder.csis_spack`, then `ansible-doc infrastructurebuilder.csis_spack.spack_env`
- [ ] T016 [US1] In `README.md`, change Status and "Installing it" from "once it is published" to published

**Checkpoint**: user stories 1, 2 and 3 are proved against the real Galaxy.

---

## Phase 6: User Story 4 - The Cloud Sandbox installs from Galaxy (Priority: P4)

**Goal**: the collection's first user installs it from Galaxy.

**Independent Test**: Cloud-Sandbox's container test.

- [ ] T017 [US4] Hand off to the Cloud-Sandbox workspace, saying which version is published and what range to name. The work there: `exportit/sandbox-provisioning/requirements.yml` (which already names 0.0.1 from git) names the collection by name with a range; `exportit/cloud-sandbox/units.toml` keeps the version; the `tools` test that holds the two together reads the range; a container run installs from Galaxy
- [ ] T018 [US4] When Cloud-Sandbox reports its container test passing, record it in `specs/001-galaxy-publish/spec.md` and set its Status to done

---

## Dependencies & Execution Order

- T011 blocks everything that remains. Nothing in this repository can do it.
- T012 is needed only for publishing by tag push (T014's second way).
- T013 → T014 → T015 → T016, in that order.
- T017 needs T014. T018 needs T017 and the Cloud-Sandbox work it hands off.
- T013 and T014 each need the operator's word, separately (principle V).
