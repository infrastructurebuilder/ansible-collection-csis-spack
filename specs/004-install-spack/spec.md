# Feature Specification: A `setup` step that installs Spack

**Feature Branch**: `feature/install-spack`

**Created**: 2026-11-25

**Status**: Done 2026-11-26: `just test` (326 tests) and `just full-test`
pass; merged into `develop` (`83c76d3`). Not released

**Input**: User description: "a setup step kind that installs Spack". Asked
after the operator's question "So does this collection actually install
Spack for me?", whose answer was no: today the collection needs a Spack
already on the managed node (README, Requirements), and a site installs it
with tasks of its own before the `setup` role.

## Clarifications

### Session 2026-11-25

- Q: What can the step install from: a git repository only, a release
  archive only, or either? → A: A git repository only, as Spack's own
  documentation installs it. A branch or a commit works as the version, a
  site's own copy is a git mirror, and the node needs `git`.
- Q: When the destination already holds a Spack at another version than the
  one named, should the step fail and change nothing, move it to the version
  named, or leave it and warn? → A: Fail and change nothing. Moving a Spack
  to another version, on a site's explicit request and off by default, is a
  spec of its own:
  [specs/005-move-spack-version/](../005-move-spack-version/spec.md), made
  on the operator's word the same day.
- Q: Should the step also fetch Spack's package recipes, which Spack 1.0 and
  later keep in a repository of their own? → A: No. They are left to Spack,
  which fetches them the first time it needs them. Pinning the recipes to a
  version a site names is a spec of its own, not yet written.

### Session 2026-11-26

- Q: (While planning.) The plan proposes the step's kind `spack`, the module
  `spack_checkout`, the options `version`, `path` and `source`, and
  `version_added: 0.0.4`. Take them, or change any? → A: Take all four.
- Recorded on the operator's yes to `/speckit-analyze`'s remediations: in
  check mode on a node with no Spack, the steps after the install step are
  not previewed (FR-009, research R9); a commit is given by its full hash
  (FR-002); the install step takes `environment` only as a mapping
  (FR-008).
- Q: (Reviewing the requirements checklist.) A Spack at the version named
  whose own files have been edited: what does the step do? → A: Make no
  change, and say so: the step warns and names the edited files. The other
  gaps the checklist found were closed with the defaults proposed for them,
  on the operator's word: a symbolic link is followed; two plays at once are
  not supported; a source holding a credential is refused; the source is
  trusted as given; any address `git` accepts; a hanging fetch is left to
  the play's own timeout; `git` 2.18 or later.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A node with no Spack gets one from the role (Priority: P1)

A site's play applies the `setup` role to a node that has no Spack. The
first step of its list is an install step, naming the Spack version the site
wants and where to put it. The role installs that Spack there, and the
steps after it (settings, mirrors, keys, compilers) run the Spack it just
installed. The site writes no task of its own before the role, and names
where Spack lives in one place.

**Why this priority**: it is the whole of the feature. Without it every site
writes the same install tasks around the role, and has to keep the path in
those tasks and in `spack_setup_executable` the same by hand.

**Independent Test**: on a node with no Spack, apply the role with an install
step followed by a `config` step; see the Spack installed at the path named,
report the version asked for, and hold the `config` step's setting.

**Acceptance Scenarios**:

1. **Given** a node where the destination does not exist, **When** the role
   is applied with an install step, **Then** Spack is installed at the
   destination, at the version named, and the step reports a change.
2. **Given** the same node and list, **When** the role is applied a second
   time, **Then** the install step reports no change and touches nothing.
3. **Given** an install step followed by other steps, **When** the role is
   applied, **Then** every later step runs the Spack the install step put at
   the destination.
4. **Given** a node where the destination does not exist, **When** the role
   is applied in check mode, **Then** the install step reports that it would
   install, and the destination still does not exist afterwards.

---

### User Story 2 - A Spack already there is respected (Priority: P2)

A site applies the role to a node that already has a Spack at the
destination: installed by an earlier run of the role, or by hand the way
Spack's own documentation says. The role does not reinstall it or break it.

**Why this priority**: a play is run again and again (principle II), and
nodes that a site set up before this feature existed already have a Spack.

