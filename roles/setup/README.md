# infrastructurebuilder.csis_spack.setup

Makes a Spack ready to build, from one piece of configuration: a list of
steps, carried out in the order written.

The role has no step of its own and knows nothing about any site. Its
defaults are an empty list, the name `spack`, and the scope `site`. Spack
may be on the node already, or the list's first step may install it (a
`spack` step). What a
site wants done to its Spack (which settings, which compilers, which
mirrors, in which order) is entirely in the list, which is that site's
shell script written as data. Each step is carried out by one of the
collection's modules, so each can tell whether it changed anything.

## Variables

| Variable | Default | What it is |
| --- | --- | --- |
| `spack_setup` | `[]` | The steps |
| `spack_setup_executable` | `spack` | The Spack executable, as a path or a name looked up on `PATH`. Not needed with a `spack` step; see below |
| `spack_setup_scope` | `site` | The configuration scope of a step that does not name one |
| `spack_setup_yes_to_all` | `false` | Whether every step answers Spack's confirmations; see below |

Before 0.0.1, in the development versions this repository tagged and later
withdrew, `spack_setup_executable` was named `spack_setup_spack`. The old
name still works: a playbook that sets `spack_setup_spack`, and does
not set `spack_setup_executable`, runs the executable it names. A playbook
that sets both runs `spack_setup_executable`. New playbooks should use the new
name.

## A step

A mapping with a `kind`, that kind's options, and optionally:

- `label`: a name for the step in the output. Without one, the role makes
  one from the kind and its main option.
- `environment`: what the step's Spack command runs in. Either the name of
  an environment that an earlier `environment` step captured, or a mapping
  of variables.
- `yes_to_all` (every kind but `environment`): whether this step answers
  Spack's confirmations; it overrides `spack_setup_yes_to_all`.

### Answering Spack's confirmations: `yes_to_all`

Some Spack commands ask before they act, `[y/N]`: `spack gc` and
`spack uninstall` before removing anything, `spack install` before
reinstalling what is installed already. Ansible gives Spack no terminal to
answer from, so such a question fails the step.

With `yes_to_all` true, for the whole role (`spack_setup_yes_to_all`) or for
one step, each Spack command a step runs to change something is given
`--yes-to-all` where the help of the Spack on the node lists that option
for it, which answers **"yes" to every confirmation** that command asks,
including the ones before removing or overwriting something. Turn it on
for the steps that need it, not out of habit. The help is read only when
it is on, once for each command. A command that already has `-y` or
`--yes-to-all` is run as written.

A `command` step's command is read from the leading words of `args`, up to
the first option: a subcommand written after an option of its parent, as
in `config --scope user add`, is not seen, and the parent's help decides.

`gpg_key` steps answer Spack's question before trusting a key in any case:
asking for the key, or for the keys the mirrors publish, is the consent.

| `kind` | Module | What it does | Options |
| --- | --- | --- | --- |
| `config` | `spack_config` | Declares settings in a configuration scope. Compared with what is there; a list is set exactly | `settings` (required), `state`, `mode`, `scope`, `yes_to_all` |
| `mirror` | `spack_mirror` | Declares one mirror. A different one of the same name is replaced | `name` (required), `url`, `type`, `signed`, `state`, `scope`, `yes_to_all` |
| `gpg_key` | `spack_gpg_key` | Trusts a public key from a file or URL, or the keys the mirrors publish | `key`, `fingerprint`, `from_mirrors`, `yes_to_all` |
| `detect` | `spack_detect` | Has Spack look for compilers and installed packages. Discovery: it depends on the machine and on the step's environment | `compilers`, `externals`, `not_buildable`, `exclude`, `paths`, `require`, `scope`, `yes_to_all` |
| `command` | `spack_command` | Runs any Spack command, for what the kinds above do not cover, with a stated way to tell a change | `args` and `changes` (required), `creates`, `sections`, `scope`, `env`, `yes_to_all` |
| `environment` | `shell_environment` | Runs shell lines of yours and keeps the environment they produce under a name, for later steps. The only shell the role runs | `name` and `shell` (required), `executable` |
| `spack` | `spack_checkout` | Installs Spack at a path at a version, by a shallow git clone; leaves a Spack already there at that version alone; with `move`, moves one at another version. Only as the first step | `version` and `path` (required), `source`, `move` |

On Spack 1.1, a step cannot write to a configuration scope whose directory
does not exist yet: the user scope (`~/.spack`) or the system scope
(`/etc/spack`). Spack 1.1 leaves such a scope out; the step fails and says
which directory to make. Spack 1.0 and 1.2 make it on the first write.

### Installing Spack: the `spack` step

A list may begin with a `spack` step, which installs Spack where a node
has none:

```yaml
spack_setup:
  - kind: spack
    version: v1.2.0          # a tag, a branch, or a commit's full 40-digit hash
    path: /opt/spack         # absolute
    # source: https://git.example.org/mirrors/spack.git   (default: Spack's own, on GitHub)
  - kind: config             # runs /opt/spack/bin/spack
    settings:
      config:
        build_jobs: 8
```

- **Only as the first step**, and only one. Every step after it runs the
  Spack it installs, `<path>/bin/spack`, so `spack_setup_executable` is not
  needed. Set to anything but `spack` or exactly `<path>/bin/spack`,
  including through its old name `spack_setup_spack`, it makes the role
  refuse the list before any step runs.
