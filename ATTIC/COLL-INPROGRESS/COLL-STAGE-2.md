# Collection stage 2: setting Spack up from one piece of configuration

*Status:* planned 2026-11-14, revised the same day at the operator's
request so that the collection prescribes nothing about what is installed
and takes it all as configuration, and executed the same day on "do coll
2", on `feature/coll-stage-2`. Merged into `develop`, released as 0.3.0
and pushed on the operator's word, 2026-11-14. The decisions
are under [Decisions taken](#decisions-taken); what was tried first, and
what it changed, under [Tried against Spack v1.2.0 first](#tried-against-spack-v120-first);
the result under [Outcome](#outcome).

## Why

0.1.0 covers what happens to a Spack *environment*: concretize, install,
module files, push. What comes before that, making a fresh Spack ready
to build anything, is still bash in the Cloud Sandbox's playbooks. In
`sandbox-provisioning` today:

| Where (Cloud-Sandbox, `exportit/sandbox-provisioning/`) | What the shell does | What is fragile about it |
| --- | --- | --- |
| `roles/spack/tasks/main.yml` L92-L119 | `config add` twice; `compiler find --scope site`; `external find --scope site`; `external find --not-buildable cmake`; `mirror add spack-public` unless `mirror list` already names it; `buildcache keys --install --trust` | Change is told by a fingerprint: Spack's whole configuration dumped through `spack python -c` (Spack's internals) plus `spack gpg list`, hashed before and after. A `grep` guards the mirror. No check mode |
| `roles/intel_oneapi/tasks/main.yml`, three tasks | `compiler find` again with the Intel modules loaded; YAML text appended to `etc/spack/site/packages.yaml` unless `grep` finds the package's name; `config --scope site add` five times; `buildcache keys` again | The two `compiler find` steps undo each other when the modules are not loaded. A changed version or prefix is never corrected, because the name is already in the file |
| `sandbox-ops/bin/spack-pubkey.sh` (run by hand) | Download the site mirror's public key, `gpg trust` it, `mirror add s3-mirror`, `buildcache keys` | By hand; "already exists" errors sent to `/dev/null` |

The first plan for this stage answered with modules *and* with a list of
workflows, one per kind of compiler, each with its own order of steps.
That would have put the sandbox's choices (Intel, MKL, `cmake`, which
modules to load) into the collection, and every site with other choices
would have needed the collection changed. This plan does the opposite.

## The principle

**The collection knows how to do each kind of thing to Spack, and nothing
about what any site wants done.** No package, compiler, version, path,
mirror or module name appears in its plugins or in its role's defaults,
which are empty. What a site wants is one piece of configuration, a list
of steps in the order the site wants them, which is to say its shell
script, written as data:

- each step is one of a small number of kinds, and each kind is a module
  that can tell whether anything changed, and, where the answer is
  knowable beforehand, preview it;
- the order is the operator's, because the order is where the site's
  knowledge is (what must be loaded before what is looked for);
- anything a kind does not cover can still be said, as a plain Spack
  command with a stated way of telling whether it changed something, so
  that no line of a script has to stay outside the configuration.

The steps still differ in nature, and the configuration keeps that
visible rather than hiding it:

- **Declared state** (a setting, a mirror, a trusted key): the answer is
  known before anything runs, so it is compared, changed only when
  different, and previewed in check mode.
- **Discovery** (`compiler find`, `external find`): the answer depends on
  the machine and on the environment the command runs in. It cannot be
  previewed, and the operator can say what must have been found.

## What Spack v1.2.0 offers (read from its `--help`, and tried)

- `spack config --scope <scope> get --json <section>` prints one section
  of one scope as JSON (tried: `{"mirrors":{}}` for an empty site scope);
  without `--scope`, the merged result. This is the supported way to
  read configuration; it replaces `spack python -c`.
- `spack config --scope <scope> add <path>` and `add -f <file>`;
  `config remove <path>`.
- `spack compiler find [--scope S] [paths...]`, `compiler list`,
  `compiler remove`. Since Spack 1.0 a compiler is a package, recorded
  under `packages:` as an external.
- `spack external find [--not-buildable] [--exclude E] [-p PATH]
  [--scope S] [--all] [packages...]`.
- `spack mirror add [--scope S] [--type binary|source] [--unsigned |
  --signed] <name> <url>`, `mirror set`, `mirror remove`, `mirror list`.
- `spack gpg trust <keyfile>`, `gpg list [--trusted] [--fmt ...]`,
  `spack buildcache keys --install --trust`.
- Scopes, lowest to highest: `defaults`, `system` (`/etc/spack`), `site`
  (inside Spack's own tree), `user` (`~/.spack`), an environment, the
  command line.

## Items

1. **The kinds of step, each a module** usable on its own in any
   playbook. All take `spack` (the executable) and, where it applies,
   `scope`.

   | Module | What it does, from options alone | Change, and check mode |
   | --- | --- | --- |
   | `spack_config` | `settings`: a mapping in the shape of Spack's configuration (sections at the top). `state: present` puts those values in the scope; `absent` removes the paths named. `mode: merge` (default) leaves every other key of the scope alone; `mode: replace` makes each section named exactly what is given | Compares, as data, with `config get --json`; writes only what differs; lists the paths changed. Check mode lists them and writes nothing |
   | `spack_mirror` | `name`, `url`, `type`, `signed`, `state` | Missing: `mirror add`. Different: `mirror set`. Says which; check mode says which it would |
   | `spack_gpg_key` | `key` (a public key file or URL) with an optional `fingerprint` it must have; or `from_mirrors: true` (`buildcache keys --install --trust`). Public keys only | A fingerprint trusted afterwards that was not before. Check mode: for a key file, whether it is trusted already; for `from_mirrors`, not knowable |
   | `spack_detect` | `compilers: true` (`compiler find`); `externals: true` or a list of names (`external find`); `not_buildable`; `exclude`; `paths`; and `require`: specs that must be registered afterwards, or the task fails naming what is missing | What was added and removed in the scope's `packages`, compared as data before and after. Check mode changes nothing and says that discovery cannot be previewed |
   | `spack_command` | `args`: any Spack command, as a list, for what no other kind covers (`gpg init`, `buildcache update-index`, a fork's own subcommand). `changes`: how to tell that it changed something: `config` (the named scope's sections differ afterwards, read with `config get --json`), `creates` (a path that exists afterwards), `always` or `never` | As `changes` says. Check mode does not run it, and reports it as a possible change unless `creates` exists or `changes: never` |

   Each takes the environment Spack should run in from the task's
   `environment:`, as in 0.1.0; none runs a shell.

   **YOUR DECISION (the plain command):** include `spack_command`
   (default): without it, whatever the other four do not cover goes back
   into shell tasks beside the configuration, and the configuration is no
   longer the whole script; or leave it out, and keep the collection to
   steps it can fully answer for.

2. **The configuration: one variable, `spack_setup`,** and a role,
   `infrastructurebuilder.csis_spack.setup`, that carries it out. The
   role's defaults are `spack_setup: []`, the executable, and the default
   scope; it contains no step of its own.

   **YOUR DECISION (the shape):** an ordered list of steps, each naming
   its `kind` and that kind's options, carried out in the order written
   (default): a shell script maps onto it line by line, and the order
   stays the operator's; or a mapping with one fixed key per kind
   (`settings`, `detect`, `mirrors`, `keys`), carried out in one order
   the role fixes: shorter to write, but a site that must detect, then
   declare, then detect again cannot say so.

   With the default, the sandbox's `roles/spack` shell (the lines the
   operator selected) is this, and nothing in the collection:

   ```yaml
   spack_setup_spack: /save/environments/spack.v1.2.0/bin/spack
   spack_setup_scope: site
   spack_setup:
     - kind: config
       settings:
         config: {install_tree: {padded_length: 73}}
         modules: {default: {enable: [tcl]}}
     - kind: detect
       compilers: true
     - kind: detect
       externals: true
     - kind: detect
       externals: [cmake]
       not_buildable: true
     - kind: mirror
       name: spack-public
       url: https://cache.spack.io
     - kind: gpg_key
       from_mirrors: true
   ```

   and its `roles/intel_oneapi` shell, applied later, after the site's
   own tasks have installed the compilers, is a second list:

   ```yaml
   spack_setup:
     - kind: environment
       name: intel
       shell: |
         . /usr/share/Modules/init/bash
         module use -a /save/environments/modulefiles
         module load intel/compiler/2024.2.1 intel/compiler-intel-llvm/2024.2.1
         module load intel/ifort/2024.2.1 intel/mpi/2021.13 intel/mkl/2024.2
     - kind: detect
       compilers: true
       environment: intel
       require: [intel-oneapi-compilers@2024.2.1]
     - kind: config
       settings:
         packages:
           intel-oneapi-mkl:
             externals: [{spec: intel-oneapi-mkl@2024.2, prefix: /opt/intel/oneapi}]
             buildable: false
           intel-oneapi-mpi:
             externals: [{spec: intel-oneapi-mpi@2021.13, prefix: /opt/intel/oneapi}]
             buildable: false
           all:
             providers:
               mkl: [intel-oneapi-mkl]
               blas: [intel-oneapi-mkl]
               lapack: [intel-oneapi-mkl]
               scalapack: [intel-oneapi-mkl]
               mpi: [intel-oneapi-mpi]
     - kind: gpg_key
       from_mirrors: true
   ```

   Every name and number in these two lists is the sandbox's, kept in the
   sandbox. `require` is what stops the accident in the table above: a
   detection that ran without the environment fails, instead of quietly
   dropping the compilers.

   - A step may have a `name`, shown in the task's output; without one
     the role makes one from the kind and its main option.
   - The role checks the whole list before the first step runs (its
     `meta/argument_specs.yml`, and the kinds' own option checks): an
     unknown kind or option stops it with the step's number, and nothing
     has been changed.
   - The role's result is one list, a line per step: its name, whether it
     changed, and what.
   - A site that needs something done between two parts (as the sandbox
     installs oneAPI between the two lists above) applies the role twice,
     with two lists. The role keeps no state between runs.

3. **The environment a step runs in.** Some steps only mean something
   with a particular environment (modules loaded, a toolset enabled).
   What that takes is the site's knowledge too.

   **YOUR DECISION (environments):** a step kind `environment` (default):
   the operator gives it a name and the shell lines that produce the
   environment; the role runs them once, keeps what they changed in the
   environment under that name, and a later step names it
   (`environment: intel`). The shell is the operator's, contained in the
   configuration, and it is the only shell the role runs. Or no such
   kind: a step takes only an `environment` mapping of variables, and the
   site computes it in a task of its own before calling the role (as the
   sandbox's stage 10 does today).

4. **Examples, as data that is tested, not as built-in behaviour.**
   `docs/examples/` holds configurations for the situations the first
   plan called workflows. They show that the differences are all in the
   list:

   | Example | What its list does |
   | --- | --- |
   | The system's own compiler | settings; detect compilers and externals; a mirror; its keys. No environment |
   | A compiler installed outside Spack and reached through environment modules | an `environment` step; detect with it and `require`; settings for the externals and providers that are not detected |
   | A compiler built by Spack itself | detect the system's; (the site's own `spack_env` task builds the compiler); detect again with `paths` and `require` |
   | A compiler toolset beside the system's | detect with `paths`, or with an `environment`; `require` |
   | Compilers that are present but not wanted | detect with `exclude`, or `config` with `state: absent` afterwards |
   | A site mirror with its own key | `gpg_key` with `key` and `fingerprint`; `mirror`; `gpg_key` with `from_mirrors` |
   | The Cloud Sandbox's two scripts | the two lists above, whole |

   Each example is applied by the unit tests against the stand-in
   `spack`. For the sandbox's, the test also runs the sandbox's own shell
   commands against a second stand-in and holds the two to each other:
   the same configuration in the scope, the same mirrors and trusted
   keys, and the discovery commands in the same order. So "the
   configuration duplicates the script" is checked, not claimed. (The
   commands themselves need not be identical: `spack_config` writes two
   settings in one call where the script uses two.)

5. **Tried before anything is written,** on the local machine and, where
   it needs oneAPI, in the sandbox's test container, as 0.1.0's commands
   were:
   - exactly when `compiler find` removes a compiler it no longer sees,
     and from which scope;
   - that `config add -f` and `config get --json` round-trip lists and
     booleans unchanged, and what `mode: replace` has to do to remove a
     key;
   - what `gpg list --trusted` prints, to read fingerprints from;
   - whether `external find` detects an installed oneAPI's MKL and MPI.
     If it does, the sandbox's example gets shorter; the collection is
     the same either way.

   What these show goes into this file before the modules are written.

6. **Tests.**
   - Unit tests against the stand-in `spack`, extended to keep
     configuration per scope, mirrors, trusted keys, and a "machine" of
     compilers a test can change between runs: every option of every
     kind, a second run changing nothing, check mode, `require` failing,
     the removed-compiler accident reproduced and caught, a bad list
     refused before anything runs.
   - **A test that the collection carries no site knowledge:** it reads
     `plugins/` and `roles/` and fails on any package, compiler or
     mirror name from the examples.
   - Integration against the real Spack v1.2.0 on the local machine: the
     first example, a mirror in a directory, a key generated for the
     test; applied twice through the role.
   - The sandbox's lists against the real oneAPI are proved where oneAPI
     is: the Cloud Sandbox's container test, when the sandbox adopts the
     role. The collection does not install a compiler to test itself.

7. **The release.** **YOUR DECISION (version):** 0.3.0, after stage 1's
   0.2.0 (default); or both stages in one 0.2.0, if stage 1 has not been
   released when this is done.

## Decisions taken

Asked one at a time on 2026-11-14; each default was taken.

1. **The plain command:** `spack_command` is included.
2. **The shape:** an ordered list of steps.
3. **Environments:** a step of kind `environment`, running the operator's
   shell lines once and keeping the result under a name.
4. **Version:** 0.3.0.

## Tried against Spack v1.2.0 first

On the local machine, and, for oneAPI, in the Cloud Sandbox's test
container (AlmaLinux 10, oneAPI 2024.2.1 from dnf, Spack v1.2.0), which
was kept after a run and removed afterwards.

**Configuration**

- `spack config add -f <file>` takes **one section per file**; a file
  with two is refused. JSON is accepted.
- It **merges a list** into the one that is there, new items in front and
  none twice: adding `mpi: [mpich]` to `mpi: [intel-oneapi-mpi]` gives
  both. A scalar is replaced. So a list can only be set exactly by
  removing its path first, and that is what `spack_config` does.
- `spack config remove` of a path that is not there succeeds, and removing
  the last key of a mapping removes the mapping.
- Spack checks what is added against its schema and refuses a wrong type.
  If that happens after the module removed a path to make room, the
  module puts back what it removed.
- `spack config --scope user get` **fails while the scope's directory does
  not exist** ("must refer to an existing scope"), which is the state of
  the user scope on a fresh machine. The module reads that as an empty
  scope; writing makes it. (Found by the integration test.)

**Mirrors and keys**

- A mirror added with no flags is kept as a bare URL, with flags as a
  mapping; `--type binary --type source` gives both; adding a name that
  exists fails.
- `spack gpg trust` asks a question unless given `-y`. Its exit code says
  little: 0 for a file that holds no key. Whether a key is trusted is read
  from `spack gpg list --trusted --fmt colons` before and after, and the
  key file's own fingerprint with `gpg --show-keys` where there is a
  `gpg`.
- `--fmt keys` runs the fingerprints together with nothing between them.
- gpg's agent needs a short path for its socket; a keyring deep in a
  temporary directory makes `gpg trust` fail after importing.

**Detection, with the real oneAPI**

- **`spack compiler find` and `spack external find` never remove
  anything.** Run without the Intel modules they find no Intel compiler
  and leave the ones already registered alone. The plan's "the two
  `compiler find` steps undo each other" (taken from the sandbox's stage
  3) was not reproduced with Spack v1.2.0. What is true is the quiet
  half: without the environment nothing is found and nothing is said,
  which is what `require` is for.
