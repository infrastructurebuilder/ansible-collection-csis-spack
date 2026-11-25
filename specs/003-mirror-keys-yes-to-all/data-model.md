# Data Model: `yes_to_all`, the help check and the version table

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
| `spack_gpg_key`'s `gpg trust <file>` and `buildcache keys --install --trust` | always (the module's own consent), where the version table says Spack asks (1.2 and later); no help is read |
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

## The version table (`BEHAVIOUR`, User Story 3)

A mapping in `plugins/module_utils/spack.py` from (major, minor) to what
that Spack does, for the commands the collection runs itself. The row of a
version is its own, or the last one before it: 1.0.4 is read as 1.0, and a
Spack newer than the last row as the last row.

| Field | 1.0 | 1.1 | 1.2 | When false |
| --- | --- | --- | --- | --- |
| `config_json` | false | true | true | configuration is read through `spack python -c`, printing `spack.config.get(section)` or `spack.config.CONFIG.get_config(section, scope=scope)` as JSON, on one line |
| `gpg_colons` | false | false | true | the trusted keys are read from `gpg list --trusted`'s own listing: each fingerprint, 40 hexadecimal digits, on a line of its own |
| `trust_answers` | false | false | true | the trusts run without `--yes-to-all`: Spack does not ask, and refuses the option |
| `scope_needs_directory` | false | true | false | (when true) a scope whose directory is missing cannot be written; the module fails, naming the scope and its directory, and does not make it |

The version is the one `spack --version` gave, which every module reads
first (`Spack.found`). A scope whose directory is missing is read as empty in
every version: 1.0 prints it empty, 1.1 and 1.2 refuse it in words of their
own, which the shared code knows.
