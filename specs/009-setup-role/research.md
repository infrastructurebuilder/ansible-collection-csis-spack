# Research: Set Spack up from one piece of configuration

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

What the modules rely on was read from Spack v1.2.0's `--help` and tried
against the real Spack v1.2.0 before the modules were written, on
2026-11-14: on the operator's local machine, and, for oneAPI, in the Cloud
Sandbox's test container (AlmaLinux 10, oneAPI 2024.2.1 installed from dnf,
Spack v1.2.0), which was kept after a run and removed afterwards. The
practice became Principle III when the constitution was ratified on
2026-11-17.

Before anything was written, the plan named four things to find out:
exactly when `compiler find` removes a compiler it no longer sees, and from
which scope (R16); whether `config add -f` and `config get --json`
round-trip lists and booleans unchanged, and what `mode: replace` must do to
remove a key (R7 to R9); what `gpg list --trusted` prints, to read
fingerprints from (R13, R14); and whether `external find` detects an
installed oneAPI's MKL and MPI (R18). If it did, the sandbox's example would
get shorter; the collection would be the same either way.

Some findings were later found incomplete or were extended for other Spack
versions; a **Later** line under a finding says where.

## What Spack v1.2.0 offers (read from its `--help`, and tried)

## R1. Reading configuration

`spack config --scope <scope> get --json <section>` prints one section of
one scope as JSON (tried: `{"mirrors":{}}` for an empty site scope). Without
`--scope` it prints the merged result of every scope.

**Decision:** this is how every module reads configuration
(`Configuration.get` in `plugins/module_utils/spack.py`). It replaces the
sandbox's `spack python -c`, which reached into Spack's internals.

**Later**, spec 003 (its research, R7): Spack 1.0 has no `--json` on
`config get`; there the modules read the configuration through
`spack python -c`, one line, as the version table `BEHAVIOUR` says.

## R2. Writing configuration

`spack config --scope <scope> add <path>` and `spack config --scope <scope>
add -f <file>` add to a scope; `spack config --scope <scope> remove <path>`
removes a path.

**Decision:** `spack_config` adds through a file (`add -f`), so that a whole
mapping goes in one call, and removes with `config remove`. It never writes
Spack's YAML files itself.

## R3. Detection

- `spack compiler find [--scope S] [paths...]`, `spack compiler list`,
  `spack compiler remove`. Since Spack 1.0 a compiler is a package, recorded
  under `packages:` as an external.
- `spack external find [--not-buildable] [--exclude E] [-p PATH]
  [--scope S] [--all] [packages...]`.

**Decision:** `spack_detect` runs `compiler find` and `external find` with
those options, and tells a change from the scope's `packages` section, where
both record what they find.

## R4. Mirrors

`spack mirror add [--scope S] [--type binary|source] [--unsigned |
--signed] <name> <url>`, `mirror set`, `mirror remove`, `mirror list`.

**Decision:** `spack_mirror` reads the mirrors from the scope's `mirrors`
section (R1), adds a missing mirror with `mirror add`, and removes one with
`mirror remove`. The plan said a different mirror would be corrected with
`mirror set`. As built, it is removed and added again (`replaced`); the
plan does not record why. Adding a name that exists fails (R12), so the
removal comes first.

## R5. Keys

`spack gpg trust <keyfile>`; `spack gpg list [--trusted] [--fmt ...]`;
`spack buildcache keys --install --trust`.

**Decision:** `spack_gpg_key` trusts a key file with `gpg trust`, the
mirrors' keys with `buildcache keys --install --trust`, and reads what is
trusted with `gpg list --trusted --fmt colons` (R13, R14).

## R6. Scopes

