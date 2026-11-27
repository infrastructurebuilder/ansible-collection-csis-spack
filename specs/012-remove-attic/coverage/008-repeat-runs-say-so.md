# Coverage: `ATTIC/COLL-INPROGRESS/COLL-STAGE-1.md` into spec 008

For the operator; not part of the spec. Every paragraph and bullet of the
source, in its order, and where it is now carried. Line numbers are the
source's. "spec", "plan", "research", "data-model", "tasks" and "checklist"
are the files of `specs/008-repeat-runs-say-so/`.

## The source file

| Source (lines) | What it says | Carried in |
| --- | --- | --- |
| Title (1) | Collection stage 1: repeat runs that do nothing and say so | spec, title; every file's title |
| Status (3-7) | Planned 2026-11-14 on `feature/coll-stage-1`, executed the same day on "do coll 1"; merged, released as 0.2.0, pushed on the operator's word | spec, Feature Branch and Status; tasks, header note and T022 |
| Why, opening (11-14) | Asked whether 0.1.0's modules are idempotent: "mostly"; proved against Spack v1.2.0 and in the Cloud Sandbox's container test | spec, Input |
| Why 1 (16-20) | `spack_env` regenerates every run, deleting the tree first; module files missing for a moment | spec, Input 1; US1, Why this priority |
| Why 2 (21-23) | `force: true` pushes and reports a change every run, unsaid | spec, Input 2; US4 |
| Why 3 (24-27) | Pushed packages read from Spack's `==> [n/m] Pushed` lines; a later Spack could break it silently | spec, Input 3; US3, Why this priority; research, Before this work |
| What exists: `spack_env` (31-34) | `apply()`: digest, `spack module <system> refresh -y [--delete-tree]`, digest | research, Before this work |
| What exists: `spack_buildcache_push` (35-38) | Check mode asks `buildcache check -m -o`; a real run reads output with `pushed_specs()` | research, Before this work; tasks T013 (`pushed_specs()` removed) |
| What exists: tests (39-41) | The stand-in answers both commands; the integration test runs both twice on v1.2.0 | research, Before this work |
| Item 1, `refresh_modules` and its values (45-59) | `always`; `when_needed` with its conditions; the stamp's three digests; a file deleted or edited by hand is put back | spec, FR-001 to FR-003, US1, US2; data-model, the stamp and `modules_reason`; plan, Design; tasks T008, T009 |
| Item 1, the stamp in Spack's directory (60-63) | Spack leaves unknown files in `.spack-env/` alone and removes them with `spack env rm`; the README says so | spec, Assumptions (first bullet), Edge Cases (last bullet), FR-014; tasks T018; [README.md](../../README.md), "What the modules keep in the environment's directory" |
| Item 1, `modules_reason` (65-66) | The result says why it regenerated, or that it did not | spec, FR-005; data-model, `modules_reason`; tasks T010 |
| Item 1, decision: the default (68-71) | `when_needed` or `always` | spec, Clarifications Q1; research, Decisions 1 |
| Item 1, decision: what counts as "needed" (73-78) | The stamp, or only "concretized, installed, root missing" | spec, Clarifications Q2; research, Decisions 2 |
| Item 2, decision: `force` (80-88) | A warning; `force: once` with a stamp beside the environment; or documentation only | spec, Clarifications Q3, FR-010 to FR-012, US4; research, Decisions 3 |
| Item 3, decision: how to know what was pushed (90-100) | Ask the mirror before and after (two index reads, a few seconds on S3), or keep reading the lines and warn | spec, Clarifications Q4, FR-008, Assumptions (cost); research R3, Decisions 4 |
| Item 3, `force: true` (102-103) | With `force: true` the mirror lacks nothing after; "pushed" is what was selected and pushed | spec, Assumptions (third bullet), FR-011 |
| Item 4, unit tests (106-111) | `refresh_modules` both ways, every reason; the stamp written, read, outdated (lock, configuration, file deleted or edited, not the time line); the `force` warning or `once`; the push from the mirror, also with lines in another form | spec, SC-004; plan, Tests; tasks T006, T007, T012, T014 |
| Item 4, integration tests (112-116) | A second `when_needed` run leaves every file and modification time; a second naming scheme regenerates; a deleted file regenerates; the push is reported once | spec, SC-001 to SC-003; tasks T017. See "Where the source and the code disagree", 2 |
| Item 4, sanity (117) | `ansible-test sanity` on both modules | spec, SC-005; tasks T021 |
| Item 5, the release (119-122) | 0.2.0, a minor version; `CHANGELOG.md`, `version_added`, README; tagged locally, pushed on the operator's word | spec, Status, Assumptions (last bullet); tasks T019, T022; plan, Constitution Check V |
| Item 5, the Cloud Sandbox (122-124) | Moving the sandbox to 0.2.0 is a stage of its own | spec, Out of scope |
| Decisions taken (126-135) | Asked one at a time on 2026-11-14; the four answers | spec, Clarifications (session heading and the four answers) |
| Tried 1 (139-142) | `config get --json modules` merged, defaults included; roots read from it; no PyYAML | research R1 (with the later note on Spack 1.0 and `DEFAULT_MODULE_ROOTS`); spec, FR-004 |
| Tried 2 (143-144) | `.spack-env/` exists once concretized, with or without a view | research R2 |
| Tried 3 (145-148) | `buildcache check` sees a fresh push without `--update-index` | research R3 |
| Tried 4 (149-153) | `push --force --only package <mirror> /<hash>...` pushes exactly those; one package prints `==> Pushed` with no counter | research R4; spec, FR-012 |
| Out of scope: the Cloud Sandbox (157-164) | Its own stage; its role passes only `modules: [tcl]`, so the default would change it silently; that stage sets `refresh_modules` explicitly, notes the difference from its script, updates its traceability and `MAP.md` | spec, Out of scope (first bullet), in part. The rest is the Cloud Sandbox's own work, not carried: see below |
| Out of scope: `update_index` (166-167) | Rebuilds the index every run without reporting it | spec, Out of scope (known limitations), naming spec 006; plan, Constitution Check II; checklist, Notes |
| Out of scope: check mode's copy (168-169) | Does not find relative `include:` and `develop:` files | spec, Out of scope (known limitations), naming spec 006; checklist, Notes |
| Out of scope: other Spack versions (170) | Testing against versions other than v1.2.0 | spec, Out of scope (last bullet) and Assumptions (spec 003 did it); plan, Constitution Check III |
| Acceptance (174-177) | `just test` and `just full-test` pass; a second default run changes no file under the roots; the push reports exactly what the mirror gained | spec, SC-001, SC-002, SC-005; tasks T020, T021 |
| Outcome: `spack_env` (181-187) | `refresh_modules`, `modules_reason`; the stamp's name and contents; check mode gives the reason and reports changes only where certain | spec, FR-001 to FR-007, US2 scenario 5, Edge Cases (check mode); data-model; plan, Design |
| Outcome: `spack_buildcache_push` (188-194) | Pushed is what the mirror gained plus what `force` overwrote; `force: once` keeps `.spack-env/csis_spack.pushed.json` per mirror URL, overwrites by hash, then pushes normally; `force: true` warns; lines not read; the stand-in words them differently in a test | spec, FR-008 to FR-012, US3, US4; data-model, the record and `force`; plan, Design; tasks T013, T015, T016 |
| Outcome: found while writing it (195-199) | The default module root is shared; `--delete-tree` removes all of it; documented in the option and the README | research R5; spec, Edge Cases (first bullet), FR-013; tasks T011, T018; [README.md](../../README.md), "One module tree, several environments" |
| Outcome: tests (200-207) | 72 unit tests (45 before); the integration test's new holds; `just test` and `just full-test` pass, sanity included | tasks T017, T020, T021; spec, SC-003, Status |
| Outcome: release (208) | 0.2.0, tagged and pushed 2026-11-14 | spec, Status; tasks T022 |

