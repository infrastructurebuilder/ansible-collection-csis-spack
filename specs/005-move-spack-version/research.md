# Research: The install step moves a Spack to another version, when a site asks

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Tried on 2026-11-26 on the operator's local machine, git 2.50.1, against the
local clones of the real Spack (`.tmp/spack-v1.0.0`, `.tmp/spack-v1.1.0`,
`.tmp/spack` at v1.2.0; each shallow, one tag), given as `file://` sources.
Spec 004's research ([../004-install-spack/research.md](../004-install-spack/research.md))
holds what an install does; this is what a move adds.

## R1. A shallow checkout moves to another version in place

A clone made by `git clone --depth 1 --branch v1.0.0` (as spec 004 installs
a tag) was moved to v1.2.0 with:

```sh
git -C <path> fetch --quiet --depth 1 <source> refs/tags/v1.2.0:refs/tags/v1.2.0
git -C <path> checkout --quiet --detach 'v1.2.0^{commit}'
```

`bin/spack --version` then printed `1.2.0 (63962ed…)`, and `git status
--porcelain` was empty. Back to v1.0.0 the same way, from the v1.0.0 clone,
printed `1.0.0 (73eaea1…)`. A branch: `fetch --depth 1 <source>
refs/heads/<b>:refs/remotes/origin/<b>`, then `checkout -B <b>
origin/<b>`, left HEAD on that branch, as spec 004's install of a branch
does. A commit: `fetch --depth 1 <source> <hash>`, then `checkout --detach
FETCH_HEAD`, as 004 installs one. The source may differ from the one the
Spack came from: the fetch names it, and `origin` is left as it was unless
changed.

`.git` keeps both versions' objects (11 MB after v1.0.0 → v1.2.0 → v1.0.0,
against about 6 MB for one), and both tags.

**Decision:** a move fetches the version named, with `--depth 1`, then checks
it out: detached for a tag or a commit, on the branch for a branch, as spec
004 leaves an install. After the move, `origin` is set to the source named,
so that the Spack says where its version came from.

## R2. Git overwrites a site's ignored files without a word

The finding that shapes the design. Spack 1.0's `.gitignore` ignores
`/etc/spack/*` (except `defaults`); Spack 1.2's ignores it too, but tracks
`etc/spack/site/README.md`. On a v1.0.0 checkout with a site's own
`etc/spack/site/README.md` ("MY OWN"), the checkout of v1.2.0 above
succeeded and **replaced the site's file with Spack's**. Git treats ignored
files as expendable. An untracked file that is not ignored stops a checkout
instead ("would be overwritten"), and the site's other files
(`etc/spack/config.yaml`, `opt/spack/…`, a note at the top) were kept.

**Decision:** before anything at the path changes, the move takes the files
the new version tracks and the current one does not, and looks at the path
for each: something already at that place, or a file at one of its parent
directories, is the site's, and the move is refused with nothing changed,
naming them (spec FR-006: every file a site added is kept). This is sized by
Spack's own file list, not by the site's install tree, which `git ls-files
--others` would have to walk (settled by `/speckit-analyze`, P1). It needs
the new version's file list before the move: see R3.

## R3. The new version is staged beside the path first

To know the new version's files, and to check its `spack --version`
(spec: a version below 1.0 is refused "before the Spack there is changed"),
the new version must exist somewhere before the path is touched. A shallow
clone of v1.2.0 into a hidden directory beside the path took 1.3 seconds;
its `git ls-tree -r --name-only HEAD` gave the list; `git -C <path> fetch
--depth 1 file://<staged>` then fetched from the staged copy, so the network
is read once.

**Decision:** a move clones the version named into a hidden directory beside
the path, `.<name>.move-*` (spec 004's install uses `.<name>.install-*`), the
same way 004 installs: then checks its `bin/spack --version`, then compares
its files with the site's at the path (R2), and only then fetches from it
into the path and checks out. The staged copy is removed afterwards, and if
anything fails. A missing version fails at the staging clone, with git's
"not found", and nothing at the path has changed (FR-007).

## R4. Finding a version without fetching it

`git ls-remote <source> refs/tags/v1.2.0 refs/heads/v1.2.0` printed the tag's
commit; for `v9` it printed nothing and exited 0. It changes nothing on the
node. It cannot check a commit, which a server lists only as a ref's target.

**Decision:** check mode does not contact the source, as spec 004's does not:
it reports the move it would make (from what, to what) and says that
whether the version exists and whether it would overwrite a site's file are
found only when the move is made. `ls-remote` is not used; the staging
clone (R3) finds a missing version in a real run. (Alternative weighed: ask
the source in check mode with `ls-remote`, which catches a wrong tag or
branch early but needs the network for a preview, and still cannot check a
commit or the site's files.)

## R5. A move stopped part-way

- Stopped during the staging clone: only the hidden `.<name>.move-*`
  directory is left; the Spack at the path is untouched. Later runs ignore
  it.
- Stopped after the fetch into the path, before the checkout: the path is
  still at the old version, with extra objects in `.git`. The next run with
  the move allowed moves it; without, it fails as spec 004 says.
- Stopped during the checkout, which writes files one by one: the path is
  part old, part new. The next run finds Spack's own files differing from
  HEAD, and refuses (spec FR-005, edited files), saying which. The spec
  allows that: "completes it or fails and says what it found".

## R6. What a site added, and what Spack's `.gitignore` covers

In all three versions `.gitignore` ignores `/opt` (the default install
tree), `/var/spack/{stage,cache,environments}`, `/etc/spack/*` but
`defaults`, the module roots under `/share/spack`, and Python's caches. So a
site's configuration in `etc/spack/`, its built packages under `opt/`, and
its environments are all "added files" in the spec's sense, and a checkout
leaves them where they are, except where R2 bites.

## Decisions

| # | Decision | Alternatives considered |
| --- | --- | --- |
| 1 | The move is a fetch and a checkout in place, as R1 | Install side by side and swap a link: the spec asks for in place (Assumptions) |
| 2 | The new version is staged beside the path, checked, and compared with the site's files before the path changes (R2, R3) | Checking out and hoping: loses a site's ignored file (R2); fetching into the path first: changes `.git` before the checks |
| 3 | A collision with any file git does not track refuses the move | Refusing only for ignored files: an untracked one stops git anyway, but with git's own message; listing both gives one message |
| 4 | `origin` is set to the source named after a move | Leaving it: the Spack would name a source it no longer came from |
| 5 | Check mode contacts no source (R4) | `ls-remote` in check mode |