Spack's configuration scopes, lowest to highest: `defaults`, `system`
(`/etc/spack`), `site` (inside Spack's own tree), `user` (`~/.spack`), an
environment, the command line.

**Decision:** each module that reads or writes configuration takes a
`scope`, default `site`, the scope the sandbox's shell used for nearly
everything; the role's `spack_setup_scope` is the default for a step that
names none.

## Tried against Spack v1.2.0 first: configuration

## R7. One section per file

`spack config add -f <file>` takes **one section per file**; a file with two
sections is refused. JSON is accepted.

**Decision:** `spack_config` writes one temporary JSON file per section and
adds each in its own call.

The plan also asked whether lists and booleans round-trip unchanged. No
separate finding was recorded; the integration test
(`tests/integration/test_real_setup.py`) reads back, through the real
Spack, a list of providers and `buildable: false` exactly as they were set.

## R8. `config add` merges lists

`config add` **merges a list** into the one that is there, new items in
front and none twice: adding `mpi: [mpich]` to `mpi: [intel-oneapi-mpi]`
gives both. A scalar is replaced.

**Decision:** a list can only be set exactly by removing its path first,
and that is what `spack_config` does: for every path whose value differs it
removes the path, then adds the value. `mode: replace` uses the same means
a key of a section at a time: a key that is not given, or differs, is
removed, and the given ones are added.

## R9. `config remove`

`spack config remove` of a path that is not there succeeds. Removing the
last key of a mapping was recorded as removing the mapping too.

**Decision:** `state: absent` removes each path named that the scope has,
and nothing else.

**Later**, 0.3.1 ([spec 011](../011-preview-long-builds/spec.md)): the
second half was wrong. The Cloud Sandbox's stage 12 found that Spack v1.2.0
leaves an emptied mapping behind, empty (`install_tree: {}`), at every
level. Since 0.3.1 a removal that would empty a mapping removes the highest
mapping it would empty instead (`highest_emptied` in
`plugins/module_utils/spack.py`), and the stand-in `spack` leaves emptied
mappings behind as the real one does. `CHANGELOG.md` records it under 0.0.1.

## R10. Spack's schema

Spack checks what is added against its schema and refuses a wrong type.

**Decision:** if that happens after the module removed a path to make room
(R8), the module puts back what it removed, so a refused value leaves the
scope as it was; then it fails with Spack's message. After every write it
also reads the section back and fails if it is not what was intended.

## R11. A scope with no directory

`spack config --scope user get` **fails while the scope's directory does
not exist** ("must refer to an existing scope"), which is the state of the
user scope on a fresh machine. Found by the integration test, not by hand.

**Decision:** the module reads that failure as an empty scope; writing to
the scope makes it.

**Later**, spec 003 (its research, R7 and R8): Spack 1.1 says `invalid
choice` for such a scope and cannot write to it at all; the module reads it
as empty and, on a write, fails saying which directory to make. Spack 1.0
reads it as empty and makes it on the first write.

## Tried against Spack v1.2.0 first: mirrors and keys

## R12. How a mirror is recorded

A mirror added with no flags is kept as a bare URL; one added with flags, as
a mapping. `--type binary --type source` gives both. Adding a name that
exists fails.

**Decision:** the module reads a bare URL as `{url: ...}`, takes a property
Spack does not record at its default (a mirror holds both binary and
source), compares only the properties the step gives, and removes a mirror
before adding it again (R4).

## R13. `gpg trust`

`spack gpg trust` asks a question unless given `-y`. Its exit code says
little: it is 0 for a file that holds no key.

**Decision:** whether a key is trusted is read from
`spack gpg list --trusted --fmt colons` before and after, not from what
`gpg trust` prints or how it exits. The key file's own fingerprint is read
with `gpg --show-keys --with-colons` where the node has a `gpg`; a file with
no key in it, or with another key than `fingerprint` names, is refused. In
0.3.0 a key file was trusted with `gpg trust -y`.

**Later**, spec 003 (its research, R2): the question arrived in Spack 1.2.0
together with its option, and `buildcache keys --trust` asks it too, for
each key a mirror publishes, which made `from_mirrors` fail on Spack 1.2
against a mirror that publishes a key. Spack 1.0 and 1.1 never ask, and
refuse `-y`. Since 0.0.3 both trusts are given `--yes-to-all` on Spack 1.2
and later, and nothing on 1.0 and 1.1.

## R14. `gpg list --fmt keys`

`--fmt keys` runs the fingerprints together with nothing between them.

**Decision:** the fingerprints are read from `--fmt colons`.

**Later**, spec 003: Spack 1.0 and 1.1 have no `--fmt`; there the
fingerprints are read from gpg's own listing.

## R15. gpg's agent socket

gpg's agent needs a short path for its socket; a keyring deep in a
temporary directory makes `gpg trust` fail after importing.

**Decision:** the integration tests make their keyring with
`tempfile.mkdtemp(prefix="csis-gpg-")`, not under pytest's `tmp_path`, and
stop its agent afterwards.

## Tried first: detection, with the real oneAPI

## R16. Detection never removes

**`spack compiler find` and `spack external find` never remove anything.**
Run without the Intel modules they find no Intel compiler and leave the
ones already registered alone. The first plan's "the two `compiler find`
steps undo each other", taken from the sandbox's own notes, was not
reproduced with Spack v1.2.0. What is true is the quiet half: without the
environment nothing is found and nothing is said.

**Decision:** `require` is what catches it: a detection that ran without its
environment fails, naming what is not registered. The stand-in `spack`
detects only what its "machine" shows in the environment it runs in, and
only ever adds, so the accident is reproduced and caught in the unit tests.

## R17. `packages.yaml` is written back in another order

Each detection writes `packages.yaml` back **in another order**, so the
file's bytes change while its data does not.

**Decision:** `spack_detect` compares the `packages` section as data, read
before and after through `config get --json`; a reorder is not a change.

## R18. `external find` and a dnf-installed oneAPI

`spack external find` does **not** detect a dnf-installed oneAPI's MKL or
MPI, by name or with `--all`.

**Decision:** the sandbox's example keeps those two externals declared, in a
`config` step, with the providers that use them.

## R19. `compiler remove` leaves an `id`

`spack compiler remove` puts an `id` on the compilers it leaves behind.

**Decision:** nothing in the modules. It explains the one difference the
trial with the real oneAPI found between the role's result and the shell's
(spec, SC-004): an `id` on three compiler entries, which came from a
`spack compiler remove` in the earlier trials (confirmed), not from the
sandbox's shell.

## Tried first: the sandbox's own script

## R20. `config add` without `--scope`

`spack config add` without `--scope` writes to the **user** scope. The
sandbox's two settings (the install tree's padding and the Tcl modules) are
therefore in the login user's `~/.spack`, not in the site scope with
everything else, and no other user has them.

