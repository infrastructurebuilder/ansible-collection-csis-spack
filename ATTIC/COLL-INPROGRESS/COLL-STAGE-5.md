# Collection stage 5: Ansible Galaxy, or not

*Status:* planned 2026-11-14 on `feature/remaining-plans`. Begun
2026-11-16 on "do coll 5", on `feature/galaxy-publish`: the decisions
are under [Decisions taken](#decisions-taken). Items 2 and 3's
preparation is done ([Outcome so far](#outcome-so-far)); the upload and
item 4 wait for the operator's namespace on Galaxy, which they began
claiming on 2026-11-16. In the order
of the remaining work (Cloud-Sandbox's `PLAN.md`) it comes after the
live proof and before any relocation, because a relocated
`sandbox-provisioning` names the collection's source in its
`requirements.yml`, and that line should not have to change twice.

## Why

The Cloud Sandbox installs the collection from its git repository at a
tag, by the operator's decision, "until we decide if we are going to
migrate to Ansible Galaxy" (sandbox stage 10). It works: the repository
is public, and the container and the first-boot template clone it. What
Galaxy would add, and what it would cost:

| | Git tag (today) | Ansible Galaxy |
| --- | --- | --- |
| How a playbook names it | the repository's URL, `type: git`, `version: 0.3.0` | `name: infrastructurebuilder.csis_spack`, `version: ">=0.3,<0.4"` |
| What is installed | built from the repository's files at the tag, on the node | the tarball made by `just build`, as released |
| Version ranges | no: one tag | yes |
| Found by others | no | yes, by search |
| Needs | a public repository, and git on the node | the namespace `infrastructurebuilder` on Galaxy, owned by an account of the operator's choosing; an API key kept as a secret; a release step that publishes |
| On a node with no access to GitHub | fails | works if Galaxy is reachable |

## The decision

**YOUR DECISION:**

- **Stay on the git tag** (default): nothing changes. The collection's
  `PLAN.md` and the sandbox's MAP.md say it is decided, and why.
- **Publish to Galaxy:** the work below.
- **Publish to a private Automation Hub or another Galaxy server:** the
  work below, with that server's URL; only if the operator already has
  one.

## Work, if the collection is published

1. **The namespace.** The operator claims `infrastructurebuilder` on
   galaxy.ansible.com (it is tied to a GitHub organisation or user, and
   only its owner can claim it), and makes an API key. Nothing here can
   do that for them.
2. **Publishing:** `just release` gains a step after the tarball:
   `ansible-galaxy collection publish dist/...tar.gz --api-key "$GALAXY_API_KEY"`,
   reading the key from the environment, never from a file in the
   repository. It runs only when the key is set, and refuses to publish a
   version that is already there.
   **YOUR DECISION (where it runs):** from the operator's local machine
   (default: one person releases, and there is no CI here yet); or a
   GitHub Actions workflow on a tag, with the key as a repository secret.
3. **The first upload:** 0.3.1 (or 0.3.0, if collection stage 4 has not
   been released), and `galaxy.yml`'s `documentation` and `homepage`
   pointing at the repository.
4. **In the Cloud Sandbox:** `requirements.yml` names
   `infrastructurebuilder.csis_spack` with a range; `units.toml` keeps
   the version; the `tools` test that holds the pinned tag to
   `units.toml` reads the range instead. A container run proves the
   install from Galaxy, and the first-boot template is unchanged (it
   already installs `requirements.yml`).

## Decisions taken

Asked on 2026-11-16, one at a time:

1. **Publish to Galaxy.**
2. **Where it runs: both**, the operator's machine and a GitHub Actions
   workflow on a tag (the operator's answer, beside the two offered).
   Both run the same `just publish`, which leaves a version Galaxy
   already has alone, so one published both ways is uploaded once.

## A change to the plan

Item 3 said the first upload would be 0.3.1. It cannot be: 0.3.1 is
tagged and released, and item 3's own `documentation` and `homepage`
change `galaxy.yml`, which is in the tarball's manifest; a published
version should be what its tag holds. **The first version on Galaxy is
the next release** (0.3.2, unless something else lands first), cut from
`develop` once this branch is merged, and published from its tag.

## Outcome so far

- `galaxy.yml`: `homepage`, and `documentation` (the README on `main`,
  which holds what was released); `tools` and `.github` kept out of the
  tarball.
- `just import-check` runs galaxy-importer (0.4.44 when written) on the
  tarball: ansible-doc on every plugin, and ansible-lint. 0.3.1's tarball
  passed it as it is. `just full-test` runs it.
- `just publish` runs [tools/publish.py](../../tools/publish.py). It refuses
  without `GALAXY_API_KEY`, unless HEAD is tagged with `galaxy.yml`'s
  version, and with changes in the tree; asks the server whether it has
  the version already (Galaxy's published index: 200 there, 404 not,
  anything else fails), and if not, runs `ansible-galaxy collection
  publish` with the key in its environment, never on its command line.
  `GALAXY_SERVER` names another server.
- [.github/workflows/publish.yml](../../.github/workflows/publish.yml): on a
  pushed tag of the form `0.3.2`, or by hand, `just init`, `just test`,
  `just publish` with the secret `GALAXY_API_KEY`, in the `galaxy`
  environment (which the operator can give required reviewers). Without
  the secret it fails, it does not skip. It has not run: it runs first
  when the next release's tag is pushed.
- `tests/unit/test_publish.py` (22 tests): every refusal, the key kept
  off the command line, a version already there not uploaded, another
  server, the workflow's trigger and secret, the tags' form.
- **Ruff checks what `ansible-test sanity`'s pylint checks**, as far as it
  can (the operator's request, 2026-11-16, after the first full run
  stopped on five pylint findings in this stage's new code that ruff had
  passed). `pyproject.toml` adds the 73 ruff rules whose pylint code
  pylint 3.0.1 enables under ansible-test 2.16's `collection.cfg`. Not
  covered, because ruff has no rule for them: `disallowed-name` and
  `dangerous-default-value`, the two that stopped the run; the full test
  still finds them. The existing code passes all 73.
- README: installing, from Galaxy and from a tag; publishing, both ways.
  CHANGELOG: an Unreleased section.

## Still to do

1. **The operator:** the namespace `infrastructurebuilder` granted on
   Galaxy; an API token; for the workflow, the secret `GALAXY_API_KEY` in
   the repository or its `galaxy` environment.
2. Release the next version (0.3.2) on the operator's word, and publish
   it from the tag, one way or the other.
3. Item 4, in the Cloud Sandbox: `requirements.yml` by name with a
   range, the `tools` test reading the range, a container run installing
   from Galaxy.

## Out of scope

Publishing anything of the Cloud Sandbox's own.

## Acceptance

With "stay": the decision recorded in both repositories. With
"publish": `ansible-galaxy collection install
infrastructurebuilder.csis_spack` works on a clean machine, and the
sandbox's container test passes installing from there.
