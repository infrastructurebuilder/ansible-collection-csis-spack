# Feature Specification: `spack_env` finds a module root written with `$env`

**Feature Branch**: `feature/module-root-variables`

**Created**: 2026-11-27, on the operator's instruction of that day in the
Cloud Sandbox (its spec 004, T020): the collection's bug "gets a spec of its
own in ansible-collection-csis-spack".

**Status**: Draft

**Input**: User description: "spack_env reads the module root `$env/modules`
from spack-stack's configuration without expanding `$env`, finds no such
directory, and regenerates the modules with `--delete-tree` on every run,
without reporting it."

## What happened

On 2026-11-27 the Cloud Sandbox's spec 004 applied its playbook
`ufs-stack.yml` twice on a head node, with the collection's 0.0.3. The
environment it builds is spack-stack's, whose `modules.yaml` sets the Tcl
module root to `$env/modules`: Spack's variable for the environment's own
directory. Each run, `spack_env` (with `modules: [tcl]` and
`refresh_modules: when_needed`) reported:

```text
modules_reason: missing_root
modules_refreshed: []
changed: false
```

and the module files' timestamps showed that it had regenerated them with
`--delete-tree` all the same, on every run. The module looks for the root at
the literal path `$env/modules`: it replaces `$spack` and `${spack}` in a
root, and no other variable of Spack's. That path never exists, so every run
gives `missing_root` and regenerates. It then compares the tree at that same
literal path before and after, finds it empty both times, and says that
nothing was refreshed, so the run reports no change although every module
file was rewritten.

In the Cloud Sandbox the regeneration deleted the meta-modules that
spack-stack writes into the same root, so the next step ran again and the
playbook never settled. The sandbox works around it (it no longer asks
`spack_env` for module files); this spec is the collection's fix.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A root written with Spack's variables is found (Priority: P1)

A site's environment sets its module root with a variable Spack expands,
`$env` above all (an environment's own `modules` directory, as spack-stack
does). `spack_env` regenerates the module files the first time, and on the
next run, with nothing changed, it leaves them alone and says so.

**Why this priority**: today every such site's module files are deleted and
written again on every run, silently; anything else kept under the root is
lost each time.

**Independent Test**: an environment whose Tcl root is `$env/modules`; apply
`spack_env` with `modules: [tcl]` twice; the first run regenerates and
reports it, the second reports `not_needed` and no change, and the files'
timestamps are unchanged.

**Acceptance Scenarios**:

1. **Given** an environment whose module root is `$env/modules`, **When**
   `spack_env` runs with `modules: [tcl]` after a change to the environment,
   **Then** it regenerates the module files under the environment's own
   `modules` directory and reports `modules_refreshed: [tcl]` and a change.
2. **Given** the same environment, regenerated and unchanged since, **When**
   `spack_env` runs again, **Then** it reports `modules_reason: not_needed`,
   regenerates nothing and reports no change.
3. **Given** a root written with `${env}`, `$spack`, `${spack}` or `~`, or as
   an absolute path, **When** `spack_env` runs, **Then** it finds the root
   Spack uses, in each case.

---

### User Story 2 - A refresh is never hidden (Priority: P1)

Whatever the root, when `spack_env` regenerates module files it says so: in
`modules_refreshed`, and as a change.

**Why this priority**: a module that rewrites files and reports nothing breaks
the collection's first promise (a run that changes nothing says so, and a run
that changes something says that).

**Independent Test**: any case in which the module regenerates; the result
names the module system and reports a change.

**Acceptance Scenarios**:

1. **Given** a run that regenerates module files, **When** it ends, **Then**
   `modules_refreshed` names each module system regenerated and the task
   reports a change, unless the files it wrote are byte for byte what was
   there.
2. **Given** a root that cannot be resolved (a variable the module does not
   know), **When** `spack_env` runs, **Then** it fails before regenerating,
   naming the root and the variable, rather than guessing.

---

### User Story 3 - A site knows what happens to files it changes under the root (Priority: P2)

Some tools write into the module root after Spack (spack-stack's
`setup-meta-modules` adds a `Core` directory and rewrites Tcl files). With
`refresh_modules: when_needed`, `spack_env` sees those files as changed and
regenerates them, with `--delete-tree` removing what the tool added. A site
needs that written where it reads about `refresh_modules`, with what to do
instead.

**Why this priority**: the behaviour is right for Spack's own files, but a site
using such a tool needs to know before it meets it.

**Independent Test**: the module's documentation says it, and a test holds the
documentation to the behaviour.

**Acceptance Scenarios**:

1. **Given** the documentation of `refresh_modules` and `delete_tree`, **When**
   a site reads it, **Then** it says that files changed or added under the
   root after a refresh make the next run regenerate them, that
   `--delete-tree` removes what was added, and what a site does when another
   tool writes there (leave `modules` empty and make the module files itself,
   or keep that tool's files outside the root).

---

### Edge Cases

- **The environment is given by a link** (`/save` to `/mnt/efs/...`): `$env`
  is the environment's directory as Spack resolves it; the module compares the
  same tree whichever spelling it is given.
- **Check mode**: the preview resolves the root the same way, and says that
  the files would be regenerated only when they would.
- **An existing stamp** (`csis_spack.modules.json`) written by an earlier
  version with the literal root: the first run after the fix regenerates
  once, reports it, and writes a correct stamp.
- **Lmod**: the same rules for its root.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `spack_env` MUST resolve a module root as the installed Spack
  does, for at least `$env`, `${env}`, `$spack`, `${spack}` and `~`, and an
  absolute path as it is. The resolution SHOULD be Spack's own (asked of the
  Spack on the node) rather than the module's copy of Spack's rules; the plan
  decides.
- **FR-002**: A root the module cannot resolve MUST fail the task before
  anything is regenerated, naming the root and what was not understood.
- **FR-003**: Every regeneration MUST be reported in `modules_refreshed` and
  as a change, measured on the resolved root.
- **FR-004**: The documentation of `refresh_modules` and `delete_tree` MUST
  say what happens to files changed or added under the root after a refresh,
  and what a site does when another tool writes there (User Story 3).
- **FR-005**: The integration tests MUST cover a root written with `$env`
  against the real Spack versions the collection supports, applied twice,
  the second run reporting no change and regenerating nothing.
- **FR-006**: The changelog MUST name the bug, the versions it was in (0.0.1
  to the last release before the fix), and what a site saw.

### Key Entities

- **A module root**: where a module system's files for an environment go,
  from the environment's `modules` configuration or Spack's default.
- **The stamp**: what `spack_env` records after regenerating, to tell next
  time whether it must again.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An environment whose Tcl root is `$env/modules`, applied twice,
  regenerates once and reports it once; the second run reports no change in
  10 runs out of 10, on each supported Spack.
- **SC-002**: No run that rewrites a module file reports `modules_refreshed:
  []`, in every case the tests cover.
- **SC-003**: The Cloud Sandbox's `ufs-stack.yml` could again hand the module
  files to `spack_env` for spack-stack's environment and settle, if it kept
  the meta-modules out of the root; whether it does is the sandbox's choice.

## Assumptions

- The roots a site writes use Spack's documented configuration variables;
  others are FR-002's case.
- The fix is a patch release (0.0.x), on the operator's word.
- The Cloud Sandbox does not wait for it: its 0.0.9 or later makes its module
  files itself (its spec 004, 2026-11-27).