## Its line in `ATTIC/PLAN.md`

| Source (lines) | What it says | Carried in |
| --- | --- | --- |
| Collection stages, Status (11-12) | Stage 1 executed and released as 0.2.0 on 2026-11-14 | spec, Status |
| Collection stages, how stages were run (17-21) | One file per stage, each executed on `do coll <n>` after decisions asked one at a time | tasks, header note ("do coll 1"); spec, Clarifications ("Asked one at a time") |
| The stage 1 entry (23-26) | Repeat runs that do nothing and say so (module files only when needed, `force` left on, what was pushed known from the mirror); released as 0.2.0 | spec, title, Input and Status |

The withdrawal of 0.2.0 is already in [CHANGELOG.md](../../CHANGELOG.md)
("Before 0.0.1") and in the Assumptions of
[specs/001-galaxy-publish/spec.md](../001-galaxy-publish/spec.md), whose
table gives 0.2.0's tag message; the spec points to both.

## Not carried, on purpose

- **The Cloud Sandbox's side of the move** (source 122-124 and 157-164):
  the line in `sandbox-provisioning/requirements.yml`, its `units.toml`,
  setting `refresh_modules` in its `spack_environment` role, the note beside
  it, the role's traceability and `MAP.md`. That is work in the
  Cloud-Sandbox repository, under its rules. The sandbox never took 0.2.0:
  it moved straight to 0.3.0, setting `refresh_modules: when_needed`, in its
  stage 11, which this repository planned as `COLL-STAGE-3.md`; the
  retrospective of that stage (010, being written) carries it. Spec 008 keeps only that it was out of scope, and
  why the sandbox had to set the option explicitly.
