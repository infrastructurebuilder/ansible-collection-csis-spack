# Interface contract: `yes_to_all`, and what `spack_gpg_key` runs

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)

What a playbook can write, and what Spack is then run with. The tests hold
each line of this.

## Module option, on `spack_buildcache_push`, `spack_command`, `spack_config`, `spack_detect`, `spack_env`, `spack_gpg_key`, `spack_mirror`

```yaml
yes_to_all:
  description:
    - Answer "yes" to every confirmation Spack asks of a command this module
      runs to change something, by giving that command C(--yes-to-all) where
      the installed Spack's help for it lists the option.
    - That includes confirmations before removing or overwriting something.
      Without it, such a confirmation fails the task, since Ansible gives
      Spack no terminal to answer from.
    - A command that already has C(-y) or C(--yes-to-all) is left as it is.
  type: bool
  default: false
```

`spack_gpg_key` adds: *"Changes nothing in this module: it answers Spack's
confirmation for the keys it is asked to trust in any case."*
`spack_command` adds: *"The command is read from the leading words of
I(args), up to the first option. A subcommand written after an option of
its parent, as in C(config --scope user add …), is not seen, and the parent's
help decides; no such subcommand has C(--yes-to-all) in Spack 1.0 to 1.2."*

## Role

```yaml
# roles/setup/defaults/main.yml
spack_setup_yes_to_all: false
```

```yaml
# a step
- kind: command            # or config, mirror, gpg_key, detect
  yes_to_all: true         # overrides spack_setup_yes_to_all for this step
  args: [uninstall, -a, zlib]
  changes: always
```

`yes_to_all` on a step of kind `environment` is reported by
`setup_problems` as "not an option of this kind", and nothing runs.

## What `spack_gpg_key` runs

| Input | Spack whose help lists `--yes-to-all` (1.2) | Spack whose help does not (1.0, 1.1) |
| --- | --- | --- |
| `key: <file or URL>` | `spack gpg trust --yes-to-all <file>` | `spack gpg trust <file>` |
| `from_mirrors: true` | `spack buildcache keys --install --trust --yes-to-all` | `spack buildcache keys --install --trust` |

whatever `yes_to_all` says. Before each, `spack gpg trust --help` or
`spack buildcache keys --help` is run once. In check mode neither trust runs,
and no help is read for them.

Reported, unchanged: `changed` is true when a key is in
`spack gpg list --trusted` afterwards and was not before; `trusted` lists
those keys.

## What the other modules run with `yes_to_all: true`

On Spack 1.2.0, from [../research.md](../research.md), R1:

| Module | Gets `--yes-to-all` | Help read, option absent |
| --- | --- | --- |
| `spack_env` | `install`; `module <system> refresh` has `-y` already | `concretize` |
| `spack_command` | whatever the site's command takes (`uninstall`, `gc`, `env remove`, …) | any other |
| `spack_buildcache_push`, `spack_mirror`, `spack_config`, `spack_detect` | nothing today | each command they change something with |

With `yes_to_all: false` these modules read no help and run exactly what
0.0.2 ran.
