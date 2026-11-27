# Research: Say how to preview a long build

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Retrospective. The finding was made on 2026-11-14, in the Cloud Sandbox's
container test during its move to 0.3.0 (collection stage 3), and recorded in
that stage's outcome. Where Ansible makes the decision was read on 2026-11-27
in ansible-core 2.16.20, the version in this repository's tool environment,
to write this file. No Spack behaviour is involved: Ansible decides before the
module runs.

## R1. What Ansible does with `async` in check mode

**Found:** Ansible refuses a task that is both asynchronous and in check
mode. The task fails with "check mode and async cannot be used on same
task." and the module is not run. In ansible-core 2.16 the check is in the
action plugins' base class, at the start of `ActionBase.run`
(`ansible/plugins/action/__init__.py`):

```python
elif self._task.async_val and self._task.check_mode:
    raise AnsibleActionFail('check mode and async cannot be used on same task.')
```

So a `spack_env` task with `async: 86400`, the documented way to run a
build that takes hours, cannot be previewed with `--check`, although the
module supports check mode.

`async` is an integer keyword that is templated before the check
(`async_val`, default 0), so a template that gives 0 in check mode passes
it: 0 is false. With `async` of 0 the task runs as an ordinary one; Ansible
reads `poll` only when `async` is above 0
(`ansible/executor/task_executor.py`: `if self._task.async_val > 0:` and,
inside it, `if self._task.poll > 0`).

A preview needs no `async`: in check mode `spack_env` concretizes a copy of
the environment in a temporary directory and installs nothing.

**Decision:** the documentation gives both keywords in a form that falls to
0 in check mode:

```yaml
async: "{{ 0 if ansible_check_mode else 86400 }}"
poll: "{{ 0 if ansible_check_mode else 60 }}"
```

`poll` is written the same way, though Ansible ignores it when `async` is 0,
so that no example leaves either keyword as a plain number for the test to
allow. The numbers are the examples' own; a site sets its own.

**Held by:** [tests/unit/test_async_and_check_mode.py](../../tests/unit/test_async_and_check_mode.py),
whose `test_a_plain_number_cannot_be_previewed` runs `async: 86400` with
`--check` and expects Ansible's message, so that a future ansible-core that
dropped the refusal would show up as a failing test.

**Alternatives considered:**

- Telling a site not to use `async`: a build of hours then holds the
  connection open for its whole length.
- Making the module refuse or work around it: it cannot. The refusal happens
  before the module runs (spec, FR-007: no module changes).
- Two tasks, one for check mode and one for a real run, chosen by `when`:
  twice the text for the same task, and the two drift apart.

**Not tried:** a task that sets `check_mode: true` on itself, instead of a
play run with `--check`, together with the form.
