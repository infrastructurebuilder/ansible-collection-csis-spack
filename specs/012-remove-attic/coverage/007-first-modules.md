# Coverage: `ATTIC/PLAN.md`, "The first modules" → `specs/007-first-modules/`

For the operator; not part of the spec. Every paragraph and bullet of the
section "## The first modules: an environment, and a build cache
(2026-11-13)" (lines 49 to 227 of `ATTIC/PLAN.md`), and where it is now
carried. Line numbers are those of `ATTIC/PLAN.md` on 2026-11-27.

Also read, for facts about 0.1.0 that the section does not state, on the
same permission: `ATTIC/COLL-INPROGRESS/COLL-STAGE-1.md` ("What exists",
which describes the code of 0.1.0; its findings and outcome), and lines 14,
95 and 353 of `COLL-STAGE-2.md` and 32 to 36 of `COLL-STAGE-3.md`. Those
files are not covered here: each stage is its own retrospective.

## The section, line by line

| Lines | Source | Carried in |
| --- | --- | --- |
| 49 | Heading, with the date 2026-11-13 | [spec.md](spec.md): title, Created |
| 51–53 | Status: planned and executed 2026-11-13 on `feature/spack-env-module`, on the operator's "do the module plan"; released as 0.1.0 and pushed 2026-11-13 | [spec.md](spec.md): Feature Branch, Status, Input; [tasks.md](tasks.md): T022, "What became of it" |
| 54–55 | Pointers to Decisions taken and Outcome | Not carried: anchors within the ATTIC file. Their content is carried (below) |
| 59–62 | Why: the sandbox's `spack.yaml` from a template (its stage 9); what is left of `spack_environment` is three shell tasks that hash before and after | [spec.md](spec.md): Context |
| 64–68 | The table: three tasks, their commands, how each reports a change | [spec.md](spec.md): Context, the same table |
| 70–73 | Each loads the Intel modules first; none supports `--check`; `sandbox-ops` pushes with three hand-written scripts | [spec.md](spec.md): Context; US3 "Why this priority" |
| 75–77 | This plan makes those steps modules: Spack's commands, machine-readable output, change reporting and check mode | [spec.md](spec.md): Context; FR-013 |
| 79 | "What Spack v1.2.0 offers (read from its `--help`)" | [research.md](research.md): opening ("Read from Spack's `--help`") |
| 81–82 | `concretize [-f] [-U\|--fresh] [--reuse] [-q]` writes `spack.lock` | [research.md](research.md): R1 |
| 83–85 | `install [--fake] [--cache-only] [--use-buildcache ...] [-j N] [--only-concrete]`; `--fake` lets a test install in seconds | [research.md](research.md): R2 |
| 86 | `find --json`: the installed specs, with their hashes | [research.md](research.md): R3 |
| 87 | `module tcl refresh --delete-tree -y` | [research.md](research.md): R4 |
| 88–90 | `buildcache push [--unsigned\|--signed\|--key KEY] [--update-index] [--only ...] [-f] <mirror> [specs]`; in an environment with no specs it pushes the environment's | [research.md](research.md): R5 |
| 94–95 | Item 1, `spack_env`: bring an environment to a state | [spec.md](spec.md): FR-001; US1 |
| 96–103 | Its options: `path`, `spack`, `state`, `fresh` (default true, as the sandbox), `install_args`, `modules` (default none), `delete_tree` (default true) | [spec.md](spec.md): FR-002, with `log_file` and the later options noted; [plan.md](plan.md): Design |
| 104–106 | Changes reported separately: `concretized`, `installed`, `modules_refreshed`; `changed` is any | [spec.md](spec.md): FR-004; US1 scenarios 1–2 |
| 107–110 | Check mode: concretize a copy in a temporary directory; report the lock change and the specs not installed; touch nothing | [spec.md](spec.md): FR-005; US2; [research.md](research.md): Decisions 8 |
| 111–112 | Long builds under `async`; the result names the install's log | [spec.md](spec.md): FR-006 |
| 114–117 | YOUR DECISION: one module or three | [spec.md](spec.md): Clarifications Q1; [research.md](research.md): Decisions 1 |
| 119–126 | Item 2, `spack_buildcache_push`: options `env`, `mirror`, `key` or `unsigned`, `update_index`, `only`, `force`, `spack`; change from Spack's output and `buildcache list` before and after; check mode lists what would be pushed; the key never handled | [spec.md](spec.md): FR-008 to FR-011; US3; the plan's `buildcache list` against what was built: [research.md](research.md), last paragraph, and R5 |
| 128–130 | YOUR DECISION: pushing to a cache | [spec.md](spec.md): Clarifications Q2; [research.md](research.md): Decisions 2 |
| 132–139 | Item 3, Spack's surroundings: `module load` is a shell function; the role works out the environment once and passes `environment:`, or a `shell_init` option | [spec.md](spec.md): Clarifications Q3 and the note after them; FR-014; [plan.md](plan.md): "What surrounds Spack" |
| 141–143 | Item 4, the shared runner: `-e`, never a shell, output collected, a failure with the last lines | [spec.md](spec.md): FR-012; [plan.md](plan.md): "The shared runner"; [tasks.md](tasks.md): T003 |
| 145–150 | Item 5, unit tests: a fake `spack` first on `PATH`, answering from fixture files, recording calls; every option, change both ways, check mode, failures | [spec.md](spec.md): SC-004; [plan.md](plan.md): Tests; [tasks.md](tasks.md): T004–T007, T009, T011 |
| 151–152 | `ansible-test sanity` on both modules, which checks documentation against options | [spec.md](spec.md): SC-005; [tasks.md](tasks.md): T020 |
| 153–157 | Integration: the real v1.2.0 cloned once into `.tmp/`; one small package with `--fake`; each module twice; check mode first; a push to a local directory, `unsigned: true` | [spec.md](spec.md): US1–US3 Independent Tests, SC-001–SC-003; [research.md](research.md): R8; [tasks.md](tasks.md): T013 |
| 159–162 | YOUR DECISION: where the integration test runs | [spec.md](spec.md): Clarifications Q4; [research.md](research.md): Decisions 4 |
| 164–166 | Item 6, YOUR DECISION: Spack versions | [spec.md](spec.md): Clarifications Q5; FR-015; [research.md](research.md): Decisions 5 |
| 168–169 | Item 7, documentation: `DOCUMENTATION`, `EXAMPLES`, `RETURN`; the README's "What it holds"; `CHANGELOG.md` with 0.1.0 | [spec.md](spec.md): FR-016; [tasks.md](tasks.md): T016–T018 |
| 173 | Decisions asked one at a time on 2026-11-13; each default taken | [spec.md](spec.md): Clarifications, opening |
| 175–181 | The five decisions taken | [spec.md](spec.md): Clarifications (each A); [research.md](research.md): Decisions 1–5 |
| 185–189 | Out of scope: using the modules in `sandbox-provisioning` (pin, `just init` into `.collections/`, shell tasks to module calls with traceability comments, `units.toml`) | [spec.md](spec.md): Out of Scope, first bullet |
| 190–191 | Out of scope: publishing, until the operator says so | [spec.md](spec.md): Out of Scope, second bullet |
| 192–194 | Out of scope: the site and user Spack configuration, the `spack` role's, discovery rather than state | [spec.md](spec.md): Out of Scope, third bullet, with the later change noted |
| 198 | Acceptance: `just test` and `just full-test` pass | [spec.md](spec.md): Status; [tasks.md](tasks.md): T019, T020 |
| 199–200 | Acceptance: `just build` makes `infrastructurebuilder-csis_spack-0.1.0.tar.gz` holding both modules, and it installs | [spec.md](spec.md): SC-006; [tasks.md](tasks.md): T021 |
| 204–205 | Outcome: the two modules and the shared `module_utils/spack.py` | [plan.md](plan.md): Design, Project Structure |
| 206–214 | Outcome: behaviour tried by hand first (concretize, `install --fake`, `find --json`, `module tcl refresh`, `buildcache push` twice, `buildcache check -o`); the modules and the stand-in follow it: `find --json` with externals marked; `spack.lock` and `find` agree on hashes; `Pushed <spec>/<short hash>` or "All specs are already in the buildcache"; `buildcache check` lists what a mirror lacks, externals included, exit 1 when missing | [research.md](research.md): opening, R3, R5, R6; [tasks.md](tasks.md): T002, T004 |
| 215–219 | Found by the integration test: the time stamp in every module file; `module_tree_digest`; the same flaw in the Cloud Sandbox's role, recorded in its MAP.md | [research.md](research.md): R7; [spec.md](spec.md): Edge Cases; [tasks.md](tasks.md): T014, T015 |
| 220–221 | `just test`: ruff, pyright (0 errors), 45 tests through `ansible`, a build that installs | [spec.md](spec.md): Status, SC-004; [tasks.md](tasks.md): T019 |
| 222–226 | `just full-test`: both modules against the real v1.2.0 (check mode touches nothing, first run does the work, second changes nothing, a push reported once); `ansible-test sanity` passes for both | [spec.md](spec.md): SC-001–SC-005; [tasks.md](tasks.md): T020 |