**Independent Test**: install Spack at a path by hand at one version, then
apply the role with an install step naming that path and version; see no
change. Then name a different version and see the step fail with the Spack
there untouched (FR-007).

**Acceptance Scenarios**:

1. **Given** a Spack at the destination at the version named, however it got
   there, **When** the role is applied, **Then** the install step reports no
   change.
2. **Given** a Spack at the destination at a different version than the one
   named, **When** the role is applied, **Then** the step fails, names the
   version it found and the version asked for, changes nothing, and no later
   step runs.
3. **Given** a destination that exists and holds something that is not a
   Spack, **When** the role is applied, **Then** the step fails, says why,
   and leaves what is there untouched.

---

### User Story 3 - A site whose nodes cannot reach the internet (Priority: P3)

A site whose nodes cannot reach Spack's public repository keeps its own copy
of Spack, a git mirror of Spack's repository, and names it in the install
step. The role installs from that copy.

**Why this priority**: HPC and cloud nodes are often kept off the internet,
and a step that can only fetch from one public address is no use to them. It
is P3 because a site with internet access, the first case, does not need it.

**Independent Test**: with no route to the public repository, apply the role
with an install step naming a local copy of Spack; see Spack installed from
it at the version named.

**Acceptance Scenarios**:

1. **Given** an install step that names a source of the site's own, **When**
   the role is applied, **Then** Spack is installed from that source and
   nothing is fetched from the public repository.
2. **Given** an install step that names no source, **When** the role is
   applied, **Then** Spack is installed from Spack's own public repository.

---

### Edge Cases

- **The version named does not exist** in the source: the step fails, says
  which version it could not find and where it looked, and leaves no
  destination behind that a later run would take for a Spack.
- **The source cannot be reached** (no network, a wrong address): the step
  fails and says so. It does not fall back to another source.
- **A run was stopped part-way** (the node lost its network, the play was
  interrupted), leaving a partial destination: a later run either completes
  the install or fails and says what it found. It never reports success over
  a Spack that does not run. An install into a destination that did not
  exist is made beside it and moved into place only when complete, so a
  stopped one leaves only a hidden directory beside the destination, which
  later runs ignore and a site may delete; an install into an empty
  directory is made in place, so a stopped one leaves a directory that the
  next run finds is not a Spack, and fails over (FR-010).
- **The version named is older than 1.0**, which the collection does not
  support: the step fails and says so, before later steps run against it.
- **Two install steps in one list**, or an install step that is not the
  first step: refused before any step runs, as the role refuses every
  malformed list today (FR-008).
- **The destination's parent does not exist**: every missing directory
  above the destination is made, owned by the user the play runs as, with
  that user's umask.
- **The destination is a symbolic link**: it is followed. The directory it
  points to is judged as if it were the destination (absent, empty, a
  Spack, or not a Spack); a link that points nowhere is "absent", and the
  install is made where it points.
- **The destination, or the directory above it, cannot be written to** by
  the user the play runs as: the step fails with what `git` or the system
  said, and nothing is changed. (An empty destination that can be written
  to, in a parent that cannot, is installed into in place.)
- **Two plays install to the same destination at the same time**: not
  supported. The move into place means that one of them fails rather than
  leaving a mix of both; the docs say so.
- **A fetch hangs** (a source that neither answers nor refuses): the step
  waits. A time limit is the play's to set (`timeout` on the task, or
  `async`), and the docs say so.
- **`git` is older than 2.18**, the version in RHEL 8 and the oldest the
  step's commands are documented against: the step fails before fetching,
  naming the version found and the one needed.
- **A Spack at the version named whose own files have been edited**: no
  change is made and none is reported, and the step warns, naming the
  edited files (FR-005).
- **A tag or branch whose name is all hexadecimal digits**, 7 to 39 of them:
  refused as a short hash would be (FR-002). Spack has none.
- **Spack's own prerequisites are missing** (Python, a C compiler, `git`,
  `patch`, and the rest Spack's documentation lists): installing them is not
  this step's work. The step fails if `git`, which it needs to fetch Spack,
  is missing, and says so; what Spack needs later is reported by Spack when
  a later step runs it.