- Each detection writes `packages.yaml` back **in another order**, so the
  file's bytes change while its data does not.
- `spack external find` does **not** detect a dnf-installed oneAPI's MKL
  or MPI, by name or with `--all`. The sandbox's externals stay declared.
- `spack compiler remove` puts an `id` on the compilers it leaves behind.

**The sandbox's own script**

- `spack config add` without `--scope` writes to the **user** scope. The
  sandbox's two settings (the install-tree padding and the Tcl modules)
  are therefore in the login user's `~/.spack`, not in the site scope
  with everything else, and no other user has them. The example says
  `scope: user` for that step, so that it reproduces the script; whether
  the sandbox wants that is the sandbox's to decide when it adopts this.

## What changed from the plan

- **The label of a step is `label`,** not `name`: a mirror step and an
  environment step already have a `name` with another meaning.
- **`mode: replace`** works a key of a section at a time: a key that is
  not given, or differs, is removed, and the given ones are added.
- **A step's `environment` may also be a mapping** of variables, as well
  as the name of a captured one.
- **No `meta/argument_specs.yml` for the role.** With one, ansible-core
  2.16.20 prints a deprecation warning of its own on every use (its
  implicit validation task uses a form of `action` that the same release
  deprecates). The role's own first task checks the list instead, and the
  role's README documents the three variables.
