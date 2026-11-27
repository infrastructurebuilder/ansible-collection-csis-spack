# Interface contract: the `setup` role, its kinds and their modules

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)

As built in 0.3.0. Options added later are named under **Later** for each
module; `ansible-doc infrastructurebuilder.csis_spack.<module>` gives the
options as they are today.

## The role `infrastructurebuilder.csis_spack.setup`

```yaml
- hosts: build_hosts
  roles:
    - role: infrastructurebuilder.csis_spack.setup
      vars:
        spack_setup_spack: /opt/spack/bin/spack   # default: spack, on PATH
        spack_setup_scope: site                   # the default
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

Every step may also have `label` and (but for `environment`) `environment`:
a captured environment's name, or a mapping of variables.

Leaves `spack_setup_results` ([../data-model.md](../data-model.md), "The
results").

**Later**: spec 002, the executable's variable is `spack_setup_executable`,
and `spack_setup_spack` still works; spec 003, `spack_setup_yes_to_all` and
a step's `yes_to_all`; spec 004, the kind `spack`; spec 005, its `move`.

## The modules, by kind

Every module but `shell_environment` also takes `spack` (str, default
`spack`): the executable, a path or a name looked up on `PATH`. Each runs
`spack --version` first and fails below 1.0. Each returns `spack_version`.
The modules support check mode. None runs Spack through a shell. The role
passes `spack_setup_spack` as `spack`, and a step's `scope`, or
`spack_setup_scope`, as `scope`.

**Later**, spec 003: each of them but `shell_environment` takes
`yes_to_all` (bool, default `false`), and on Spack 1.0 the configuration is
read through `spack python -c`, which has no `config get --json`.

### `config`: `spack_config`

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `settings` | dict | required | Sections at the top, each a mapping. With `state: absent`, the values are not read: each path that ends in something other than a non-empty mapping is removed |
| `scope` | str | `site` | |
| `state` | `present`, `absent` | `present` | |
| `mode` | `merge`, `replace` | `merge` | `replace`: each section named becomes exactly what is given |

Returns `paths` (the paths set or removed, or that would be), `scope`.
Supports diff mode. Refuses a section that is not a mapping, a whole
section to remove with no keys named, and a key that holds a colon.

Runs: `spack config --scope <scope> get --json <section>`;
`spack config --scope <scope> remove <path>`;
`spack config --scope <scope> add -f <file>` (one section per file).

### `mirror`: `spack_mirror`

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `name` | str | required | |
| `url` | str | | Required with `state: present` |
| `type` | list of `binary`, `source` | | Left out: Spack's default, not compared |
| `signed` | bool | | `--signed` or `--unsigned`. Left out: not compared |
| `scope` | str | `site` | |
| `state` | `present`, `absent` | `present` | |

Returns `action` (`added`, `replaced`, `removed`, `none`) and `mirror` (as
the scope holds it afterwards).

Runs: `spack config --scope <scope> get --json mirrors`;
`spack mirror add --scope <scope> [--type ...] [--signed|--unsigned] <name> <url>`;
`spack mirror remove --scope <scope> <name>`.

### `gpg_key`: `spack_gpg_key`

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `key` | str | | A public key file on the node, or a URL to fetch it from |
| `fingerprint` | str | | 40 hexadecimal digits (spaces and case allowed) the key must have. Needs `key`. Given, a key trusted already is not fetched or read |
| `from_mirrors` | bool | `false` | Trust the keys the configured binary mirrors publish |

One of `key` and `from_mirrors` is needed. Returns `trusted` (the
fingerprints newly trusted, or in check mode those known to be missing) and
`previewed` (false where check mode cannot tell).

Runs: `spack gpg list --trusted --fmt colons` (before and after);
`gpg --show-keys --with-colons <file>` where the node has `gpg` or `gpg2`;
`spack gpg trust -y <file>`; `spack buildcache keys --install --trust`.

**Later**: spec 003, `yes_to_all`; the trusts take `--yes-to-all` on Spack
1.2 and later and no answer on 1.0 and 1.1; on 1.0 and 1.1 the trusted keys
are read from gpg's own listing.

### `detect`: `spack_detect`

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `compilers` | bool | `false` | Run `spack compiler find` |
| `externals` | `true`, `false`, or a list of names | `false` | Run `spack external find`, for Spack's default set or for the names given |
| `not_buildable` | bool | `false` | `--not-buildable` |
| `exclude` | list of str | `[]` | `--exclude` for each |
| `paths` | list of paths | `[]` | Where to look instead of `PATH`: given to `compiler find`, and as `-p` to `external find` |
| `require` | list of str | `[]` | Specs that must be registered afterwards, in any scope; a version accepts anything more exact |
| `scope` | str | `site` | Where detection records |

At least one of `compilers` and `externals`. Returns `added`, `removed`
(external specs), `previewed` (false in check mode).

Runs: `spack config --scope <scope> get --json packages` (before and
after); `spack compiler find --scope <scope> [paths...]`;
`spack external find --scope <scope> [--not-buildable] [--exclude N]...
[-p P]... [names...]`; `spack config get --json packages` (every scope, for
`require`).

### `command`: `spack_command`

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `args` | list of str | required | The command, as Spack takes it after its own name |
| `changes` | `config`, `creates`, `always`, `never` | required | How a change is told |
| `creates` | path | | Required with `changes: creates`; while it exists the command is not run |
| `sections` | list of str | `[config, concretizer, mirrors, modules, packages, repos]` | Compared with `changes: config` |
| `scope` | str | `site` | Compared with `changes: config` |
| `env` | path | | A Spack environment's directory to run the command in (`spack -e`) |

Returns `ran`, and `stdout` when it ran.

### `environment`: `shell_environment`

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `shell` | str | required | The lines to run |
| `executable` | path | `/bin/bash` | The shell to run them with |

In the role, the step also has `name` (required), the name later steps use.
Returns `environment` (the variables set or changed, with their values) and
`unset` (the variables removed, which Ansible's `environment` keyword
cannot express). Leaves out what a shell changes by running (`_`, `SHLVL`,
`PWD`, `OLDPWD`) and exported shell functions. Never reports a change.

## The filters

| Filter | Input | Returns |
| --- | --- | --- |
| `setup_problems` | the list | a list of sentences, one per problem; empty when the list can be carried out |
| `setup_label` | one step | its label |

```yaml
- name: Refuse a list of steps that cannot be carried out
  ansible.builtin.assert:
    that: spack_setup | infrastructurebuilder.csis_spack.setup_problems | length == 0
```

**Later**: spec 004, `setup_problems` takes the executable as an optional
argument, and a third filter, `setup_executable`, gives the Spack the steps
run.
