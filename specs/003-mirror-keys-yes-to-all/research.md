# Research: `spack_gpg_key` trusts the mirrors' keys without a prompt

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Date**: 2026-11-24

Everything here was tried against the real Spack on the local machine
(macOS), as Principle III asks: v1.2.0 in `.tmp/spack` (the integration
tests' pinned Spack), and v1.0.0 and v1.1.0 cloned for this research into
the session's scratch directory. Each was run with its own user scope and
cache (`SPACK_USER_CONFIG_PATH`, `SPACK_USER_CACHE_PATH`,
`SPACK_DISABLE_LOCAL_CONFIG=1`) and, where keys were trusted, a throwaway
`SPACK_GNUPGHOME`.

## R1. Which commands take `--yes-to-all`, by Spack version

`spack <command> --help`, searched for an option line
`-y, --yes-to-all  assume "yes" is the answer to every confirmation request`.

| Command | Run by | 1.0.0 | 1.1.0 | 1.2.0 |
| --- | --- | --- | --- | --- |
| `buildcache keys` | `spack_gpg_key` (`from_mirrors`) | no | no | **yes** |
| `gpg trust` | `spack_gpg_key` (`key`), today with `-y` always | no | no | **yes** |
| `install` | `spack_env` | yes | yes | yes |
| `module tcl refresh`, `module lmod refresh` | `spack_env`, today with `-y` always | yes | yes | yes |
| `uninstall`, `gc`, `env remove` | only through `spack_command` | yes (`uninstall`) | yes (`uninstall`) | yes |
| `buildcache push`, `buildcache check` | `spack_buildcache_push` | no | no | no |
| `compiler find`, `external find` | `spack_detect` | no | no | no |
| `concretize` | `spack_env` | no | no | no |
| `mirror add`, `mirror remove`, `mirror list` | `spack_mirror` | no | no | no |
| `config add`, `config remove`, `config get` | `spack_config` and the shared code | no | no | no |
| `env create` | only through `spack_command` | no | no | no |
| `repo add`, `repo remove`, `compiler remove` | only through `spack_command` | no | no | no |
| `gpg list`, `find`, `location`, `--version` | queries in the shared code | — | — | no |

What `install --yes-to-all` answers in 1.2.0: the confirmation before
reinstalling specs that are installed already (`--overwrite`;
`require_user_confirmation_for_overwrite` in `lib/spack/spack/cmd/install.py`).

**Finding:** none of the commands the modules run only to read something
takes the option, so the help check of FR-007 can be confined to the commands
that change something, with the same outcome on 1.2.0, at one help call
(about 0.9 s on the local machine) less per query.

## R2. The trust prompt arrived in 1.2.0, with its option

In 1.0.0 and 1.1.0, `lib/spack/spack/util/gpg.py` has no confirmation and
`lib/spack/spack/cmd/gpg.py` and `cmd/buildcache.py` give `gpg trust` and
`buildcache keys` no `yes_to_all`. In 1.2.0, `GPG.trust` asks
`Trust key: <fingerprint> [y/N]` for each key unless `yes_to_all`
(`util/gpg.py`, line 690), and both commands gained `-y, --yes-to-all`
(`cmd/gpg.py` line 28, `cmd/buildcache.py` line 203). The prompt ignores
whether the key is trusted already, which matches the head node's failure.

Tried with the throwaway key `tests/fixtures/throwaway-mirror-key.pub`:

| Spack | `spack gpg trust -y <key>` | `spack gpg trust <key> </dev/null` |
| --- | --- | --- |
| 1.0.0 | `Error: unrecognized arguments: -y`, exit 1 | imported, exit 0, no prompt |
| 1.1.0 | `Error: unrecognized arguments: -y`, exit 1 | "not changed", exit 0, no prompt |
| 1.2.0 | trusted, exit 0 (the integration tests) | reads end-of-file at the prompt |

**Findings:**

1. A Spack without the option is also a Spack without the prompt. On 1.0
   and 1.1, `from_mirrors` works today and would keep working without the
   option.
2. **A defect in the released 0.0.1 and 0.0.2:** `spack_gpg_key` with `key`
   always passes `gpg trust -y`, so it fails on Spack 1.0 and 1.1, which the
   collection says it supports. It went unseen because the integration tests
   run only 1.2.0 and the stand-in `spack` accepts `-y`.

## R3. Reading a command's help safely

- `spack buildcache --help` lists its subcommands under
  `positional arguments:`, after a `SUBCOMMAND` line, four spaces in, one per
  line, with an alias in brackets (`push (create)`); a description can run on
  to indented lines of its own.
- `spack <group> <unknown> --help` prints the group's usage with an error,
  and exits 0 in this shell's pipeline; `spack <unknown> --help` fails with
  "not a recognized Spack command".
- `spack --help` itself has no `--yes-to-all`.
- `--help` is handled by argparse wherever it falls, so a help call made
  with a word that is not a subcommand (a spec, a path, a script for
  `spack python`) could hand `--help` to that command's own arguments, or run
  it. A help call is therefore only ever made for words known to be Spack
  commands: the first word, and each next word only if the previous help
  lists it as a subcommand.

## R4. A mirror that publishes keys, made in a test

Tried with Spack 1.2.0, two keys made by `spack gpg create` in a signing
keyring, zlib installed with `--fake`, and a second, empty keyring to trust
into:

1. `spack buildcache push --key <A> <dir>` writes
   `v3/manifests/key/<A>.key.manifest.json`, but `buildcache keys` finds
   nothing (exit 0, no output) until the key index is written:
   `spack buildcache update-index --keys <mirror>` adds
   `v3/manifests/key/keys.manifest.json`.
2. Then `buildcache keys --install --trust` with stdin closed fails as on the
   head node: `Trust key: <A> [y/N] ==> Error: EOF when reading a line`,
   exit 3. **The failure is reproduced on the local machine.**
3. `buildcache push --force --key <B>` to the same mirror, and the index
   again: the mirror publishes both keys. `--yes-to-all` trusts both, exit 0.
4. Run again with `--yes-to-all`: exit 0, gpg says "not changed", and the
   trusted list is the same (no change, FR-002).
5. Run again without the option, both keys trusted: it asks again and fails,
   exit 3. Spack asks whatever the keyring holds.
6. A mirror must be added to a scope that is read: with
   `SPACK_DISABLE_LOCAL_CONFIG=1`, `spack mirror add` without `--scope` writes
   to Spack's own `etc/spack/mirrors.yaml` (the site scope). The role's
   integration test points the user and system scopes at the test's own
   directories; the module test does the same for this part.

(While trying this, a mirror was written to `.tmp/spack/etc/spack/mirrors.yaml`
by item 6; the file had not existed before, and was removed.)

## R5. Where the check goes, and what it costs

- **Decision:** one method in `plugins/module_utils/spack.py`, on the `Spack`
  class, which every module already uses: it takes a command's arguments and
  gives them back with `--yes-to-all` after the command's words when the flag
  (or the module's own consent) asks for it and the help lists it. Each help
  is read once per run of a module.
  **Rationale:** one place to test; the modules stay as they are apart from
  marking the commands that change something.
  **Alternatives considered:** a list of commands built into the collection
  (rejected by the operator, Clarifications); answering on stdin (rejected,
  answer 1); every call through the check, queries too (the same outcome on
  1.2.0, R1, at about 0.9 s a query).
- **Decision:** a module's own commands name how many of their words are the
  command (`gpg trust` is two), so one help is read. For `spack_command`,
  whose arguments are a site's, the words are found by walking the help
  (R3): the first word, then each next word while the previous help lists it
  as a subcommand, stopping at the first option. A command written with an
  option before its subcommand (`config --scope user add …`, the only order
  `config` accepts: `--scope` is the parent's option) is therefore checked as
  `config`, which has no `--yes-to-all`. Skipping such options would mean
  knowing which take a value. Of the groups tried, only `config` puts an
  option before its subcommand (`repo add --scope site …` takes it after),
  and none of `config`'s subcommands has the option in 1.0 to 1.2, so the
  limit is documented rather than worked around.
  **Rationale:** `--help` is never passed after a word that might be a
  command's own argument (R3).
- **Decision:** a help call that fails (an unknown command) counts as "does
  not take it"; the command itself is then run and fails as Spack does.
- **Decision:** the stand-in `spack` answers `--help` from texts kept in the
  unit tests, as Spack 1.2.0 prints them, and can be told to behave as 1.0 and
  1.1 (no `--yes-to-all` in the help of `gpg trust` and `buildcache keys`,
  and `unrecognized arguments: -y` when given it).

## R6. The fixed module against the real Spack 1.0.0 and 1.1.0 (T016, SC-004)

Tried 2026-11-24, by hand, with the module as fixed for User Story 1, the
clones of R2, a user and system scope and a keyring of the check's own, and
R4's mirror (two published keys, its key index written):

| Step | 1.0.0 | 1.1.0 |
| --- | --- | --- |
| `spack_gpg_key` `key:` the throwaway key | fails: `spack gpg list --trusted --fmt colons`: `unrecognized arguments: --fmt colons` | the same |
| `spack_mirror` in scope `user` | fails: `spack config --scope user get --json mirrors`: `unrecognized arguments: --json` | fails: `argument --scope: invalid choice: 'user'` (the scope's directory does not exist yet, worded otherwise than 1.2's "must refer to an existing scope", which the shared code expects) |
| `spack_gpg_key` `from_mirrors: true` | fails: `gpg list --fmt colons`, as above | the same |

`spack gpg list --help` in both: `usage: spack gpg list [-h] [--trusted] [--signing]`
(no `--fmt`); `spack config get --help` in 1.0.0:
`usage: spack config get [-h] [section]` (no `--json`).

**Findings:**

1. The fix of FR-008 is right, but not enough: before `gpg trust` is reached,
   `spack_gpg_key` reads the trusted keys with `gpg list --fmt colons`, which
   neither 1.0 nor 1.1 has. So SC-004 cannot be met by this spec as written.
2. More broadly, **the collection does not work with Spack 1.0 or 1.1**,
   which it says it supports (`MINIMUM_VERSION = (1, 0)` in
   `plugins/module_utils/spack.py`; the constitution's Principle III and
   Technical Constraints). At least `spack_gpg_key`, `spack_mirror` and,
   on 1.0, everything that reads configuration with `config get --json`
   (`spack_config`, `spack_command` with `changes: config`) fail there. Only
   1.2.0 has ever been tested.
3. This is for the operator to decide (Principle V); it is outside what
   this spec was asked to fix.

## R7. Every option the modules pass, by Spack version (2026-11-25)

Each command the modules run, and each option they give it, looked for in
`spack <command> --help` of the real 1.0.0, 1.1.0 and 1.2.0 (no terminal, as
under Ansible). Only the rows that differ:

| Command | Option | 1.0.0 | 1.1.0 | 1.2.0 | Used for |
| --- | --- | --- | --- | --- | --- |
| `config get` | `--json` | no | yes | yes | reading configuration (`spack_config`, `spack_mirror`, `spack_command` `changes: config`, `spack_env`'s modules config) |
| `gpg list` | `--fmt` (`colons`) | no | no | yes | reading the trusted keys (`spack_gpg_key`) |
| `gpg trust` | `-y, --yes-to-all` | no | no | yes | answering the trust question (R2) |
| `buildcache keys` | `-y, --yes-to-all` | no | no | yes | the same |

Every other option is in all three: `buildcache check -m -o`;
`buildcache push --unsigned --key --only --force --update-index`;
`buildcache keys --install --trust`; `compiler find --scope`;
`external find --scope --not-buildable --exclude -p`;
`concretize --force -q --fresh`; `module tcl|lmod refresh -y --delete-tree`;
`find --json`; `config --scope`; `config add -f`; `config remove`;
`gpg list --trusted`; `location -r`;
`mirror add --scope --type --signed --unsigned`; `mirror remove --scope`;
`mirror list`; `spack -e` (1.0.0 lists it only under `spack --help --all`;
`spack -e <env> …` works).

Also seen: for a scope whose directory does not exist, 1.0.0 prints
`config --scope user get mirrors` as `mirrors: {}` and exits 0; 1.1.0 fails
with `invalid choice: 'user'`; 1.2.0 fails with `must refer to an existing
scope`.

**What this does not cover:** what the commands print and do. The modules
read `find --json`'s records, `buildcache check -o`'s report, the messages
of `buildcache push`, `mirror list`'s lines, `spack.lock`, the stamp in
module files, what `config add` and `config remove` leave behind, and what
detection writes. None of that is in a help text; only running the modules
against 1.0.0 and 1.1.0 (FR-010) will show it.

## R8. The integration tests against the real 1.0.0 and 1.1.0 (2026-11-25)

`just integration`, every test once per version. 1.2.0 passed throughout.

**Run 1, before any fix** (7 failed, 5 passed):

| Version | Where it stopped | What Spack said |
| --- | --- | --- |
| 1.0.0 | `spack_env`, reading the modules configuration | `config get --json modules`: `unrecognized arguments: --json` |
| 1.0.0 | the role's `config` step | `config --scope user get --json config`: the same |
| 1.0.0, 1.1.0 | the tests' own signing-key helper | `gpg list --signing --fmt colons`: exit 1 (no `--fmt`) |
| 1.1.0 | the role's `config` step | `argument --scope: invalid choice: 'user'` |
| 1.1.0 | (passed) `spack_env` and `spack_buildcache_push` | concretize, install, module refresh, push, check, force: as on 1.2.0 |

**Run 2, with the table and its fallbacks**:

| Version | Where it stopped | What Spack said |
| --- | --- | --- |
| 1.0.0 | every read through `spack python -c` | `SyntaxError: multiple statements found while compiling a single statement`: `-c` takes one line; the code is now one line, joined with `;` |
| 1.1.0 | writing to the user scope (`config --scope user add`, `mirror add --scope user`) | `invalid choice: 'user'`, as for reading |

Why 1.1 refuses a scope it has no directory for: in 1.1.0 and 1.2.0 alike,
`etc/spack/include.yaml` declares the user scope (`~/.spack`, or
`SPACK_USER_CONFIG_PATH`) and the system scope (`/etc/spack`, or
`SPACK_SYSTEM_CONFIG_PATH`) as `optional: true` includes. Spack 1.1 leaves an
optional include whose directory does not exist out of its scopes
altogether: `spack config scopes -p` does not list `user`, and no command
can write to it. Spack 1.2 keeps the scope, empty, and makes the directory
on the first write. With the directory made by hand, 1.1 writes to it
(`config --scope user add config:build_jobs:2` wrote `config.yaml`).
On a real machine the user scope's directory usually exists, since Spack's
cache is there by default too; `/etc/spack` usually does not.

For run 3 the tests make the user scope's directory first on 1.1 only,
provisionally, until the operator decides what the modules do there.

**Run 3**, with the one-line code, and the user scope's directory made first
on 1.1 only: **12 passed** (every test on 1.0.0, 1.1.0 and 1.2.0; 35
minutes). So, with the table of plan.md, the one difference left is 1.1's
missing scope, for writing. Spack 1.0.0 reads a missing user scope as empty
and writes to it, making its directory, as 1.2.0 does.

## Decisions

- **Answer 1 replaced (operator, 2026-11-24, during planning):**
  `buildcache keys` and `gpg trust` get `--yes-to-all` where the help lists
  it and run without it where it does not, whatever `yes_to_all` says. The
  `gpg trust -y` defect (R2, finding 2) is fixed in this spec (FR-008).
  Recorded in the spec's Clarifications.
- **The release is 0.0.3** (operator, 2026-11-24), not 0.1.0, so that the
  Cloud-Sandbox's `<0.1.0` pin takes it (FR-006). When to release is still
  the operator's word.
