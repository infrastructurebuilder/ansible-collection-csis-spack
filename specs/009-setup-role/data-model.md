# Data Model: Set Spack up from one piece of configuration

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

As built in 0.3.0. A **Later** note says where a later spec changed it.

## The role's variables

| Variable | Default | What it is |
| --- | --- | --- |
| `spack_setup` | `[]` | The list of steps, carried out in the order written |
| `spack_setup_spack` | `spack` | The Spack executable, a path or a name looked up on `PATH` |
| `spack_setup_scope` | `site` | The configuration scope of a step that names none |

**Later**: spec 002 named the executable's variable `spack_setup_executable`
(default `spack`); `spack_setup_spack` still works when the new name is not
set. Spec 003 added `spack_setup_yes_to_all` (default `false`).

## The list

`spack_setup` is a list. Each item is a step: a mapping.

## A step

| Field | Required | Type | Rule |
| --- | --- | --- | --- |
| `kind` | yes | one of the kinds below | |
| that kind's options | as the kind says | as its module says | passed to the module as given; an option left out is left to the module's default |
| `label` | no | string | shown in the output; without it, the kind and its main option (below) |
| `environment` | no | string or mapping | the name of an environment an earlier `environment` step captured, or a mapping of variables. Not allowed on an `environment` step |

`scope`, on the kinds that have it, defaults to `spack_setup_scope`, not to
the module's own default.

**Later**: spec 003 added `yes_to_all` to every kind but `environment`.

## The kinds

| Kind | Nature | Module | Required | Optional |
| --- | --- | --- | --- | --- |
| `config` | declared | `spack_config` | `settings` | `scope`, `state`, `mode` |
| `mirror` | declared | `spack_mirror` | `name` | `url`, `type`, `signed`, `scope`, `state` |
| `gpg_key` | declared | `spack_gpg_key` | | `key`, `fingerprint`, `from_mirrors` |
| `detect` | discovery | `spack_detect` | | `compilers`, `externals`, `not_buildable`, `exclude`, `paths`, `require`, `scope` |
| `command` | as `changes` says | `spack_command` | `args`, `changes` | `creates`, `sections`, `scope`, `env` |
| `environment` | captures; changes nothing | `shell_environment` | `name`, `shell` | `executable` |

The executable is the role's, never a step's option.

**Later**: spec 004 added the kind `spack` (module `spack_checkout`;
`version` and `path` required, `source` optional; first step only); spec 005
gave it `move`.

What each nature means:

- **Declared**: the answer is known before anything runs. Compared with
  Spack, changed only where different, previewed exactly in check mode.
- **Discovery**: depends on the machine and the step's environment. Not
  previewed; in check mode nothing runs. `require` says what must be found.
- **Command**: a change is what `changes` says (`config`, `creates`,
  `always`, `never`). In check mode not run.
- **Environment**: runs the site's shell lines once and keeps the variables
  they set or changed. Never a change.

## Labels (`setup_label`)

`label` when given; otherwise `<kind>: <detail>`, or the kind alone when
there is no detail:

| Kind | Detail |
| --- | --- |
| `config` | the section names, sorted, separated by a comma and a space; with `state: absent`, `remove from <sections>` |
| `mirror` | `name` |
| `gpg_key` | `key`, or `from the mirrors` |
| `detect` | `compilers`, and the external names (or `externals`), separated by the word "and" |
| `command` | `args`, separated by spaces |
| `environment` | `name` |

## The check before any step (`setup_problems`)

Each problem is a sentence naming the step's number. The list is refused,
with nothing changed, if any of these is found:

- `spack_setup` is not a list; a step is not a mapping;
- a step's `kind` is missing or unknown (the sentence lists the kinds);
- an option that is not the kind's, nor `kind`, `label` or `environment`
  (and `environment` on an `environment` step);
- a required option missing;
- `environment` names an environment no earlier step captures, or is
  neither a name nor a mapping;
- an `environment` step whose `name` an earlier step already captures.

Values are not checked; each module checks them when its step runs.

**Later**: spec 004 added the rules for a `spack` step (the first and only
one; an absolute `path`; agreement with `spack_setup_executable`).

## Captured environments

`spack_setup_environments`, a mapping from an `environment` step's `name` to
the variables its shell lines set or changed. Empty at the start of each
application of the role; not kept between applications.

The environment a step runs in:

- no `environment`: the play's;
- a mapping: those variables;
- a name: the variables captured under it.

## The results

`spack_setup_results`, a list with one entry per step carried out:

| Key | Value |
| --- | --- |
| `step` | its number, from 1 |
| `kind` | its kind |
| `label` | its label |
| `changed` | whether it changed something (in check mode, would) |
| `result` | what its module returned |

A step that fails stops the role; the steps before it keep their entries.

**Later**: spec 004 added entries for steps not carried out in check mode
after an install (`previewed: false`, with the reason).

## How the role runs a list

```text
check the whole list (setup_problems)  --problem-->  stop, nothing changed
          |
start: no captured environments, no results
          |
for each step, in order:
   run kinds/<kind>.yml (one module call) with the step's environment
   environment step: keep its variables under its name
   record the step's entry in spack_setup_results
   a failure stops here
```

## The examples

Each is a file of variables for the role under `docs/examples/`, with one
or more lists (`spack_setup`, or `spack_setup_<when>` where the role is
applied more than once).

| Example | What its list does |
| --- | --- |
| `system-compiler.yml` | settings; detect compilers and externals; a mirror; its keys. No environment |
| `compiler-in-environment-modules.yml` | an `environment` step; detect with it and `require`; settings for the externals and providers that are not detected |
| `compiler-built-by-spack.yml` | two lists: detect the system's; (the site's own `spack_env` task builds the compiler); detect again with `paths` and `require` |
| `compiler-toolset.yml` | detect the system's; detect again with `paths` and `require` |
| `unwanted-compilers.yml` | detect; `config` with `state: absent` afterwards (a change on every run, as its comment says) |
| `site-mirror-with-key.yml` | `gpg_key` with `key` and `fingerprint`; `mirror`; a `command` step |
| `cloud-sandbox.yml` | the sandbox's two scripts, as `spack_setup_base` and `spack_setup_intel` |

Where the plan named two forms, the example shows one. A toolset: the plan
said "detect with `paths`, or with an `environment`"; the example uses
`paths` (an `environment` is shown by `compiler-in-environment-modules.yml`).
Unwanted compilers: the plan said "detect with `exclude`, or `config` with
`state: absent` afterwards"; the example uses `state: absent`, and `exclude`
is an option of `detect` (contracts/interface.md). A site mirror: the plan
said "`gpg_key` with `key` and `fingerprint`; `mirror`; `gpg_key` with
`from_mirrors`"; the example ends instead with a `command` step that reads
the mirror's index (`changes: never`); the plan does not record why.

**Later**: spec 004 added `spack-installed-by-the-role.yml`.
