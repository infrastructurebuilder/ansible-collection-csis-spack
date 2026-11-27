# Feature Specification: Set Spack up from one piece of configuration

**Feature Branch**: `feature/coll-stage-2`, until the history was reset on 2026-11-18

**Created**: 2026-11-14

**Status**: Done 2026-11-14 (retrospective, written 2026-11-27 from
`ATTIC/COLL-INPROGRESS/COLL-STAGE-2.md`): built on `feature/coll-stage-2`,
where `just test` (193 unit tests) and `just full-test` (the integration
tests against the real Spack v1.2.0 and `ansible-test sanity`) passed;
merged into `develop`, released as the development version 0.3.0 and pushed,
each on the operator's word, the same day. 0.3.0 was withdrawn on
2026-11-18; its work is in 0.0.1, the first release (see `CHANGELOG.md`,
and the Assumptions of
[specs/001-galaxy-publish/spec.md](../001-galaxy-publish/spec.md)).

**Input**: the operator's request, on 2026-11-14, to set a fresh Spack up
from the collection instead of from the Cloud Sandbox's shell tasks; planned
that day as collection stage 2, revised the same day at the operator's
request "so that the collection prescribes nothing about what is installed
and takes it all as configuration", and carried out on the operator's
"do coll 2".

This spec was written after the fact, so that the work has a spec of its
own and the stage plan it was carried out from is no longer needed. It
describes what was built. Where a later spec changed something, a note
says which.

## Why

0.1.0 covered what happens to a Spack *environment*: concretize, install,
module files, push. What comes before that, making a fresh Spack ready to
build anything, was still bash in the Cloud Sandbox's playbooks. In its
`exportit/sandbox-provisioning/`, on 2026-11-14:

| Where | What the shell did | What was fragile about it |
| --- | --- | --- |
| `roles/spack/tasks/main.yml` L92-L119 | `config add` twice; `compiler find --scope site`; `external find --scope site`; `external find --not-buildable cmake`; `mirror add spack-public` unless `mirror list` already named it; `buildcache keys --install --trust` | A change was told by a fingerprint: Spack's whole configuration dumped through `spack python -c` (Spack's internals) plus `spack gpg list`, hashed before and after. A `grep` guarded the mirror. No check mode |
| `roles/intel_oneapi/tasks/main.yml`, three tasks | `compiler find` again with the Intel modules loaded; YAML text appended to `etc/spack/site/packages.yaml` unless `grep` found the package's name; `config --scope site add` five times; `buildcache keys` again | The two `compiler find` steps were thought to undo each other when the modules were not loaded (not so: [research.md](research.md), R16). A changed version or prefix was never corrected, because the name was already in the file |
| `sandbox-ops/bin/spack-pubkey.sh`, run by hand | Download the site mirror's public key, `gpg trust` it, `mirror add s3-mirror`, `buildcache keys` | By hand; "already exists" errors sent to `/dev/null` |

The first plan for this work answered with modules *and* with a list of
workflows, one per kind of compiler, each with its own order of steps. That
would have put the sandbox's choices (Intel, MKL, `cmake`, which modules to
load) into the collection, and every site with other choices would have
needed the collection changed. The plan was revised to do the opposite.

### The principle

**The collection knows how to do each kind of thing to Spack, and nothing
about what any site wants done.** No package, compiler, version, path,
mirror or module name appears in its plugins or in its role's defaults,
which are empty. What a site wants is one piece of configuration: a list of
steps in the order the site wants them, which is to say its shell script,
written as data.

- Each step is one of a small number of kinds, and each kind is a module
  that can tell whether anything changed and, where the answer is knowable
  beforehand, preview it.
- The order is the site's, because the order is where the site's knowledge
  is (what must be loaded before what is looked for).
- Anything no kind covers can still be said, as a plain Spack command with a
  stated way of telling whether it changed something, so that no line of a
  script has to stay outside the configuration.

The steps still differ in nature, and the configuration keeps that visible:

- **Declared state** (a setting, a mirror, a trusted key): the answer is
  known before anything runs, so it is compared, changed only when
  different, and previewed in check mode.
- **Discovery** (`compiler find`, `external find`): the answer depends on
  the machine and on the environment the command runs in. It cannot be
  previewed, and the site can say what must have been found.

This principle became Principle I of the constitution when it was ratified
on 2026-11-17.

## Clarifications

### Session 2026-11-14