- **What is at `path` decides what it does.** Nothing there, or an empty
  directory: Spack is cloned there (beside it and moved into place, or into
  the empty directory in place, keeping its ownership and mode), and the step
  reports a change. A Spack at the version named, however it got there: left
  alone, no change, and no network needed. Its own files edited: left alone
  too, with a warning naming them. A Spack at another version: the step
  fails, naming what it found and what was asked for, and nothing is
  changed, unless the step has `move: true` (below). Anything else
  (a file, a directory that is not a Spack): the step fails, nothing
  changed.
- **Moving it to another version: `move: true`.** Off by default. With it,
  a Spack at the path at another version is moved to the version named, in
  place, forward or back, to a tag, a branch or a commit, and the step reports
  a change, with `moved_from` naming what was there. The new version is
  cloned beside the path first (`.<name>.move-*`) and its `spack --version`
  checked; only then is it fetched into the path and checked out, and the
  Spack's `origin` set to the source named. Everything the site added is
  kept: its configuration in `etc/spack/`, the packages built under `opt/`,
  its environments. The move is refused, with nothing changed and the files
  named, when Spack's own files have been edited, or when the new version
  has a file where the site added one, or a directory where the site has a
  file (Spack 1.2 has `etc/spack/site/README.md`, which Spack 1.0 leaves to
  the site; move yours aside and run again). Nothing the old version built is
  rebuilt or removed: environments may need to be concretized and installed
  again, by steps of your own after this one. The steps after a move run the
  new version. In check mode the move is reported, but no source is
  contacted, so a missing version or a file in the way is found only when the
  move is made. `.git` keeps both versions' objects. A move killed part-way
  can leave the hidden `.<name>.move-*` directory, which later runs ignore
  and you may delete.
- **A commit is given by its full hash.** Any 7 to 39 hexadecimal digits are
  taken for a short hash and refused, as git cannot fetch by one; a tag or
  branch so named is refused too.
- **The node needs `git` 2.18 or later.** The step installs nothing else
  Spack needs.
- **`source`** may be any address git accepts. It is trusted as given. One
  holding a user name or password (`https://token@host/...`) is refused, so
  the credential is not shown or kept; use a git credential helper or an SSH
  key. A proxy or a certificate goes in the step's `environment`, which here
  must be a mapping (no step comes before it to capture one by name); every
  variable in it is set for `git`.
- **Spack's package recipes** are fetched by Spack the first time a step
  needs them, not by this step. A site without the network sets a recipe
  repository of its own with a `config` step.
- **In check mode** on a node with no Spack, the `spack` step reports that it
  would install, and the steps after it are not carried out (there is no
  Spack yet to preview them with): each is recorded with `previewed: false`
  and the reason.
- A run stopped during an install can leave a hidden directory
  `.<name>.install-*` beside `path`; later runs ignore it, and it may be
  deleted. Two plays installing to the same path at once are not supported.

`ansible-doc infrastructurebuilder.csis_spack.<module>` describes each
option. The role passes a step's options to the module as they are, and
leaves out what the step leaves out.

```yaml
- hosts: build_hosts
  roles:
    - role: infrastructurebuilder.csis_spack.setup
      vars:
        spack_setup_executable: /opt/spack/bin/spack
        spack_setup:
          - kind: config
            settings:
              config:
                build_jobs: 8
          - kind: environment
            name: mycompiler
            shell: . /opt/mycompiler/12/setvars.sh
          - kind: detect
            compilers: true
            environment: mycompiler
            require: [mycompiler@12]
          - kind: mirror
            name: site-cache
            url: https://cache.example.org/spack
            type: [binary]
          - kind: gpg_key
            from_mirrors: true
          # Spack asks before removing anything; this step answers "yes".
          - kind: command
            args: [gc]
            changes: always
            yes_to_all: true
```

## What it does with the list

1. **Checks all of it first.** An unknown kind, an option that belongs to
   another kind, a missing required option, or an environment named before
   it is captured stops the role with every problem and its step's number,
   and nothing has been changed. (Values are checked by each module when
   its step runs.)
2. **Carries out each step in the order written.** A step that fails stops
   the rest.
3. **Leaves `spack_setup_results`:** one entry per step, with its number,
   kind, label, whether it changed, and the module's result.

Where a site has to do something of its own between two parts, such as
install a compiler, it applies the role twice with two lists. The role
keeps nothing between applications.

## Declared and discovered

A `config`, `mirror` or `gpg_key` step declares a state. It is compared
with what Spack has, changes only what differs, and is previewed exactly in
check mode.

A `detect` step asks Spack to look. What it finds depends on the machine
and on the environment it runs in, so it cannot be previewed: in check mode
it does nothing and says so. Spack says nothing when it finds nothing, so
give `require` whatever must be there afterwards; a step run without the
environment it needed then fails instead of passing quietly. Detection only
ever adds.

A `command` step is whatever you say it is. It reports a change by the
rule you give in `changes`, and in check mode it is not run.

## Examples

The collection's `docs/examples/` holds complete lists for a system
compiler, a compiler behind environment modules, a compiler built by Spack,
a toolset beside the system's compiler, unwanted compilers, a site mirror
with its key, Spack installed by the role's first step, and one real
site's two scripts. Each is applied by the
collection's tests.