- **The examples in the documentation of 0.1.0's two modules** used the
  sandbox's paths and names; they are now neutral, and the test for site
  knowledge covers them.
- **`just test` takes two to three minutes**, not one: 193 tests, each
  running Ansible.

## Out of scope

- **Using this in the Cloud Sandbox.** That is a stage of the Cloud
  Sandbox's own: the two lists above become variables of its `spack` and
  `intel_oneapi` roles, each step carrying its traceability to
  `funcs-setup-instance.sh` as a comment; the shell tasks,
  `spack_fingerprint` and `spack_config_json` go; `spack-pubkey.sh`
  becomes a third list; and its container test proves all of it with the
  real oneAPI.
- Installing Spack itself, or any compiler. A site's playbook does that,
  before or between applications of the role.
- Per-user configuration (`~/.spack/config.yaml`): `spack_config` with
  `scope: user` can do it, but the sandbox writes it from a template,
  which is right for a whole file Ansible owns.
- Private keys, and signing.
- Testing against a fork of Spack (the sandbox's UFS add-on uses
  spack-stack). Its extra subcommands can be written as `spack_command`
  steps; whether they work is that site's to prove.

## Acceptance

- `just test` and `just full-test` pass.
- The role's defaults are empty, and the test for site knowledge passes.
- The sandbox example leaves the stand-in `spack` in the state the
  sandbox's shell commands leave it in, with the discovery commands in
  the same order.