- Recorded, not asked: the operator asked that the first plan be revised
  so that the collection prescribes nothing about what is installed and
  takes it all as configuration. The list of workflows, one per kind of
  compiler, was dropped; the role carries out a list the site writes, and
  its defaults are empty (The principle, above).

Asked one at a time, after the revision; each default was taken.

- Q: Include a plain command kind (`spack_command`), for whatever the other
  kinds do not cover, or leave it out and keep the collection to steps it
  can fully answer for? → A: Include it. Without it, whatever the other
  kinds do not cover goes back into shell tasks beside the configuration,
  and the configuration is no longer the whole script.
- Q: What shape is the configuration: an ordered list of steps, each naming
  its `kind` and that kind's options, carried out in the order written; or a
  mapping with one fixed key per kind (`settings`, `detect`, `mirrors`,
  `keys`), carried out in one order the role fixes? → A: An ordered list. A
  shell script maps onto it line by line and the order stays the site's; a
  site that must detect, then declare, then detect again could not say so
  with the mapping.
- Q: How does a step get the environment it must run in (modules loaded, a
  toolset enabled): a step kind `environment`, whose shell lines the role
  runs once and keeps the result of under a name for later steps; or no such
  kind, each step taking only a mapping of variables that the site computes
  in a task of its own before the role? → A: A step kind `environment`. The
  shell is the site's, contained in the configuration, and it is the only
  shell the role runs. (While building, a step's `environment` was allowed
  to be a mapping of variables as well: see FR-013.)
- Q: Release it as 0.3.0, after stage 1's 0.2.0, or both stages in one
  0.2.0 if stage 1 has not been released by then? → A: 0.3.0.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A site's set-up script becomes one list of steps (Priority: P1)

A site that sets its Spack up with a shell script (settings, compiler and
package detection, a mirror, its keys) writes the same thing as a list of
steps and gives it to the `setup` role. The role carries the steps out in
the order written. Each step reports a change only when it made one, so a
second application of the same list reports none.

**Why this priority**: it is the whole of the feature. Without it, each
site keeps its own shell tasks and its own way of guessing whether they
changed anything.

**Independent Test**: apply the role with a list holding one step of each
kind against a Spack; see each step's effect in Spack's configuration and
keys; apply it again and see no change reported.

**Acceptance Scenarios**:

1. **Given** a Spack and a list of steps, **When** the role is applied,
   **Then** every step is carried out in the order written, and the role
   leaves one result per step: its number, kind, label, whether it changed,
   and what its module returned.
2. **Given** the same Spack after that, **When** the role is applied again
   with the same list, **Then** no step reports a change.
3. **Given** a list with an unknown kind, an option of another kind, or a
   missing required option, **When** the role is applied, **Then** it stops
   before the first step, naming every problem and its step's number, and
   nothing has been changed.
4. **Given** a list whose step 2 fails, **When** the role is applied,
   **Then** step 1 has been carried out, the role stops at step 2, and no
   later step runs.
5. **Given** no list, **When** the role is applied, **Then** it does
   nothing: its defaults hold no step.

---

### User Story 2 - A detection that ran without its environment fails (Priority: P1)

A site's compilers are visible only with some environment modules loaded.
The site captures that environment in an `environment` step and names it in
the `detect` step that needs it, with `require` naming what must be found.
If the environment is missing or wrong, the step fails, naming what is not
registered, instead of passing quietly.

**Why this priority**: this was the accident the sandbox's shell left open.
Spack says nothing when it finds nothing, so a detection in the wrong
environment looked like success.

**Independent Test**: on a stand-in machine whose compiler is visible only
with a variable set, run a `detect` step with `require` naming it, once
without the environment (fails, naming the compiler) and once with it
(passes).

**Acceptance Scenarios**:

1. **Given** an `environment` step that captures a variable and a later
   `detect` step that names it, **When** the role is applied, **Then** the
   `detect` step runs with that variable set, and the steps that do not name
   it run without it.
2. **Given** a `detect` step with `require` whose compiler is not visible,
   **When** it runs, **Then** it fails with "not registered after
   detection" and the names missing.
3. **Given** a compiler registered by an earlier detection and not visible
   now, **When** detection runs again, **Then** it stays registered:
   detection only adds.

---

### User Story 3 - Check mode previews what is declared (Priority: P2)

Before applying a list, a site runs it in check mode. Settings, mirrors and
keys whose answer is known beforehand are reported exactly; nothing is
written. Detection, which cannot be previewed, says so and does nothing. A
plain command is not run and is reported as a possible change unless it
cannot be one.