## The section above it, "Collection stages" (lines 9–47)

Read for context only, as asked. It is the index of the five stage plans of
2026-11-14 to 2026-11-17, each its own retrospective (stage 5 is already
[specs/001-galaxy-publish/](../001-galaxy-publish/spec.md)). From it this
spec takes only the names and dates of the development versions it mentions
in its *Changed later* notes: 0.2.0 (stage 1), 0.3.0 (stage 2) and 0.3.1
(stage 4), all 2026-11-14. Line 46–47 (the order among the Cloud Sandbox's
stages is in that repository's `PLAN.md`) is the Cloud Sandbox's and is not
carried.

## Deliberately not carried, and why

- **The in-file anchors** (`#decisions-taken`, `#outcome`, line 54–55): they
  point inside the ATTIC file.
- **"YOUR DECISION" as a form**: the questions are carried as Q → A under
  Clarifications; the bold prompts were how the plan asked them.
- **The tarball's name with 0.1.0** is carried only as history (tasks T021).
  0.1.0 was withdrawn and its tag deleted; no version requirement or pin in
  the repository should name it, and none does.
- **"the version the sandbox pins" (v1.2.0)** is carried as the version the
  tests were written to, which it still is (constitution, principle III;
  [tests/integration/real_spack.py](../../tests/integration/real_spack.py)).
  What the Cloud Sandbox pins today is that repository's business.
- **The Cloud Sandbox's stage number** ("its stage 9", line 60): the
  Context keeps what that stage did (the `spack.yaml` written from a
  template), not its number, which is that repository's numbering.

## Where the source and the code disagree

- **What was pushed (line 123–124).** The plan said the change would come
  "from Spack's output and `spack buildcache list` against the mirror
  before and after". As built (Outcome, and `COLL-STAGE-1.md` "What
  exists"), a real run read only Spack's `Pushed` lines (`pushed_specs()`),
  and `buildcache check` was asked only in check mode; `buildcache list` was
  not used. Since 0.2.0 a real run asks `buildcache check` before and after.
  Carried as built: spec FR-009, research R5, R6 and the last paragraph.
- **Options and returns the plan did not list.** Today's `spack_env` has
  `log_file` (an option, as well as the return the plan named), `lmod` as a
  choice of `modules`, and returns `roots` and `spack_version`;
  `spack_buildcache_push` returns `mirror_url` and refuses an unknown mirror
  name. No plan or spec records adding them later, so the spec takes them
  as 0.1.0's and says so (spec, Assumptions). This is the one inference the
  spec makes.
- **Module roots in 0.1.0** were read in a way that needed PyYAML
  (`COLL-STAGE-1.md`, "Tried against Spack v1.2.0 first"); how exactly is
  not recorded. Since 0.2.0 they come from `config get --json modules`.
  Carried as a note in research R4; the spec makes no claim about how.
- **Check mode and module files.** The plan's check mode says nothing about
  module files. Today's check mode reports them where a change is certain;
  that came with 0.2.0 (`COLL-STAGE-1.md`, Outcome). Carried as a *Changed
  later* note on FR-005.

## Nothing left unplaced

Every paragraph and bullet of the section is placed above. After these
files are in `specs/007-first-modules/`, the section adds nothing that the
spec does not hold, except the in-file anchors and the form of the
decision prompts.
