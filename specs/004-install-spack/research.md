# Research: A `setup` step that installs Spack

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Principle III asks that the behaviour a module relies on is tried first, and
what was found is written down here. Everything below was tried on
2026-11-26 on the operator's local machine, with git 2.50.1, against the
local clones of the real Spack that the integration tests already keep
(`.tmp/spack` at v1.2.0, `.tmp/spack-v1.0.0`, `.tmp/spack-v1.1.0`; each made
by `git clone --depth 1 --branch <tag>`, so each is shallow and holds one
tag). The sources were given as `file://` addresses, which take git's
network code path, not its local shortcut.

## R1. How Spack installs, by its own account

Spack's getting-started documentation (`lib/spack/docs/getting_started.rst`
in the v1.2.0 checkout) installs it with one command, a shallow `git clone`:
`git clone --depth=2 https://github.com/spack/spack.git`, which takes the
default branch, `develop`. There is no build step and no installer: the
checkout is the installation, and `bin/spack` in it is the executable
(sourcing `share/spack/setup-env.sh` is for a person's shell, not needed to
run `bin/spack`).

**Decision:** the step does what the documentation does, a shallow clone,
but of the version the site names (FR-002), not of whatever the default
branch is that day. Nothing else is run to install Spack.

## R2. Which form of `git` fetches which kind of version

| What was named | `git clone --depth 1 --branch <v>` | `git init` + `git fetch --depth 1 <source> <v>` + `git checkout FETCH_HEAD` |
| --- | --- | --- |
| A tag (`v1.2.0`) | Works; HEAD detached at the tag, and the tag is there locally | Works |
| A branch (`releases/v1.2`) | Works; HEAD is that branch, checked out | Works, but HEAD is detached and the branch's name is lost |
| A full commit (40 hex digits) | Fails: "Remote branch … not found in upstream origin" | Works |
| A short commit (`63962ed9`) | Fails | Fails: "couldn't find remote ref 63962ed9" |
| A version that does not exist (`v9.9.9`) | Fails: "Remote branch v9.9.9 not found"; **no directory is left behind** | Fails |

GitHub serves a fetch of a full commit's hash: `git fetch --depth 1
https://github.com/spack/spack.git 63962ed9…` (v1.2.0's commit, written in
full) took 2.3 seconds and 5.7 MB, so the second form works against Spack's
public repository as it does against a local one. (One release of Spack is
that small because the package recipes are no longer in it.)

**Decision:** a tag or a branch is installed with `git clone --depth 1
--branch <v>`, exactly as a person following the documentation would; a
full commit hash with `git init`, `git fetch --depth 1 <source> <hash>` and
`git checkout --detach FETCH_HEAD`. A short hash is refused before anything
is fetched, with a message asking for the full one: git cannot fetch it
without the whole history, which for Spack is far larger than one release.

## R3. Telling, offline, whether the Spack there is at the version named

Every form above leaves something that a later run can read without the
network:

- After a tag: HEAD is detached, and `refs/tags/<v>` exists and points at
  HEAD's commit.
- After a branch: `git symbolic-ref --short HEAD` prints the branch's name.
- After a commit: `git rev-parse HEAD` is that hash.

A Spack installed by hand from the documentation's command is on the branch
`develop`, the second case; one installed with `--branch <tag>`, as the
integration tests' clones were, is the first. Both are recognised the same
way as the step's own (spec, US2 AC1).

