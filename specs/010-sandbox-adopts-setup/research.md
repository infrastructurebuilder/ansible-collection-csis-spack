# Research: The Cloud Sandbox replaces its Spack set-up shell with the `setup` role

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

What was tried and found about the collection, and about the Spack it
drives, when the Cloud Sandbox moved to 0.3.0 on 2026-11-14. R6 to R8 were
found in collection [stage 2](../009-setup-role/spec.md)'s trials, with Spack v1.2.0, and acted on here.
The rest was found in this stage's work, which ran in Cloud-Sandbox; its own
record is that repository's `INPROGRESS/STAGE-11.md` and `exportit/MAP.md`.
Written down on 2026-11-27, from the collection's stage file.

## R1. 0.3.0 carries out a real site's lists as released

The sandbox's three lists use the kinds `config`, `detect`, `mirror`,
`gpg_key` and `environment`, with `scope`, `require`, `not_buildable`,
`externals`, `fingerprint` and `from_mirrors`. All were carried out by the
`setup` role of 0.3.0 with no change, and no defect was found that would
have been fixed as 0.3.1.

**Decision:** the collection does not change in this stage.

**Later:** "no change" held for what was run. On 2026-11-24 a `from_mirrors`
step stopped at Spack 1.2's trust prompt, against a mirror that published a
key in Spack's own layout. The public mirror the container used did not
make Spack ask, and the site mirror's list, which would have, was not
applied. The defect was fixed in 0.0.3
([specs/003-mirror-keys-yes-to-all/](../003-mirror-keys-yes-to-all/spec.md)).

## R2. A step can name its scope

Asked by the operator before deciding where the sandbox's two settings go.
A step names its configuration scope with `scope`; a step that names none
takes the role's `spack_setup_scope`, whose default is `site`. So the
sandbox's choice of the site scope needed only a step with no `scope`.

**Decision:** no change to the collection; the first step of the sandbox's
first list names no scope. (Today:
[roles/setup/defaults/main.yml](../../roles/setup/defaults/main.yml),
`spack_setup_scope: site`; each kind's tasks pass
`spack_setup_step.scope | default(spack_setup_scope)`.)

## R3. `--tags`, with the role included from a tagged role

Tried first, before the sandbox's roles were changed: the sandbox includes
the `setup` role from its own `spack` and `intel_oneapi` roles, which are
tagged, and runs its play with `--tags`. The tags of the including task
reach the role's own includes (today, its `include_tasks` of
[roles/setup/tasks/step.yml](../../roles/setup/tasks/step.yml) and of each
kind's file), so every step ran.

**Decision:** the role needs no tags of its own. (The role's README does
not say this today.)

## R4. `apply: {become: true, become_user: ...}`

The sandbox includes the role with
`apply: {become: true, become_user: "{{ sandbox_user }}"}`, so that its
Spack is set up as the login user. Every step ran as that user.

**Decision:** becoming another user is the site's, given on the
`include_role`; the role adds nothing for it. (The role's README does not
say this today.)

## R5. The real oneAPI, in the sandbox's container test

The collection was installed from the tag 0.3.0. The container test starts
from a fresh Spack clone, so its first application is the whole of both
lists. First application of the sandbox's `site.yml`: 55 changes. Second:
0. The three roles that use the collection, once more in check mode: 0
changes. What Spack was told, compared as data with what the shell roles
had left (recorded before the change), was the same but for the one
difference decided: the two settings in the site scope.

**Decision:** 0.3.0 is proved on the machine it was written for, for the
first two lists. The third list is not proved (R11).

## R6. The two `compiler find` steps do not undo each other

The sandbox's stage 3 recorded that they do, and its `spack` role loaded
the Intel modules "when they exist" to prevent it. With Spack v1.2.0,
detection never removes: run without the modules, `compiler find` finds no
Intel compiler and leaves the registered ones alone.

**Decision:** the first list has no `environment` step, and the
conditional loading of the Intel modules goes. (Today the stand-in `spack`
behaves the same way: its detection only adds,
[tests/unit/fake_spack_setup.py](../../tests/unit/fake_spack_setup.py).)

## R7. `spack config add` without `--scope` writes to the user scope

The script's two settings, `config:install_tree:padded_length` and the Tcl
modules, are written with `spack config add` and no `--scope`, so they are
in the login user's `~/.spack`, and only there.

**Decision:** the operator moved them to the site scope in the sandbox, as
a deliberate difference (spec, Clarifications). The collection's example,
[docs/examples/cloud-sandbox.yml](../../docs/examples/cloud-sandbox.yml),
keeps `scope: user`, because it reproduces the script, and says why in a
comment.

## R8. `spack external find` does not detect the dnf-installed MKL and MPI

**Decision:** they stay declared, with a `config` step of `packages`, as
the example's second list has them.

## R9. A declared external whose version or prefix changes

The sandbox's here-document appended an external to `packages.yaml` only
when no package of that name was there, so a changed version or prefix was
never written. A `config` step compares what it declares with what is there
and sets it.

**Decision:** nothing to do in the collection; the sandbox gains the
correction by moving.

## R10. `async` and check mode

Ansible refuses a task that is both asynchronous and in check mode ("check
mode and async cannot be used on same task"), and a build of a Spack
environment wants `async`. A playbook that wants both writes
`async: "{{ 0 if ansible_check_mode else <seconds> }}"`, and the same for
`poll`. 0.3.0's `spack_env` notes said only to use `async`.

**Decision:** a documentation change for the next version, not part of
this stage. It became collection [stage 4](../011-preview-long-builds/spec.md) and was released in 0.3.1; it is
in 0.0.1. Today: the notes and example of
[plugins/modules/spack_env.py](../../plugins/modules/spack_env.py), held by
[tests/unit/test_async_and_check_mode.py](../../tests/unit/test_async_and_check_mode.py),
and the last bullet of the constitution's principle II.

## R11. The site mirror's list cannot be proved here

Applying `spack_setup_site_mirror` needs the site's real S3 bucket and its
published key. The sandbox's parity test holds the list to
`spack-pubkey.sh`'s commands, and the collection's unit tests cover each
kind.

**Decision:** the list is first applied in the live proof on AWS, which is
out of scope.

## Decisions

| # | Decision | Alternatives considered |
| --- | --- | --- |
| 1 | The collection does not change (R1) | A fix released as 0.3.1, had the move found a defect |
| 2 | The site scope by a step with no `scope` (R2) | `scope: user`, as the script has it (the proposal) |
| 3 | No tags and no `become` in the role (R3, R4) | None was weighed: both worked as Ansible gives them |
| 4 | The `async` form is documented in the next version (R10) | None recorded |