- Against the real Spack v1.2.0, the first example applied twice changes
  nothing the second time, and check mode before the first run names
  every declared change and makes none.

## Outcome

- **Modules:** `spack_config`, `spack_mirror`, `spack_gpg_key`,
  `spack_detect`, `spack_command`, `shell_environment`; shared code in
  `plugins/module_utils/spack.py`.
- **Role:** `setup`, with empty defaults; `tasks/kinds/<kind>.yml` holds
  the one module call of each kind. Filters `setup_problems` (the check
  made before any step runs) and `setup_label`.
- **Examples:** seven under `docs/examples/`, each a list that the unit
  tests carry out against a stand-in machine made for it.
- **No site knowledge:** `tests/unit/test_no_site_knowledge.py` takes
  every package, mirror, path and module name out of the sandbox's
  example and fails if one is in `plugins/` or `roles/`. It caught one on
  its first run.
- **The sandbox's example against its shell, on a stand-in:** the test
  runs the sandbox's own Spack commands against a second stand-in and
  holds the two to each other: the same scopes, the same trusted keys,
  the discovery commands in the same order.
- **The same, with the real oneAPI:** in the sandbox's container, what
  its shell had written to the site and user scopes was dumped and wiped,
  and the example's two lists applied through the role from the built
  0.3.0 tarball. First application: 7 changes. Second: 0. Check mode
  afterwards: 0. The scopes, compared as data, were the same as the
  shell's in every section but one attribute: an `id` on three compiler
  entries, which came from a `spack compiler remove` in the earlier
  trials (confirmed), not from the sandbox's shell. This was a trial by
  hand, not a test that is kept: the sandbox's container test will hold
  it when the sandbox adopts the role.
- **Tests:** 193 unit tests through `ansible` and `ansible-playbook`
  against the stand-in. Integration against the real Spack v1.2.0 on the
  local machine, in a user scope and a keyring of the test's own: check
  mode writes nothing; the first application changes, the second does
  not; a list is set exactly; a changed mirror is corrected; `absent`
  removes only what is named; a value Spack's schema refuses fails and
  leaves the scope as it was. `just test` and `just full-test` pass,
  `ansible-test sanity` included.