- **Spack's package recipes** are not fetched by this step. Spack fetches
  them the first time it needs them, so the first later step that needs them
  needs the network, or a recipe repository of the site's own, set with a
  `config` step.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `setup` role MUST have a step kind that installs Spack on
  the managed node, given in the list of steps like every other kind.
- **FR-002**: The step MUST be given the Spack version to install and the
  destination (the directory Spack is installed in). Neither has a default:
  both are a site's choice (principle I). The version is what Spack's
  project names a release by (for example `v1.2.0`); a branch, or a commit
  given by its full 40-digit hash, MUST be accepted too. A shorter hash MUST
  be refused before anything is fetched: git cannot fetch a commit by a
  short hash without Spack's whole history (research R2). Any version of
  7 to 39 hexadecimal digits is taken for a short hash, so a tag or branch
  so named is refused too, and the documentation says so.
- **FR-003**: The step MAY be given the source to install from: the address
  of a git repository holding Spack, such as a site's own mirror of Spack's.
  Without one, it installs from Spack's own public repository. Any address
  `git` accepts may be given (`https://`, `ssh://`, `user@host:path`,
  `file://`, a path on the node); whatever access it needs (a key, an
  agent, a certificate) is the node's. No other kind of source (a release
  archive, a package) is accepted. An `http://` or `https://` address that
  holds a user name or password MUST be refused before anything runs, so
  that no credential reaches the play's output, the step's result or the
  Spack's own git configuration; the documentation points to a credential
  helper or an SSH key instead.
- **FR-004**: When the destination does not exist, or is an empty
  directory, the step MUST install the version named there and report a
  change. Missing directories above it are made (Edge Cases).
- **FR-005**: When the destination holds a Spack at the version named, the
  step MUST change nothing and report no change, whether the role installed
  it or not. "At the version" is decided without the network: for a tag, its
  commit is checked out; for a branch, that branch is checked out, however
  far the source's branch has moved since; for a commit, it is checked out.
  A repeat run MUST need no network. "Change nothing" means no file that
  Spack's git repository tracks is changed and nothing is fetched; what
  Spack itself writes and its own `.gitignore` ignores (Python's caches) is
  not a change. When Spack's own files there have been edited, the step
  still changes nothing and reports no change, and MUST warn, naming the
  edited files.
- **FR-006**: After installing, and in every run, the step MUST check that
  the Spack at the destination runs and reports a version of 1.0 or later,
  and fail if it does not. The version is the first word of what
  `spack --version` prints, read as major and minor: `1.3.0.dev0` is 1.3;
  an answer whose first word is not a version fails.
- **FR-007**: When the destination holds a Spack at another version than the
  one named, the step MUST fail and change nothing, saying the version it
  found (the tag, branch or commit checked out, and what `spack --version`
  printed) and the version asked for. No later step runs: as for any step's
  failure, the role stops there and keeps the results of the steps before
  it. (Moving it to the
  version named, when a site asks for that, is spec 005.)
- **FR-008**: The steps after an install step MUST run the Spack it
  installed (`<destination>/bin/spack`). A list with more than one install
  step, or with an install step that is not the first step, MUST be refused
  before any step runs. A list whose install step's Spack differs from a
  `spack_setup_executable` the site also set MUST be refused the same way.
  "Also set" means a value other than its default, `spack`; a value set
  through its name before 0.0.1, `spack_setup_spack`, counts as set. Set to
  exactly `<destination>/bin/spack`, it is accepted.
  Because no step comes before it, the install step's `environment` (a proxy
  or a certificate for fetching) MUST be given as a mapping of variables;
  the name of an environment an earlier step captured cannot be used. Every
  variable in that mapping is set for `git` and for `spack --version`, as
  given (for example `HTTPS_PROXY`, `NO_PROXY`, `GIT_SSL_CAINFO`).
- **FR-009**: In check mode the step MUST report what it would do (install,
  nothing, or what FR-007 says) and change nothing on the node. When it
  would install, the steps after it MUST NOT be carried out, since the Spack
  they would run is not there yet: each is reported as not changed and not
  previewed, with that reason, and the role succeeds.