**Why this priority**: a preview that changes nothing (Principle II) is how
a site checks a new list before it runs it on a node.

**Independent Test**: run a list of one step of each kind in check mode on a
fresh Spack; see the declared steps report changes, the detection report
`previewed: false`, and the Spack's scopes and keys unchanged.

**Acceptance Scenarios**:

1. **Given** a `config` step whose settings differ from the scope, **When**
   it runs in check mode, **Then** it reports a change, lists the paths it
   would change, and writes nothing.
2. **Given** a `mirror` step for a mirror that is missing or different,
   **When** it runs in check mode, **Then** it reports what it would do
   (`added`, `replaced`, `removed`) and does none of it.
3. **Given** a `gpg_key` step for a key file whose fingerprint is known,
   **When** it runs in check mode, **Then** it reports whether the key would
   be newly trusted; for `from_mirrors` it reports that it cannot tell.
4. **Given** a `detect` step, **When** it runs in check mode, **Then** it
   runs nothing and reports `previewed: false` and no change.
5. **Given** a `command` step, **When** it runs in check mode, **Then** the
   command is not run, and it reports a possible change unless `changes` is
   `never`, or `changes` is `creates` and the path exists.

---

### User Story 4 - Each kind is a module usable on its own (Priority: P3)

A playbook that wants one thing done to Spack, such as one mirror or one
trusted key, uses that kind's module as a task, with the same options and
results as the role's step, without the role.

**Why this priority**: the role is built on the modules; the modules are
useful without it, but a site with a list needs the role first.

**Independent Test**: run each module as a single Ansible task against a
stand-in Spack, twice, and in check mode.

**Acceptance Scenarios**:

1. **Given** any of `spack_config`, `spack_mirror`, `spack_gpg_key`,
   `spack_detect`, `spack_command`, **When** it runs as a task, **Then** it
   takes the Spack executable as `spack` and, where it applies, the
   configuration scope as `scope`, and reports change and check mode as its
   step would.
2. **Given** `shell_environment` as a task, **When** it runs, **Then** it
   returns the variables the lines set or changed, to give to later tasks
   with Ansible's `environment` keyword, and never reports a change.

---

### User Story 5 - The collection carries no site's choices (Priority: P2)

Someone reading the collection's plugins and role finds no site's package,
compiler, mirror, path or module name. A site's choices are in its own list.
The collection's examples show whole lists for common situations, and the
tests carry each one out, so an example cannot quietly stop working.

**Why this priority**: a collection that carries one site's choices has to
be changed for every other site (Principle I).

**Independent Test**: run the test that reads `plugins/` and `roles/` for
every name the Cloud Sandbox's example uses, and the test that carries out
every example.

**Acceptance Scenarios**:

1. **Given** the collection, **When** its plugins and role are searched for
   every package, mirror, path and module name in the Cloud Sandbox's
   example, **Then** none is found.
2. **Given** the Cloud Sandbox's example, **When** its two lists are applied
   to a stand-in Spack and the sandbox's own shell commands to a second
   stand-in, **Then** both are left with the same configuration in every
   scope, the same mirrors and trusted keys, and the discovery commands run
   in the same order.
3. **Given** each example under `docs/examples/`, **When** the tests carry
   it out against a stand-in machine made for it, **Then** it does what its
   comments say.

---

### Edge Cases

- **A list Spack would need in another order** (detect, then declare, then
  detect again): written in that order, carried out in that order.
- **Something must happen between two parts of the set-up** (the sandbox
  installs oneAPI with dnf between its two lists): the site applies the
  role twice, with two lists. The role keeps nothing between applications.
- **A step's value is wrong but its option is right** (a string where Spack
  wants a boolean): the list passes the first check, which looks at kinds
  and options, not values; the step's module or Spack refuses it when the
  step runs, and the steps before it have been carried out.
- **A value Spack's schema refuses**, after `spack_config` removed a path to
  make room for it: the module puts back what it removed, and the scope is
  as it was.
- **A list in the scope is to be set exactly** (`mpi: [othermpi]` where the
  scope holds `mpi: [mympi, othermpi]`): Spack's `config add` alone would
  merge the two; the module removes the path first and adds the new list
  (research R8).
- **A scope that does not exist yet**, as the user scope on a fresh machine:
  read as empty, and made by the first write (research R11). (Later, spec
  003: Spack 1.1 cannot write to such a scope; the module fails and says
  which directory to make.)