- **0.2.0 as a version for `version_added`** (source 119-121): the number no
  longer means anything. The tag was deleted, and the modules carry
  `version_added: 0.0.1`. The spec says so once, in Assumptions.
- **"Merged into `develop`" as a fact that can be checked**: the commits are
  gone since the history reset of 2026-11-18. The spec records it as the
  source says it, without a commit hash.
- **The source's links** (`../../plugins/modules/...`): replaced by the
  paths of the files today.
- **"72 unit tests (45 before)"** is kept in tasks T020 as what was counted
  then. It is not a claim about today's test count.
- **The "YOUR DECISION (default)" wording**: the options and the defaults
  proposed are carried in the Clarifications' questions; the marker itself is
  the old procedure's.

## Where the source and the code disagree

1. **`force: true` warns "on every run"** (Outcome, 192). The code warns only
   in a real run; check mode lists every package and gives no warning. The
   spec describes the code (FR-011, Edge Cases).
2. **The integration test "enabling a second module naming scheme"** (Item 4,
   114). The test as built changes the configuration another way
   (`tcl: hash_length: 3`) and holds that it regenerates with nothing to
   install. The Outcome's own wording ("a changed modules configuration")
   matches the code; the spec uses it (SC-003).
3. **Roots read from `config get --json modules`** (Tried 1). True on Spack
   1.1 and 1.2. Spack 1.0 has no `config get --json`, so `spack_env` with
   `modules` failed on 1.0 as released in 0.2.0 and 0.0.1; spec 003 fixed it
   in 0.0.3 (`spack python -c`, through `BEHAVIOUR`). The code also falls back
   to Spack's default roots (`DEFAULT_MODULE_ROOTS`) when the configuration
   names none, which the source does not mention. The spec notes both (FR-004,
   research R1).
4. **"Tested against v1.2.0 only"** (Out of scope, 170): no longer true; the
   integration test runs on 1.0.0, 1.1.0 and 1.2.0 since spec 003.
5. **`version_added` for the new options** (Item 5): there is none; the
   options came with the modules in 0.0.1.
6. **The README's summary of `when_needed`** ([README.md](../../README.md),
   "Building an environment") lists every condition but a missing module
   root; the option's documentation and `CHANGELOG.md` list it. Not a
   disagreement with the source, but a small gap found while checking; the
   spec does not change it.

## Could not place

Nothing. Every paragraph and bullet of the source is carried above, or left
out for a reason given.
