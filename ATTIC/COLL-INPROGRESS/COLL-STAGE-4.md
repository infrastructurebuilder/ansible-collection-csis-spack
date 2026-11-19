# Collection stage 4: say how to preview a long build (0.3.1)

*Status:* planned 2026-11-14 on `feature/remaining-plans`, and executed
the same day on "do coll 4", on `feature/coll-stage-4`, and merged into
`develop`. It was kept unreleased, by decision, until the Cloud
Sandbox's stage 12 found a defect in `spack_config` the same day; the
operator then chose to fix it and release both as 0.3.1, and to move the
sandbox's pin to it in that stage. The decisions are under [Decisions taken](#decisions-taken),
the result under [Outcome](#outcome). First in the order of the remaining
work (Cloud-Sandbox's `PLAN.md`): it depends on nothing and nothing waits
for it, and it is the smallest.

## Why

Found in collection stage 3, on the Cloud Sandbox's container test:
Ansible refuses a task that is both asynchronous and in check mode
("check mode and async cannot be used on same task"). A `spack_env` task
that builds wants `async`, since a build takes hours, and the module
claims check mode. Today its notes say only "Run the task with `async`
and `poll`", and its example and the README's do exactly that: copied as
they are, a playbook cannot be previewed. The sandbox found it the hard
way.

## Items

1. **`spack_env`'s notes** say that a task with `async` cannot run in
   check mode, and give the form that works:

   ```yaml
   async: "{{ 0 if ansible_check_mode else 86400 }}"
   poll: "{{ 0 if ansible_check_mode else 60 }}"
   ```

   with the reason: a preview builds nothing and is over in a minute, so
   it does not need `async`.

2. **The examples** in `spack_env`'s `EXAMPLES` and in the README use
   that form.

3. **A test** that holds the documentation to it: the unit test reads
   the module's `EXAMPLES` and the README, and fails on any `async:`
   with a literal number. And one that holds the module to the claim:
   the form above, run through `ansible-playbook --check` against the
   stand-in `spack`, passes and builds nothing.

4. **`CHANGELOG.md`**, 0.3.1: documentation only.

   **YOUR DECISION (the release):** cut 0.3.1 and push it (default: the
   documentation people read is the released one); or keep it on
   `develop` until the next change that needs a release.

   **YOUR DECISION (the Cloud Sandbox's pin):** leave it at 0.3.0
   (default: nothing it runs changes, and its role already uses the
   form); or move it to 0.3.1, which is one line in each of
   `requirements.yml` and `units.toml` and a container run.

## Decisions taken

Asked on 2026-11-14.

1. **The release:** keep it on `develop`, not the default. No tag; the
   version stays 0.3.0 in `galaxy.yml`, and the changelog names the
   change "Unreleased (to be 0.3.1)".
2. **The Cloud Sandbox's pin:** first answered "move it to 0.3.1", which
   cannot be done without a 0.3.1 tag, since the sandbox installs the
   collection from a tag. Asked again, the operator chose: **no tag now;
   the pin moves when 0.3.1 is cut.** That is the first thing to do at
   the release that follows: tag 0.3.1, then move
   `sandbox-provisioning/requirements.yml` and
   `exportit/cloud-sandbox/units.toml` to it, and run the container test.

## Out of scope

Any change to what a module does.

## Acceptance

`just test` and `just full-test` pass; `ansible-doc
infrastructurebuilder.csis_spack.spack_env` shows the note.

## Outcome

- `spack_env`'s notes say why `async` and check mode cannot go together
  and give the form; its example and the README's use it. `ansible-doc`
  shows the note.
- The README's two examples used one site's paths and names (the test
  for site knowledge looks only at `plugins/` and `roles/`); they are
  neutral now.
- `tests/unit/test_async_and_check_mode.py`: the notes and examples are
  held to the form, no example anywhere gives `async` or `poll` as a
  plain number, and against the stand-in `spack` the form previews
  without building, builds when not previewing, and a plain number fails
  in check mode with Ansible's own message.
- **Still to do, at the next release:** tag 0.3.1, and move the Cloud
  Sandbox's pin to it.