**Decision:** the sandbox's example says `scope: user` for that step, so
that it reproduces the script. Whether the sandbox wants that is the
sandbox's to decide when it adopts the role.

## Tried first: ansible-core

## R21. `meta/argument_specs.yml` and ansible-core 2.16.20

With a `meta/argument_specs.yml`, ansible-core 2.16.20 prints a deprecation
warning of its own on every use of the role: its implicit validation task
uses a form of `action` that the same release deprecates.

**Decision:** the role has no `meta/argument_specs.yml`. Its first task
checks the list with the filter `setup_problems` (an `assert`), and its
README documents the variables.

## Decisions

| # | Decision | Alternatives considered |
| --- | --- | --- |
| 1 | One module per kind of step; the role only calls them | A list of workflows, one per kind of compiler (dropped: it built a site's choices in) |
| 2 | Configuration read with `config get --json`, written with `config add -f` and `config remove` (R1, R2) | `spack python -c` and hashing, as the sandbox did; writing the YAML files |
| 3 | A list or scalar set exactly by removing its path first (R8) | `config add` alone, which merges lists |
| 4 | A change in detection told from `packages` compared as data (R17) | Comparing the file, which changes on every run |
| 5 | Trust told from `gpg list --trusted --fmt colons` before and after (R13, R14) | `gpg trust`'s exit code and output |
| 6 | `require` to catch a detection run without its environment (R16) | Trusting detection to report what it did not find |
| 7 | A different mirror removed and added again (R4, R12) | `mirror set`, as the plan said |
| 8 | No `meta/argument_specs.yml` (R21) | Ansible's own validation, with a warning on every use |
