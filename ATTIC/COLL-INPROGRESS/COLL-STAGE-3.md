# Collection stage 3: the Cloud Sandbox moves to 0.3.0

*Status:* planned 2026-11-14 on `feature/coll-stage-3`; the decisions
were asked the same day and are under [Decisions taken](#decisions-taken);
executed the same day on "do coll 3", in Cloud-Sandbox, on its branch
`feature/stage-11-csis-spack-0.3.0`. Committed locally in both
repositories; nothing merged or pushed. The result is under
[Outcome](#outcome). The collection itself did not have to change.

## What this stage is, and where its work happens

Stages 1 and 2 changed this collection. This one changes its first user:
the Cloud Sandbox's `sandbox-provisioning`, in the Cloud-Sandbox
repository under `exportit/`, which still pins the collection at `0.1.0`
and still sets Spack up in bash. The plan is kept here, with the other
collection stages, because it is where 0.2.0 and 0.3.0 are proved on the
machine they were written for.

- **The changes are made in Cloud-Sandbox**, on a feature branch there
  (`feature/stage-11-csis-spack-0.3.0`), under that repository's rules:
  its copies stay byte-identical, its translations keep their
  traceability to `funcs-setup-instance.sh`, its root `just test` and
  `just full-test` are the bar, and nothing is pushed to IOOS.
- **Cloud-Sandbox records it as its stage 11:** a short
  `INPROGRESS/STAGE-11.md` that points here and carries the decisions and
  the outcome, and a row in its `INPROGRESS/TODO.md`.
- **This collection changes only if the move finds a defect in it.** That
  would be fixed here, released as 0.3.1, and pinned there.

## Why

`sandbox-provisioning` uses `spack_env` from 0.1.0 for its Spack
environment (the sandbox's stage 10). Since then:

- **0.2.0** changed a default. `spack_env` regenerates module files only
  when needed, where 0.1.0 and the sandbox's script regenerate on every
  run. The role passes `modules: [tcl]` and nothing else, so moving the
  pin changes what the role does without a line changing there.
- **0.3.0** can replace the shell that still sets Spack up: one task in
  the `spack` role and three in `intel_oneapi`, each telling a change by
  hashing Spack's whole configuration through `spack python -c`.
- Trying things for stage 2 showed three things about the sandbox itself
  that its records do not say, or say wrongly (below).

## What exists (Cloud-Sandbox, `exportit/sandbox-provisioning/`)

| What | Where | Today |
| --- | --- | --- |
| The pin | `requirements.yml`; `exportit/cloud-sandbox/units.toml`; a test in `exportit/tools` holds the two together | `0.1.0` |
| The environment | `roles/spack_environment/tasks/main.yml`: one `spack_env` task | no `refresh_modules` |
| Setting Spack up | `roles/spack/tasks/main.yml` L92-L119: one shell task (`funcs-setup-instance.sh` L661-L700) | bash, `spack_fingerprint` |
| The Intel part | `roles/intel_oneapi/tasks/main.yml`: "Let Spack find the Intel compilers" (L919, L928-L937), "Tell Spack that MKL and MPI are installed outside it" (L709-L732, L941-L949), "Make the Intel libraries Spack's providers" (L951-L955, L959) | bash, a here-document, `spack_fingerprint` |
| The fingerprint | `group_vars/all.yml`: `spack_config_json`, `spack_fingerprint`; also used by `tests/container/verify.yml` | `spack python -c` |
| Parity tests | `tests/test_parity.py`: `test_the_spack_role_runs_the_scripts_commands_in_order` reads the `$spack` lines of the shell task; `test_spack_is_told_about_the_same_externals_and_providers` reads two role variables | tied to the shell's text |
| Traceability | `tests/test_traceability.py`: every task names its lines; every line that does something is replaced or in `tests/not_carried.yml` | one comment per task |
| The container test | `tests/container/converge.sh` applies `spack` and `intel_oneapi` twice, with the real oneAPI; `verify.yml` greps Spack's configuration | second run must change nothing |
| The site mirror's key, by hand | `exportit/sandbox-ops/bin/spack-pubkey.sh`, a byte-identical copy marked in use; the setup has these steps commented out | a script |

What stage 2 found, to be acted on or recorded here:

1. **The two `compiler find` steps do not undo each other.** The
   sandbox's stage 3 recorded that they do, and its `spack` role loads
   the Intel modules "when they exist" to prevent it. With Spack v1.2.0,
   detection never removes: without the modules it finds no Intel
   compiler and leaves the registered ones alone.
2. **The script's two settings are in the user scope.** `spack config add`
   without `--scope` writes to the login user's `~/.spack`. The
   install-tree padding and the Tcl modules are there, and only there.
3. **`spack external find` does not detect the dnf-installed MKL and
   MPI.** They stay declared.

## Items

1. **The pin moves to 0.3.0:** `requirements.yml`, `units.toml`. `just
   init` installs it; the container and the first-boot template already
   install `requirements.yml` before the plays.

2. **`spack_environment` says what it wants** (the note left by stage 1).
   Its `spack_env` task gets `refresh_modules`, and the comment beside it
   says where that differs from the script.

   **YOUR DECISION (`refresh_modules` in the sandbox):** `when_needed`
   (default): a second run of `site.yml` touches no module file, and a
   file deleted or edited by hand is still put back. Differs from the
   script, which regenerates every time; noted with the task. Or
   `always`: as the script.

3. **The `spack` role's shell task becomes the `setup` role with a
   list.** The task is replaced by one `include_role` of
   `infrastructurebuilder.csis_spack.setup`, applied as the login user
   (`apply: {become: true, become_user: "{{ sandbox_user }}"}`), under
   the same `when: spack_save.stat.exists`. The list is
   `docs/examples/cloud-sandbox.yml`'s `spack_setup_base`, with the
   sandbox's variables in place of its literals where it has them.
   - The conditional loading of the Intel modules goes (finding 1): the
     list has no environment step. The comment that explained it is
     replaced by what was found.
   - `buildcache keys` needs the network, as it does today.

   **YOUR DECISION (where the lists live):** as `vars:` of the
   `include_role` task, in the role's tasks file (default): the steps sit
   where the shell sat, and each step carries its own `# Replaces
   funcs-setup-instance.sh L<n>` comment; or in the role's
   `defaults/main.yml`, where a site can override a whole list, with the
   comments there.

   **YOUR DECISION (the two settings' scope):** keep them in the user
   scope, `scope: user`, as the script has them (default: this stage
   moves what exists and proves it the same; the finding is recorded in
   MAP.md for a decision of its own); or move them to the site scope
   now, where every user and every node gets them, as a deliberate
   difference from the script, noted with the step and in
   `tests/not_carried.yml`.

4. **`intel_oneapi`'s three Spack tasks become the `setup` role with the
   second list:** `spack_setup_intel` of the example, built from
   `sandbox_modules_init`, `sandbox_load_intel_modules`,
   `intel_oneapi_spack_externals` and `intel_oneapi_spack_providers`, so
   that those variables stay the one place the values are. The
   environment step runs the two shell variables; the detect step
   requires `intel-oneapi-compilers@{{ oneapi_version }}`.
   - `intel_oneapi_spack_packages_file` goes: nothing writes that file by
     hand any more.
   - An external whose version or prefix changes is now corrected. The
     here-document skipped any package whose name was already in the
     file.

5. **What the shell needed goes:** `spack_config_json` and
   `spack_fingerprint` leave `group_vars/all.yml`. `verify.yml` reads
   the configuration with `spack config get --json` instead.

6. **Traceability and parity, kept.**
   - `tests/test_traceability.py` learns to read a `# Replaces` or
     `# New:` comment on each step of a list, as it does on each task.
     Every line of the four functions that does something is still
     either replaced or in `tests/not_carried.yml`.
   - `tests/test_parity.py`: the test that read the `$spack` lines of the
     shell task instead reads the script's Spack commands (L661-L700,
     L919-L959) and holds the two lists to them, command for step: each
     `config add` path is a setting of a `config` step in the scope the
     script writes it to, each `compiler find` and `external find` is a
     `detect` step with the same options, the `mirror add` is the
     `mirror` step, each `buildcache keys` is a `gpg_key` step, in the
     script's order. The externals and providers are held to the script
     as they are today.

7. **Validation in the container, with the real oneAPI.** The container
   test starts from a fresh Spack clone, so its first application is the
   whole of both lists.
   - Applied twice, as today; the second run must change nothing.
   - `verify.yml` stops grepping and compares data. After the run, each
     scope's `config`, `modules`, `mirrors` and `packages` (the declared
     part: providers, the two externals, `cmake` not buildable), read
     with `spack config --scope <s> get --json`, must equal what the
     variables say; `spack compiler list` must hold the system's GCC and
     the Intel compilers at `oneapi_version`.
   - Check mode after the second run reports no change.

   **YOUR DECISION (a side-by-side proof):** add to the container test a
   one-time comparison with the shell (default): before this stage's
   change is made, dump what the present shell roles leave in the site
   and user scopes into `tests/container/expected-spack-config.json`;
   afterwards the container test holds the new roles' result to that
   file, as data. It is the comparison stage 2 made by hand, kept. Or
   rely on `verify.yml`'s comparison with the variables alone.

8. **The site mirror and its key.**

   **YOUR DECISION (`spack-pubkey.sh`):** leave it (default): it is a
   tool in `sandbox-ops`, run by hand, and the setup has its steps
   commented out; moving it is a change of what the sandbox does, not of
   how. Or make it a third list, `spack_setup_site_mirror`, applied when
   a variable says so: a `gpg_key` step with `spack_key_url` and the
   key's fingerprint, a `mirror` step with `spack_mirror`, and
   `from_mirrors`; `spack-pubkey.sh` is then superseded and goes to the
   attic with its catalogue row.

9. **Records, in Cloud-Sandbox.**
   - `exportit/MAP.md`: the `sandbox-provisioning` section (the lists,
     the variables gone, what the container now proves); the stage 3
     note that the two `compiler find` steps undo each other, corrected
     with what was found; the two settings in the user scope, under
     "Found"; the collection's section and state at 0.3.0.
   - `INPROGRESS/STAGE-11.md` and `TODO.md`.
   - `sandbox-provisioning/README.md`: `just init`'s line, and the
     roles' table where it describes the two roles.

## Decisions taken

Asked one at a time on 2026-11-14, before execution.

1. **`refresh_modules` in the sandbox:** `when_needed`.
2. **Where the lists live:** in the tasks files, as `vars:` of the
   `include_role` task, each step with its own `# Replaces` comment.
3. **The two settings' scope:** **site**, not the default. The operator
   first asked whether 0.3.0 can set a step's scope (it can: `scope` on
   the step, or the role's `spack_setup_scope`; no change to the
   collection), then chose to move the install-tree padding and the Tcl
   modules to the site scope.
4. **A side-by-side proof:** yes, a recorded comparison with what the
   shell roles leave.
5. **`spack-pubkey.sh`:** a third list, off by default.
6. **How Cloud-Sandbox records it:** as its stage 11, with a short
   `INPROGRESS/STAGE-11.md` that points here.

### What the decisions change in the items

- **Item 3 (decision 3).** The first step of the first list has no
  `scope`, so it takes the role's `site`. This is a deliberate
  difference from the script, which leaves the two settings in the login
  user's `~/.spack`. It is said in a comment on the step (`# Replaces
  funcs-setup-instance.sh L672-L673`, and that the script's `config add`
  has no `--scope`), in `tests/not_carried.yml` (what is not carried:
  that the settings are the login user's alone), and in MAP.md under
  what the role does differently on purpose. The parity test holds the
  step's settings to the script's two paths, and its scope to `site`.
  - On a head node built before this change, the two settings are still
    in the login user's `~/.spack/config.yaml` and `modules.yaml`, where
    they have the same values and do no harm. The list does not remove
    them: that would be a step of state `absent` in the user scope, and
    the operator has not asked for it. MAP.md says so.
- **Item 7 (decisions 3 and 4).** `expected-spack-config.json` is what
  the present shell roles leave, dumped before the change and committed
  unedited. The container test compares the new roles' result with it as
  data, **expecting exactly one difference, stated in the test:** `config`
  and `modules` of the user scope are empty, and the site scope's
  `config` and `modules` hold what the user scope's held. Any other
  difference fails.
- **Item 8 (decision 5).** A third list, `spack_setup_site_mirror`, in
  the `spack` role, applied by a second `include_role` only when a new
  variable, `spack_site_mirror`, is true; it is false by default, so a
  build does what it does today.
  - The steps, from `spack-pubkey.sh` in its order: a `gpg_key` step
    with `spack_key_url` and the key's fingerprint (a new variable,
    `spack_key_fingerprint`; the fingerprint is the name of the public
    key file the sandbox already keeps,
    `sandbox-ops/keys/22DC0120263F329AE5C9DA08F525C05B06DCA266.pub`); a
    `mirror` step named `s3-mirror` with `spack_mirror`; a `gpg_key`
    step with `from_mirrors`. Each carries `# Replaces
    scripts/spack-pubkey.sh L<n>`.
  - `spack_key`, the path the script downloads the key to, goes: the
    module fetches the key itself.
  - `spack-pubkey.sh` is then superseded. In Cloud-Sandbox's terms: its
    row in `sandbox-ops/CATALOGUE.tsv` moves to the attic's catalogue as
    superseded by the list; `sandbox-ops.map` loses the line and
    `cloud-sandbox.map` gains it under `attic/superseded/`; the counts in
    `sandbox-ops/README.md`, the attic's README and MAP.md follow (15
    files in use, the key among them, and 27 superseded); its shellcheck count leaves
    `sandbox-ops/tests/shellcheck.counts`. The copy stays byte-identical.
    The public key file stays in `sandbox-ops/keys/`: the mirror tools
    there still sign with that key.
  - **Not proved by this stage:** applying the third list needs the
    site's real S3 bucket and its published key. The parity test holds
    the list to the script's commands, and the unit tests of the
    collection cover each kind; the list itself is first applied in the
    live proof on AWS. The plan says so in MAP.md.
- **Item 9 (decision 6).** Cloud-Sandbox's branch is
  `feature/stage-11-csis-spack-0.3.0`; `INPROGRESS/STAGE-11.md` is short,
  points here, and carries these decisions and the outcome.

## Out of scope

- Using `spack_buildcache_push` for the `sandbox-ops` mirror scripts.
- The UFS spack-stack.
- Removing the two settings from the login user's scope on a head node
  that already has them there.
- Applying the site mirror's list against the real bucket.
- The live proof on AWS.

## Acceptance

- In Cloud-Sandbox, the root `just test` and `just full-test` pass.
- The container applies `spack`, `intel_oneapi` and `spack_environment`
  through the collection twice; the second run changes nothing, and check
  mode afterwards reports no change.
- No task of the `spack` and `intel_oneapi` roles runs Spack through a
  shell; `spack_fingerprint` and `spack_config_json` are gone.
- Every line of `install_spack`, `install_intel_oneapi_dnf` and
  `add_spack_site_external` that does something is still replaced by a
  task or a step that names it, or listed in `tests/not_carried.yml`.
- The new roles leave the same configuration, as data, as the shell
  roles did, but for the one difference decided: the padding and the Tcl
  modules are in the site scope.
- With `spack_site_mirror` false, the default, the site mirror's list is
  not applied, and `spack-pubkey.sh` is in the attic, superseded.

## Outcome

Recorded in full in Cloud-Sandbox's `INPROGRESS/STAGE-11.md` and its
`exportit/MAP.md`. For this collection:

- **0.3.0 needed no change.** The sandbox's two lists, and its third,
  are carried out by the `setup` role as released. Under `--tags`, with
  the role included from a tagged role, every step runs (tried first:
  the tags of the including task reach the role's own includes). Applied
  with `apply: {become: true, become_user: ...}`, every step ran as that
  user.
- **With the real oneAPI, in the sandbox's container test:** installed
  from the tag `0.3.0`; first apply of the sandbox's `site.yml`, 55
  changes; second, 0; the three roles that use the collection once more
  in check mode, 0 changes. What Spack was told is the same, as data, as
  what the sandbox's shell left, but for the one difference decided (the
  two settings in the site scope).
- **Found about using `spack_env`:** Ansible refuses a task that is both
  asynchronous and in check mode, and a build wants `async`. A playbook
  that wants both writes `async: "{{ 0 if ansible_check_mode else <seconds> }}"`,
  and the same for `poll`. The module's notes say only to use `async`;
  they should say this too (a documentation change for the next
  version).
- **What differs from this plan** is listed in Cloud-Sandbox's
  `STAGE-11.md`: `spack-pubkey.sh` went to `sandbox-provisioning/legacy/`
  and not to the attic; `spack_key` stays; the scope decision is on the
  step and in MAP.md, not in `not_carried.yml`; the site mirror goes to
  the site scope too; the side-by-side proof compares externals by
  package name.
- **Not proved:** the site mirror's list against the real bucket.