- **FR-010**: A destination that exists and is not a Spack MUST make the
  step fail with nothing changed in it, saying what it found: a file, a
  directory that is not a git repository, a repository with no `bin/spack`,
  or a directory inside another repository (naming that repository's top).
- **FR-011**: The step MUST NOT run anything through a shell, and MUST NOT
  install Spack's own prerequisites.
- **FR-012**: The step MUST NOT fetch or configure Spack's package recipes,
  which Spack 1.0 and later keep in a repository apart from Spack itself.
  They are left to Spack, which fetches them the first time it needs them.
  The step's documentation MUST say so, and that a site without the network
  sets a recipe repository of its own with a `config` step.
- **FR-013**: The role's README, the step's documentation, an example and
  `CHANGELOG.md` MUST describe the step. The README's Requirements MUST say
  that a Spack on the node is needed only when the list has no install step,
  and that the install step needs `git` 2.18 or later on the node.
- **FR-014**: The step's result MUST give back, for later tasks: the
  destination, the executable (`<destination>/bin/spack`), the version
  named, what `spack --version` printed, the source used, what was found at
  the destination (nothing, an empty directory, or a Spack), and the edited
  files, if any.

### Key Entities

- **Install step**: a step of the new kind in `spack_setup`: the version,
  the destination, the source (optional), and the options every step may
  have (`label`, and `environment` as a mapping; `yes_to_all` does not
  apply, as no Spack command asks anything here). In the role it is the
  kind `spack`, with the options `version`, `path` (the destination) and
  `source`, carried out by the module `spack_checkout` (Clarifications,
  2026-11-26).
- **Destination**: the directory Spack is installed in. Its `bin/spack` is
  the Spack the later steps run.
- **Version**: a release tag of Spack's project, a branch, or a commit's
  full hash.
- **Source**: the git repository Spack is fetched from: Spack's public
  repository unless the site names its own copy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a node with no Spack, one application of the role, with an
  install step first, leaves a working Spack at the version named and every
  later step applied; the site writes no task of its own for Spack.
- **SC-002**: A second application with the same list reports no change for
  the install step, on every Spack version the collection supports.
- **SC-003**: Check mode on a node with no Spack reports one change for the
  install step and leaves the destination absent.
- **SC-004**: A site need name where Spack lives only once, in the install
  step: a list with an install step and no `spack_setup_executable` runs
  every later step with the Spack it installed.
- **SC-005**: Every case of FR-004 to FR-010 is held by a test that fails if
  the step does otherwise, both in a real run and in check mode, and the install of each version the collection is
  tested against (1.0.0, 1.1.0, 1.2.0) is proved against the real Spack.
  The tests need no network: installing from Spack's public repository (US3,
  scenario 2) is proved by research R2's fetch from GitHub, and held by a
  test that the step names that repository when no source is given.
- **SC-006**: No version, path or source of any site is built into the
  collection: the test that holds the collection to that still passes,
  unchanged.

## Assumptions

- The install step is a kind of the `setup` role, as asked. Whether it is
  carried out by a new module, as every other kind is, or by Ansible's own
  modules, is the plan's to decide.
- "Spack's own public repository" is Spack's, not a site's choice, in the
  same way that the default executable `spack` is: naming it as the default
  source does not build a site into the collection.
- Installing Spack the way its documentation describes is a copy of its
  source at a release; there is no build (Spack's own
  `lib/spack/docs/getting_started.rst`, read in the v1.2.0 checkout;
  research R1). If a later Spack documents another way, this assumption
  and the step are revisited in a spec of their own. Bootstrapping Spack's solver,
  which happens the first time Spack concretizes, is not part of the step.
- The step runs as whatever user the play runs it as. What it makes is
  owned by that user, with that user's umask; an empty destination a site
  made keeps its own ownership and mode. `become` is the site's, as for the
  rest of the role.
- The source is trusted as given. The step does not verify a signature on a
  tag or check a commit against a known list; verifying what was fetched
  could be a spec of its own.
- The role keeps `spack_setup_executable` for lists with no install step,
  and its meaning does not change.
- The step works the same on the Spack versions the collection supports
  (1.0 or later) and is tested against 1.0.0, 1.1.0 and 1.2.0, the versions
  the integration tests already use.
- Out of scope, each its own spec: moving a Spack that is there to another
  version (spec 005), and pinning Spack's package recipes (not yet written).
- No release is cut by this spec. It goes out in the next release, on the
  operator's word.
