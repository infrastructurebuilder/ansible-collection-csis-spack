# Data Model: `yes_to_all` and the help check

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

There is no stored data. What follows is the values the feature passes
around, and the rules that hold between them.

## The flag

| Where it is set | Name | Type | Default | Overrides |
| --- | --- | --- | --- | --- |
| A module's option | `yes_to_all` | bool | `false` | — |
| The `setup` role, for every step | `spack_setup_yes_to_all` | bool | `false` | — |
| One step of `spack_setup` | `yes_to_all` | bool | the role's variable | the role's variable |

- The role passes each step's value to the step's module. A step of kind
  `environment` has no Spack to run, and `yes_to_all` there is a problem
  reported by `setup_problems`, before any step runs.
- `shell_environment` has no `yes_to_all`.

## Consent

Whether a command is answered at all:

| Command | Answered when |
| --- | --- |
| `spack_gpg_key`'s `gpg trust <file>` and `buildcache keys --install --trust` | always (the module's own consent) |
| A command a module runs to change something | the flag is true |
| A query (`find`, `config get`, `mirror list`, `gpg list`, `location`, `--version`, `buildcache check`) | never |

## The command's words

The leading arguments that name the Spack command, as opposed to its options
and its own arguments.

- Given by the module for its own commands: `gpg trust` (2),
  `buildcache keys` (2), `module tcl refresh` (3), `install` (1), …
- Walked for `spack_command`: the first argument, if it is not an option;
  then each next argument, while the help read so far lists it as a
  subcommand (with its alias, as in `push (create)`), stopping at the first
  argument that starts with `-`.
- No words (the first argument is an option, or `args` is empty): nothing is
  added and no help is read.

## The help cache

One per run of a module (one `Spack` object): a mapping from a command's
words to what its help said.

| Field | Meaning |
| --- | --- |
| words | the command, as a tuple (`("buildcache", "keys")`) |
| takes | whether the help lists `-y, --yes-to-all` |
| subcommands | the subcommand names and aliases the help lists, for the walk |

A help that fails is cached as `takes = false`, no subcommands.

## Rules

1. `--yes-to-all` is added only when: the command is answered (Consent), and
   neither `-y` nor `--yes-to-all` is among its arguments, and the help of its
   words lists the option.
2. It is inserted straight after the command's words.
3. Nothing is ever written to Spack's stdin.
4. Which commands were answered does not change what a module reports as a
   change (Principle II).