- **Spack writes `packages.yaml` back in another order** after each
  detection: the module compares the section as data, so a reorder is not a
  change (research R17).
- **A mirror of the same name with another URL or properties**: replaced,
  and reported as `replaced`. Only the properties the step gives are
  compared.
- **A key file that holds no key**: `spack gpg trust` exits 0 for it; the
  module refuses the file, reading it with `gpg` where there is one
  (research R13).
- **A key file holding another key than the `fingerprint` named**: refused,
  naming both.
- **A compiler that is present but not wanted**: a `detect` step with
  `exclude`, or a `config` step with `state: absent` after the detection.
  The second form reports a change on every application, since detection
  finds the compiler again each time; the example says so.
- **An environment named before it is captured**, or captured twice under
  one name: refused before any step runs.
- **An environment step's shell lines fail**: the step fails. A line that
  fails does not stop the ones after it unless the lines say so (`set -e`);
  only the shell's own exit status counts.
- **The sandbox's own script writes two settings to the user scope**
  (`config add` without `--scope`): the sandbox's example says `scope: user`
  for that step, so that it reproduces the script (research R20).

## Requirements *(mandatory)*

### Functional Requirements

**The modules (one per kind of step)**

- **FR-001**: `spack_config` MUST make the given settings (a mapping in the
  shape of Spack's configuration, a section at the top of each key) true in
  one configuration scope. With `state: present` and `mode: merge` (the
  default) it MUST leave every key it is not given alone; with
  `mode: replace` it MUST make each section named exactly what is given,
  working a key of the section at a time: a key not given, or different, is
  removed, and the given ones are added. With `state: absent` it MUST remove
  the paths named and nothing else. A list or a scalar MUST be set to
  exactly the value given. It MUST compare with the scope as data, read
  through `spack config get --json`, write only what differs, and return the
  paths it changed; in check mode it MUST return them and write nothing.
  (Later, 0.3.1, [spec 011](../011-preview-long-builds/spec.md): a removal
  that would leave a mapping empty removes the mapping, since Spack leaves
  it behind; research R9.)
- **FR-002**: `spack_mirror` MUST make one mirror (`name`, `url`, `type`,
  `signed`) be present in one scope with the properties given, or absent,
  and MUST say what it did, or in check mode would do: `added`, `replaced`,
  `removed` or `none`. A mirror there with another URL, or another value of
  a property the step gives, MUST be replaced. A property the step does not
  give MUST NOT be compared.
- **FR-003**: `spack_gpg_key` MUST trust a public key from a file or a URL
  (`key`, with an optional `fingerprint` it must have), or the keys the
  configured mirrors publish (`from_mirrors: true`), or both. A change MUST
  be a fingerprint trusted afterwards that was not before, read from
  `spack gpg list --trusted` before and after. It MUST handle public keys
  only. In check mode it MUST report, for a key file whose fingerprint is
  known, whether it is trusted already, and for `from_mirrors` that it
  cannot tell (`previewed: false`).
- **FR-004**: `spack_detect` MUST run `spack compiler find` (`compilers:
  true`) and `spack external find` (`externals: true`, or a list of package
  names), with `not_buildable`, `exclude` and `paths` passed to Spack. A
  change MUST be told from the scope's `packages` section before and after,
  compared as data, and it MUST return the external specs added and
  removed. `require` MUST name specs that must be registered afterwards, in
  any scope; the task MUST fail naming those that are not. A required
  version MUST accept anything more exact (`gcc@14` accepts `gcc@14.3.1`).
  In check mode it MUST run nothing, report no change, and say that
  discovery cannot be previewed (`previewed: false`).
- **FR-005**: `spack_command` MUST run any Spack command given as a list of
  arguments, without a shell, for what the other kinds do not cover.
  `changes` MUST say how a change is told: `config` (the named `sections` of
  the scope differ afterwards, read as data), `creates` (a path made by the
  command; the command is not run while it exists), `always` or `never`. In
  check mode it MUST NOT run the command, and MUST report a possible change
  unless `changes` is `never`, or `creates` and the path exists.
- **FR-006**: `shell_environment` MUST run the given shell lines and return
  the environment variables they set or changed, as a mapping, and the
  names of those they removed. It MUST never report a change, and MUST run
  in check mode too.
- **FR-007**: Every module but `shell_environment` MUST take the Spack
  executable as `spack` (default `spack`, looked up on `PATH`), and, where
  it applies, the configuration scope as `scope` (default `site`). Each MUST
  run Spack only as a list of arguments, never through a shell, and MUST
  refuse a Spack older than 1.0. Each MUST take the environment Spack runs
  in from the task's `environment:` keyword. (Later, spec 003: each module
  that runs Spack also takes `yes_to_all`, and the modules follow Spack 1.0
  and 1.1 where their commands differ from 1.2's.)

**The role and its list**

- **FR-008**: The role `infrastructurebuilder.csis_spack.setup` MUST carry
  out one variable, `spack_setup`, an ordered list of steps, in the order
  written. Its defaults MUST be an empty list, the executable `spack`, and
  the scope `site`; it MUST contain no step of its own. (Later: spec 002
  named the executable's variable `spack_setup_executable`, keeping the
  name it had in 0.3.0, `spack_setup_spack`, as an alias; spec 003 added
  `spack_setup_yes_to_all`.)
- **FR-009**: Each step MUST be a mapping with a `kind`, that kind's
  options, and optionally a `label` and an `environment`. The kinds MUST be
  `config`, `mirror`, `gpg_key`, `detect`, `command` and `environment`, each
  carried out by its module (FR-001 to FR-006) with the step's options
  passed as they are, and an option the step leaves out left to the
  module's default. A step's `scope` MUST default to the role's scope.
  (Later: spec 004 added the kind `spack`, which installs Spack; spec 005
  gave it `move`.)
- **FR-010**: A step's label MUST be `label`, shown in the task's output;
  without one the role MUST make one from the kind and its main option (as
  `mirror: site-cache`). It is `label`, not `name`, because a `mirror` step
  and an `environment` step already have a `name` with another meaning.
- **FR-011**: The role MUST check the whole list before the first step runs:
  that it is a list of mappings, that each kind is known, that each option
  belongs to its kind, that each required option is there, that a named
  environment was captured by an earlier step, and that no name is captured
  twice. Any problem MUST stop the role with every problem and its step's
  number, with nothing changed. Values are not checked here; each module
  checks them when its step runs.
- **FR-012**: The role MUST leave `spack_setup_results`, one entry per step:
  its number, kind, label, whether it changed, and the module's result. A
  step that fails MUST stop the steps after it.
- **FR-013**: An `environment` step MUST take a `name` and the `shell` lines
  that produce the environment, and optionally the shell to run them with
  (`executable`, default `/bin/bash`). The role MUST run them once and keep
  what they changed under that name. A later step's `environment` MUST be
  either that name or a mapping of variables; with neither, the step runs in
  the play's environment. The `environment` step's shell MUST be the only
  shell the role runs.
- **FR-014**: The role MUST keep no state between applications; a site that
  must do something between two parts applies it twice, with two lists.

**What holds it to its principle**

- **FR-015**: No package, compiler, version, path, mirror or module name of
  any site MUST appear in `plugins/` or `roles/`. A test MUST read every
  `.py`, `.yml`, `.md` and `.j2` file there and fail on any package,
  mirror, path or module name taken from the Cloud Sandbox's example.
- **FR-016**: `docs/examples/` MUST hold a list for each of these, each
  carried out by the unit tests against a stand-in machine made for it: the
  system's own compiler; a compiler outside Spack reached through
  environment modules; a compiler built by Spack itself; a toolset beside
  the system's compiler; compilers present but not wanted; a site mirror
  with its own key; and the Cloud Sandbox's two scripts. Every example but
  the sandbox's MUST use neutral names. (Later, spec 004 added an eighth:
  Spack installed by the role's first step.)
- **FR-017**: The Cloud Sandbox's example MUST be held to the sandbox's own
  shell commands: a test runs those commands against a second stand-in and
  requires the same configuration in every scope, the same mirrors and
  trusted keys, and the discovery commands in the same order. (The commands
  need not be identical: `spack_config` writes two settings in one call
  where the script uses two.)
- **FR-018**: The examples in the documentation of 0.1.0's two modules,
  `spack_env` and `spack_buildcache_push`, MUST use neutral paths and names,
  as the test of FR-015 covers them.

**Documentation and release**

- **FR-019**: Each new module MUST have `DOCUMENTATION`, `EXAMPLES` and
  `RETURN`; the role MUST have a README documenting its variables, the
  kinds and their options, how the list is carried out, declared and
  discovered steps, and the examples; the collection's README and
  `CHANGELOG.md` MUST describe the role and the modules.
- **FR-020**: The role MUST NOT have a `meta/argument_specs.yml`. With one,
  ansible-core 2.16.20 prints a deprecation warning of its own on every use
  of the role (research R21); the role's first task checks the list
  instead (FR-011), and its README documents the variables.

### Key Entities

- **The list (`spack_setup`)**: the steps, in order: one site's set-up
  script, written as data. See [data-model.md](data-model.md).
- **A step**: a mapping with a `kind`, that kind's options, and optionally
  `label` and `environment`.
- **A kind**: what one step does, and the module that does it: `config`,
  `mirror`, `gpg_key` (declared state); `detect` (discovery); `command`
  (anything else, with a stated rule for change); `environment` (the
  environment later steps run in).
- **A captured environment**: the variables an `environment` step's shell
  lines set or changed, kept for the rest of one application of the role
  under the step's `name`.
- **The results (`spack_setup_results`)**: one entry per step.
- **An example**: a list under `docs/examples/`, data and not behaviour of
  the collection, carried out by the tests.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The role's defaults hold no step, and the test that reads the
  plugins and the role for the Cloud Sandbox's names passes. (It caught one
  such name on its first run.)
