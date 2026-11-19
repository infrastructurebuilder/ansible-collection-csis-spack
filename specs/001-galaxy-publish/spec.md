# Feature Specification: Publish the collection to Ansible Galaxy

**Feature Branch**: `feature/galaxy-publish`, until the history was reset on 2026-11-18 (its preparation is on `develop`)

**Created**: 2026-11-17

**Status**: Done 2026-11-19. 0.0.1 was cut on 2026-11-18 and published to
Ansible Galaxy on 2026-11-19, and the Cloud Sandbox installs it from there;
see [Outcome](#outcome). Two checks need a second release (below).

**Input**: Converted on 2026-11-17, on the operator's instruction, from
collection stage 5 ("Ansible Galaxy, or not"), which was planned on 2026-11-14
and begun on 2026-11-16. This spec carries everything of that stage that still
matters and stands on its own.

## Clarifications

### Session 2026-11-16

- Q: Stay on installing from a git tag, publish to Ansible Galaxy, or publish
  to a private Automation Hub? → A: Publish to Ansible Galaxy.
- Q: Where does publishing run: the operator's local machine, or a GitHub
  Actions workflow on a tag? → A: Both. (The operator's own answer, beside the
  two offered.) Both run the same command, and a version Galaxy already has is
  left alone, so a version published both ways is uploaded once.

### Session 2026-11-18

- Q: (The operator: "I'd rather the version of this collection be 0.0.1
  initially".) Tags 0.1.0, 0.2.0, 0.3.0 and 0.3.1 were already released and
  pushed to GitHub, and nothing was on Galaxy. Should Galaxy start at 0.0.1
  with those tags kept as history, should the history be renumbered so that
  0.0.1 is the first version anywhere, or should the numbering stay? → A:
  Renumber the history. The four tags and their `release/*` branches are
  withdrawn, and the first release is 0.0.1.
- Q: The Cloud Sandbox installed the collection from git at tag 0.3.1. Delete
  the old tags now, after it moves, or with the 0.0.1 release? → A: Now. The
  operator had already moved the Cloud Sandbox's `requirements.yml` to 0.0.1.
  They were deleted, locally and on GitHub, on 2026-11-18; see Assumptions.
- Recorded, not asked: later on 2026-11-18 the operator reset the
  repository's history to a single commit, on both `main` and `develop`,
  recreated the repository on GitHub, and removed every feature branch and
  tag.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install the collection by name (Priority: P1)

Someone writing a playbook names the collection in `requirements.yml` as
`infrastructurebuilder.csis_spack` with a version range, and
`ansible-galaxy collection install` fetches the released tarball from Ansible
Galaxy. They need neither the repository's URL nor git on the machine, and a
range such as `>=0.0.1,<0.1.0` picks up a later release without the file changing.

**Why this priority**: it is what publishing is for. Today the collection
installs only from the git repository at one exact tag: no ranges, not found
by search, and it fails on a node that cannot reach GitHub.

**Independent Test**: on a clean machine with ansible-core and no copy of this
repository, install the collection by name and run `ansible-doc` on one of its
modules.

**Acceptance Scenarios**:

1. **Given** a clean machine and a published version, **When**
   `ansible-galaxy collection install infrastructurebuilder.csis_spack` is run,
   **Then** the collection is installed and its modules are documented by
   `ansible-doc`.
2. **Given** a `requirements.yml` that names the collection with the range
   `>=0.0.1,<0.1.0`, **When** a later 0.0.x has been published, **Then** installing
   from that file fetches the later version with no change to the file.
3. **Given** a published version, **When** its tarball is compared with one
   built from its tag, **Then** they hold the same files.

---

### User Story 2 - Publish a release from the operator's machine (Priority: P2)

The operator, having cut a release, runs one command on their local machine
and the release is on Galaxy. The command refuses whenever what it would
upload might not be what was released.

**Why this priority**: one person releases, and this is the way that needs
nothing but the operator's machine and their token.

**Independent Test**: with a stand-in for the server, run the command in each
state it must refuse, and once where it must upload; the unit tests do this.
The proof against the real Galaxy is the first upload.

**Acceptance Scenarios**:

1. **Given** HEAD at the tag of `galaxy.yml`'s version, a clean working tree
   and the API key in the environment, **When** `just publish` is run, **Then**
   the tarball of that version is uploaded.
2. **Given** no API key in the environment, **When** `just publish` is run,
   **Then** it refuses and uploads nothing.
3. **Given** HEAD is not the release tag, or the working tree has changes,
   **When** `just publish` is run, **Then** it refuses and uploads nothing.
4. **Given** Galaxy already has the version, **When** `just publish` is run,
   **Then** it says so, uploads nothing, and exits successfully.

---

### User Story 3 - Publish by pushing the release tag (Priority: P3)

The operator pushes a release tag, and a workflow on GitHub publishes that
release with the token kept as a secret, so a release does not depend on the
operator's machine.

**Why this priority**: it is the second of two ways to do the same thing. It
adds a release that can be approved and repeated away from one machine.

**Independent Test**: push a release tag and see the workflow run, pass its
tests, and publish; or see it fail loudly when the secret is missing.

**Acceptance Scenarios**:

1. **Given** the secret is set, **When** a tag of the form `0.0.1` is pushed,
   **Then** the workflow runs the fast tests and then publishes that version.
2. **Given** the secret is not set, **When** the tag is pushed, **Then** the
   workflow fails. It does not skip quietly.
3. **Given** the version was already published from the operator's machine,
   **When** the tag is pushed, **Then** the workflow succeeds without uploading
   again.

---

### User Story 4 - The Cloud Sandbox installs from Galaxy (Priority: P4)

The collection's first user, the Cloud Sandbox's `sandbox-provisioning`, names
the collection in its `requirements.yml` by name with a range instead of by
the repository's URL at a tag. Its container test proves the install.

**Why this priority**: it proves the published collection on the machine it was
written for, but it is work in another repository (Cloud-Sandbox), under that
repository's rules. Here it is a hand-off.

**Independent Test**: in Cloud-Sandbox, the container test passes with the
collection installed from Galaxy.

**Acceptance Scenarios**:

1. **Given** a published version, **When** the Cloud Sandbox's container test
   runs with `requirements.yml` naming the collection by name with a range,
   **Then** it passes with the collection installed from Galaxy.

---

### Edge Cases

- The server answers neither "has this version" nor "does not have it" (an
  error, a timeout): publishing fails. It does not guess.
- A version is published both ways, in either order: it is uploaded once, and
  the second attempt succeeds without uploading.
- Galaxy keeps every version for good. A version number is never used again,
  and a mistaken upload is corrected by a new version.
- A publish fails part-way: the workflow can be run again by hand for the tag.
- Another server with Galaxy's API (a private Automation Hub) can be named in
  place of galaxy.ansible.com.
- A tag that is not a bare version (for example `v0.0.1`) does not publish.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The collection MUST be installable from Ansible Galaxy by the
  name `infrastructurebuilder.csis_spack`, with a version range.
- **FR-002**: Each published version MUST be exactly the tarball built from its
  release tag.
- **FR-003**: Publishing MUST be one command, `just publish`, which behaves the
  same on the operator's local machine and in the workflow.
- **FR-004**: Publishing MUST refuse, uploading nothing, when the API key is
  not in the environment; when HEAD is not tagged with `galaxy.yml`'s version;
  and when the working tree has changes.
- **FR-005**: The API key MUST come only from the environment (`GALAXY_API_KEY`)
  or a repository secret. It MUST NOT be read from a file in the repository,
  and MUST NOT appear on any command line.
- **FR-006**: Publishing MUST ask the server whether it already has the version.
  If it has, publishing uploads nothing, says so, and succeeds. Any answer other
  than "has it" or "does not have it" MUST fail.
- **FR-007**: Pushing a tag that is a bare version MUST start a workflow that
  runs the fast tests and then publishes. Without the secret the workflow MUST
  fail, not skip.
- **FR-008**: The tarball MUST pass Galaxy's own import checks before it is
  uploaded, and the full test MUST run those checks.
- **FR-009**: `galaxy.yml` MUST name the repository as `homepage`, and as
  `documentation` the README of what was released.
- **FR-010**: The release tools and the workflows MUST NOT be in the tarball.
- **FR-011**: The README MUST say how to install the collection from Galaxy and
  from a tag, and how to publish a release both ways.
- **FR-012**: Another server with Galaxy's API MUST be selectable
  (`GALAXY_SERVER`) without changing any file.
- **FR-013**: The first release, and the first version published, MUST be
  0.0.1. The withdrawn development versions (0.1.0 to 0.3.1) MUST NOT be
  published.
- **FR-014**: Cutting the release, pushing its tag and publishing MUST each
  wait for the operator's word.

### Key Entities

- **Namespace**: `infrastructurebuilder` on galaxy.ansible.com. It is tied to a
  GitHub organisation or user, and only its owner can claim it.
- **API token**: the operator's, from Galaxy. Kept in the operator's
  environment and as the secret `GALAXY_API_KEY` in the repository or its
  `galaxy` environment.
- **Release tag**: the bare version, as `0.0.1`.
- **Release tarball**: `dist/infrastructurebuilder-csis_spack-<version>.tar.gz`,
  built from the tag.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a clean machine, one command installs the collection by name,
  with no repository URL and no git.
- **SC-002**: A release reaches Galaxy with one action by the operator: one
  command on their machine, or one pushed tag.
- **SC-003**: Publishing the same version twice, by either way, results in
  exactly one upload and no failure.
- **SC-004**: Every unsafe state (no key, not at the tag, changes in the tree,
  an unclear answer from the server) ends with nothing uploaded.
- **SC-005**: The API token appears in no file of the repository, no command
  line and no log.
- **SC-006**: The Cloud Sandbox's container test passes with the collection
  installed from Galaxy by name with a range.

## Assumptions

- The operator will be granted the namespace `infrastructurebuilder`. Nothing
  in this repository can claim it for them. Until it is granted, user stories
  1, 3 (its run against the real Galaxy) and 4 cannot be completed.
- The first version on Galaxy, and the first release, is 0.0.1 (decided
  2026-11-18). Before that the plan was 0.3.2, the version after the
  development tag 0.3.1.
- **The withdrawn development versions.** Tagged 2026-11-13 to 2026-11-14 and
  deleted, with their `release/*` branches, from this repository and from
  GitHub on 2026-11-18. None was published to Galaxy, and everything they
  held is in 0.0.1. Later that day the repository's history was reset to a
  single commit, so their commits are no longer in it, and the tags cannot be
  recreated from it. What they were:

  | Tag | Tagged | Tag message |
  | --- | --- | --- |
  | 0.1.0 | 2026-11-13 | spack_env and spack_buildcache_push |
  | 0.2.0 | 2026-11-14 | repeat runs that do nothing, and say so |
  | 0.3.0 | 2026-11-14 | set a Spack up from one list of steps |
  | 0.3.1 | 2026-11-14 | removing a setting removes the mapping it empties; async with check mode documented |

  Each tag message began `infrastructurebuilder.csis_spack <version>: `.
- Until 0.0.1 is tagged, the collection cannot be installed from a tag: none
  exists. The Cloud Sandbox's `requirements.yml` already names 0.0.1, so its
  install fails until then.
- The server is galaxy.ansible.com. A private Automation Hub is not planned;
  `GALAXY_SERVER` allows one.
- Installing from the git repository at a tag stays documented, and works
  again once 0.0.1 is tagged.
- User story 4 is done in the Cloud-Sandbox repository, in its own workspace
  and under its own rules. This repository's part is to say when a version is
  published and what range to name.
- Publishing anything of the Cloud Sandbox's own is out of scope.

## Outcome

Recorded 2026-11-19.

- **Published:** `infrastructurebuilder.csis_spack` 0.0.1 is on
  galaxy.ansible.com (created 2026-11-19 10:48 UTC). The tag push of
  2026-11-18 started no run, because workflows were not yet enabled on the
  repository after it was recreated; once the operator enabled them, the
  workflow was started by hand on the tag (`workflow_dispatch`, run
  44508677571). It ran `just test`, then `just publish`, which ran
  galaxy-importer, uploaded the tarball and waited for Galaxy's import to
  finish.
- **The key** is an organisation secret of `infrastructurebuilder`, which the
  repository can use; on the operator's machine it is in a git-ignored
  `.envrc`, loaded by direnv.
- **Installs by name (T015):** into an empty collections path outside the
  repository, `ansible-galaxy collection install infrastructurebuilder.csis_spack`
  fetched 0.0.1 from Galaxy, and `ansible-doc` described `spack_env`.
- **What was published is what was tagged (acceptance scenario 1.3):** the
  tarball from Galaxy and one built from the tag's tree hold the same 57
  files with the same checksums.
- **The Cloud Sandbox installs from Galaxy (user story 4, SC-006):**
  reported by the Cloud-Sandbox workspace on 2026-11-19. Its
  `sandbox-provisioning` `requirements.yml` names
  `infrastructurebuilder.csis_spack` with `">=0.0.1,<0.1.0"`, and its
  container test on AlmaLinux 10 installed 0.0.1 from galaxy.ansible.com by
  that range. First apply: `site.yml` 55 changes, `users.yml` 11,
  `jupyterhub.yml` 21, none failed; second apply and check mode: no
  changes. Its root `just full-test` passed. The work is on branches
  `feature/collection-from-galaxy` in `csis-sandbox-provisioning`
  (`795009e`) and in Cloud-Sandbox (`9ca2759`), not merged there yet.
- **Not yet proved:** a range picking up a later release (scenario 1.2), and
  publishing a version both ways (SC-003); both need a second release.
