# infrastructurebuilder.csis_spack.setup

Makes a Spack ready to build, from one piece of configuration: a list of
steps, carried out in the order written.

The role has no step of its own and knows nothing about any site. Its
defaults are an empty list, the name `spack`, and the scope `site`. What a
site wants done to its Spack (which settings, which compilers, which
mirrors, in which order) is entirely in the list, which is that site's
shell script written as data. Each step is carried out by one of the
collection's modules, so each can tell whether it changed anything.

## Variables

| Variable | Default | What it is |
| --- | --- | --- |
| `spack_setup` | `[]` | The steps |
| `spack_setup_executable` | `spack` | The Spack executable, as a path or a name looked up on `PATH` |
| `spack_setup_scope` | `site` | The configuration scope of a step that does not name one |

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

| `kind` | Module | What it does | Options |
| --- | --- | --- | --- |
| `config` | `spack_config` | Declares settings in a configuration scope. Compared with what is there; a list is set exactly | `settings` (required), `state`, `mode`, `scope` |
| `mirror` | `spack_mirror` | Declares one mirror. A different one of the same name is replaced | `name` (required), `url`, `type`, `signed`, `state`, `scope` |
| `gpg_key` | `spack_gpg_key` | Trusts a public key from a file or URL, or the keys the mirrors publish | `key`, `fingerprint`, `from_mirrors` |
| `detect` | `spack_detect` | Has Spack look for compilers and installed packages. Discovery: it depends on the machine and on the step's environment | `compilers`, `externals`, `not_buildable`, `exclude`, `paths`, `require`, `scope` |
| `command` | `spack_command` | Runs any Spack command, for what the kinds above do not cover, with a stated way to tell a change | `args` and `changes` (required), `creates`, `sections`, `scope`, `env` |
| `environment` | `shell_environment` | Runs shell lines of yours and keeps the environment they produce under a name, for later steps. The only shell the role runs | `name` and `shell` (required), `executable` |

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
with its key, and one real site's two scripts. Each is applied by the
collection's tests.