- **SC-002**: The Cloud Sandbox's example leaves the stand-in Spack in the
  state the sandbox's shell commands leave it in, with the discovery
  commands in the same order.
- **SC-003**: Against the real Spack v1.2.0, a list applied twice changes
  nothing the second time, and check mode before the first run names every
  declared change and makes none.
- **SC-004**: With the real oneAPI, in the Cloud Sandbox's test container,
  the sandbox's two lists applied from the built 0.3.0 tarball over scopes
  wiped of what the shell had written make 7 changes the first time, 0 the
  second, and 0 in check mode afterwards; and the scopes, compared as data,
  match what the shell had written in every section but one attribute (an
  `id` on three compiler entries, left by an earlier trial's
  `spack compiler remove`: research R19). This was a trial by hand, not a
  test that is kept.
- **SC-005**: Every option of every kind, a second run changing nothing,
  check mode, `require` failing, the removed-compiler accident reproduced
  and caught, and a bad list refused before anything runs are each held by
  a unit test against the stand-in Spack.
- **SC-006**: Each of the seven examples is carried out by a unit test.

## Assumptions

- The work was tested against the real Spack v1.2.0, the version the Cloud
  Sandbox pins, and needs Spack 1.0 or later. (Later, spec 003: the
  integration tests run against 1.0.0, 1.1.0 and 1.2.0, and the modules
  follow the version they find.)