**Decision:** "at the version named" means: for a full hash, HEAD is that
commit; otherwise HEAD is on a branch of that name, or HEAD is the commit of
a local tag of that name. Anything else is another version. A branch is at
its version as long as it is checked out, however far Spack's branch has
moved since: the step never fetches to find out (moving a Spack is spec
005's), so a repeat run needs no network and reports no change.

## R4. Telling a Spack from something else

- `git -C <dir> rev-parse --show-toplevel` prints the top of the repository
  a directory is in, which for a directory inside another repository is that
  other repository (tried with a subdirectory of a clone).
- A Spack checkout has `bin/spack`.

**Decision:** a destination holds a Spack when it is the top of a git
repository and has `bin/spack`. A destination that exists, is not empty, and
is not that, is "not a Spack" (FR-010).

## R5. What `spack --version` says, and what running it leaves

| Checkout | `bin/spack --version` |
| --- | --- |
| v1.0.0 | `1.0.0 (73eaea13f381e3495299284856fd02a64e1d154c)` |
| v1.1.0 | `1.1.0 (0c2be44e4ece21eb091ad5de4c97716b7c6d4c87)` |
| v1.2.0 | `1.2.0 (63962ed90680d339004305075da272ae93c04a41)` |

The first word is Spack's version; a checkout of a development branch says
so in it (`1.3.0.dev0`). The first run took about 3 seconds (Python compiles
Spack's modules), later runs about 1. Running it leaves `git status` clean:
what Spack writes is ignored by its own `.gitignore`. It needs no network
and no package recipes.

**Decision:** after an install, and on every run, the step runs
`<destination>/bin/spack --version` and reads the major and minor numbers
from its first word. Below 1.0, or unreadable, fails (FR-006). The stand-in
`spack` already answers `--version` the same way
(`tests/unit/fake_spack.py`), so the unit tests can play any version.

## R6. A failed or stopped install

- A `git clone` that fails removes the directory it was making (R2's last
  row). A clone that is killed part-way does not.
- `git clone` into a directory that exists and is empty works.
- On the same filesystem, renaming a directory into place is atomic.

**Decision:**

- **The destination does not exist:** clone into a new temporary directory
  beside it (in the same parent, so on the same filesystem), check the
  version there, then rename it to the destination. A stopped run leaves at
  most a hidden temporary directory, named for the destination, never a
  destination that a later run would take for a Spack; a version below 1.0
  leaves nothing. The parent is made first if it does not exist.
- **The destination exists and is empty** (a site often makes it with the
  ownership it wants, in a parent it cannot write to): clone into it
  directly, which keeps its ownership and mode. If that is stopped part-way,
  the next run finds a directory that is not a Spack and fails, saying so
  and what to remove; the spec allows that ("completes the install or fails
  and says what it found").

## R7. What the later steps need from a new Spack

The integration tests already run `config`, `mirror`, `gpg_key` and
`command` steps against fresh shallow clones like these, so a new Spack
needs nothing more for them. A step that needs package recipes (`detect`
with externals, an environment's concretization) has Spack 1.0 and later
fetch its recipe repository the first time, from the network: the spec
leaves that to Spack (FR-012).

## R8. `git` on the node

`git` is not installed by default on a minimal RHEL 10; it is in AppStream.
Ansible's `module.get_bin_path("git", required=True)` fails with a message
naming the program it could not find.

**Decision:** the module looks `git` up that way, and the step's
documentation says that the node needs it.

## R9. Check mode after an install that has not happened

In check mode a new node has no Spack, so every later step, which runs
`<destination>/bin/spack`, would fail. Ansible's own git module has the same
problem for tasks after it, and its users skip them.

**Decision:** in check mode, when the install step reports that it would
install, the role does not carry out the later steps: each is recorded as
not previewed, with the reason, and the role reports success. This keeps
SC-003 (one change, the destination absent) true for a whole list, not just
for the step. The plan records this as a design decision beyond the spec's
words.

## R10. The oldest `git` the step accepts (2026-11-26, from the checklist)

Every command the step runs exists in git 2.18: `clone --depth --branch`
(1.7.10), `symbolic-ref --short` (1.7.10), `checkout --detach` (1.7.5),
`rev-parse --show-toplevel` and `status --porcelain` (1.7). 2.18 is the git
of RHEL 8, the oldest RHEL a managed node is likely to run. The tests run
only the local machine's git (2.50.1); no older git was tried.

**Decision:** the step reads `git --version` first and refuses below 2.18,
naming both versions. The floor is a documented choice, not a measured one.

## R11. A credential in the source's address (2026-11-26, from the checklist)

An address such as `https://token@host/spack.git` would be printed in the
task's arguments, returned in the step's result, and written by `git clone`
into `<path>/.git/config` as `origin`, where every user who can read the
Spack can read it.

**Decision:** an `http://` or `https://` source with a user name or password
in it is refused before anything runs. The documentation sends a site to a
credential helper or an SSH key, which keep the secret out of the address.
(An `ssh://` or `user@host:path` address names a user, which is not a
secret, and is accepted.)

## Decisions

| # | Decision | Alternatives considered |
| --- | --- | --- |
| 1 | A new module carries the step out, as every other kind has one | Ansible's own `ansible.builtin.git`: it moves a checkout at another version to the version named (spec 005's behaviour, which 004 refuses), or with `update: false` reports no change over another version; either way it needs tasks around it to meet FR-005 to FR-010 |
| 2 | Tags and branches by `git clone --depth 1 --branch`; full hashes by init and fetch | One form for all (init and fetch): it loses a branch's name, so a hand-installed branch would not be recognised |
| 3 | A short hash is refused | A full clone to find it: hundreds of megabytes for one commit |
| 4 | "At the version" is read offline (R3) | Asking the source each run: needs the network on every run, and reports a change when a branch moves |
| 5 | Clone beside the destination and rename; clone in place only into an empty directory | Always in place: a stopped run leaves a partial Spack; always beside: loses the ownership of a directory a site made |
| 6 | Check mode does not contact the source | Asking the source in check mode (`git ls-remote`) to find a wrong version early: a preview that needs the network, and that still cannot check a commit |
| 7 | Later steps are not previewed in check mode when Spack is not installed yet (R9) | Letting them fail: check mode on a new node would always fail |