- The sandbox's lists are proved against the real oneAPI where oneAPI is:
  in the Cloud Sandbox's container test, once the sandbox adopts the role.
  The collection does not install a compiler to test itself; the trial of
  SC-004 was made by hand in that container.
- "Site" means an installation that uses the collection, such as the Cloud
  Sandbox, not Spack's `site` configuration scope, which the modules
  support like any other scope and which is the role's default scope.
- `just test` takes two to three minutes, not one: its 193 tests each run
  Ansible.
- The work was asked for, planned and decided on 2026-11-14, before this
  repository used Spec Kit; this spec was written from that plan on
  2026-11-27. The code of 0.3.0 itself is no longer in the repository
  (the history was reset on 2026-11-18); what is said here was checked
  against the code released in 0.0.1 and against today's.

## Out of Scope

- **Using this in the Cloud Sandbox.** That is the sandbox's own work: its
  two lists become variables of its `spack` and `intel_oneapi` roles, each
  step carrying its traceability to `funcs-setup-instance.sh` as a comment;
  its shell tasks, `spack_fingerprint` and `spack_config_json` go;
  `spack-pubkey.sh` becomes a third list; and its container test proves all
  of it with the real oneAPI. (It was done the same day, in the Cloud
  Sandbox, and needed no change to 0.3.0:
  [spec 010](../010-sandbox-adopts-setup/spec.md).)
- Installing Spack itself, or any compiler: a site's playbook does that,
  before or between applications of the role. (Later, spec 004 added a step
  that installs Spack; installing a compiler is still the site's.)
- Per-user configuration (`~/.spack/config.yaml`): `spack_config` with
  `scope: user` can write it, but the sandbox writes it from a template,
  which is right for a whole file Ansible owns.
- Private keys, and signing.
- Testing against a fork of Spack (the sandbox's UFS add-on uses
  spack-stack). Its extra subcommands can be written as `command` steps;
  whether they work is that site's to prove.
