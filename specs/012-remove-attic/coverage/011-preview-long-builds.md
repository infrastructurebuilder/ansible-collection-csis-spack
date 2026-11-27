# Coverage: `ATTIC/COLL-INPROGRESS/COLL-STAGE-4.md` into spec 011

For the operator, not part of the spec. Every paragraph and bullet of the
source, and the lines of `ATTIC/PLAN.md` and `ATTIC/COLL-INPROGRESS/COLL-STAGE-3.md`
that concern it, with where each is now carried. Line numbers are the
source's as of 2026-11-27.

## `ATTIC/COLL-INPROGRESS/COLL-STAGE-4.md`

| Source (lines) | What it says | Carried in |
| --- | --- | --- |
| Title (1) | "Collection stage 4: say how to preview a long build (0.3.1)" | spec.md title; the 0.3.1 in the Status line |
| Status, sentence 1 (3-5) | Planned 2026-11-14 on `feature/remaining-plans`; executed the same day on "do coll 4", on `feature/coll-stage-4`; merged into `develop` | spec.md **Created**, **Feature Branch** and **Status**; tasks.md T015. "do coll 4" is not carried (below) |
| Status, sentence 2 (5-6) | Kept unreleased by decision, until the Cloud Sandbox's stage 12 found a defect in `spack_config` the same day | spec.md Clarifications (Q1, Q4), Status, Assumptions ("The fix released with it") |
| Status, sentence 3 (6-8) | The operator chose to fix it, release both as 0.3.1, and move the sandbox's pin to it in that stage | spec.md Clarifications (Q4), Outcome; tasks.md T016, T017 |
| Status, sentence 4 (8-9) | Pointers to Decisions taken and Outcome | spec.md Clarifications and Outcome (the structure itself) |
| Status, sentence 5 (9-11) | First in the order of the remaining work (Cloud-Sandbox's `PLAN.md`): depends on nothing, nothing waits for it, the smallest | spec.md Assumptions, the bullet "It depended on nothing" |
| Why (15-22) | Found in stage 3 on the sandbox's container test; Ansible's message; `spack_env` wants `async` and claims check mode; its notes said only "Run the task with `async` and `poll`"; copied as they were, a playbook could not be previewed; the sandbox found it the hard way | spec.md **Input**; research.md R1; spec.md US1 "Why this priority" |
| Item 1 (26-35) | The notes say `async` cannot run in check mode, give the two-line form, and the reason (a preview builds nothing and is over in a minute) | spec.md FR-001, FR-002; plan.md Design, `spack_env`'s documentation; research.md R1 Decision; tasks.md T003 |
| Item 2 (37-38) | The examples in `EXAMPLES` and the README use the form | spec.md FR-003; plan.md Design; tasks.md T004, T005 |
| Item 3, sentence 1 (40-42) | A unit test reads `EXAMPLES` and the README and fails on any `async:` with a literal number | spec.md FR-004, US2, SC-003; plan.md test table; tasks.md T008, T009. Widened as built: `poll:` too, and `roles/setup/README.md` |
| Item 3, sentence 2 (42-44) | A test runs the form through `ansible-playbook --check` against the stand-in `spack`: passes, builds nothing | spec.md FR-005, US1 scenario 1; tasks.md T006 |
| Item 4 (46) | `CHANGELOG.md`, 0.3.1: documentation only | spec.md FR-008; tasks.md T011. Now under 0.0.1, "Building an environment". "Documentation only" did not stay true of 0.3.1 once the fix joined it (spec.md Assumptions) |
| YOUR DECISION, the release (48-50) | Cut 0.3.1 and push it (default), or keep it on `develop` | spec.md Clarifications Q1, with the default |
| YOUR DECISION, the pin (52-55) | Leave at 0.3.0 (default, and why), or move to 0.3.1: one line in each of `requirements.yml` and `units.toml` and a container run | spec.md Clarifications Q2, with the default, its reason and the two files |
| Decisions taken, "Asked on 2026-11-14" (59) | The date | spec.md Clarifications, "Session 2026-11-14" |
| Decision 1 (61-63) | Keep on `develop`, not the default; no tag; version stays 0.3.0 in `galaxy.yml`; changelog says "Unreleased (to be 0.3.1)" | spec.md Clarifications Q1 answer; tasks.md T011 |
| Decision 2 (64-70) | First "move it to 0.3.1", which cannot be done without a tag; asked again: no tag now, the pin moves when 0.3.1 is cut; at the next release tag 0.3.1, move `sandbox-provisioning/requirements.yml` and `exportit/cloud-sandbox/units.toml`, run the container test | spec.md Clarifications Q2, Q3; spec.md Assumptions ("The release and the pin, as history": carried out, then superseded by 0.0.1 and spec 001); tasks.md T017, T018 |
| Out of scope (74) | Any change to what a module does | spec.md FR-007 and Out of Scope; plan.md Constraints |
| Acceptance (78-79) | `just test` and `just full-test` pass; `ansible-doc` shows the note | spec.md SC-004, Status (the source does not quote the runs' output); plan.md Technical Context; tasks.md T012, T013, T014 |
| Outcome bullet 1 (83-85) | Notes say why and give the form; example and README use it; `ansible-doc` shows the note | spec.md Outcome, first bullet |
| Outcome bullet 2 (86-88) | The README's two examples used one site's paths and names (the site-knowledge test looks only at `plugins/` and `roles/`); now neutral | spec.md US3, FR-006, Outcome; plan.md Design, the README; tasks.md T010 |
| Outcome bullet 3 (89-93) | `tests/unit/test_async_and_check_mode.py`: notes and examples held to the form; no example anywhere gives `async` or `poll` as a plain number; previews without building, builds when not previewing, a plain number fails with Ansible's message | spec.md US1 scenarios 1-3, US2, FR-004, FR-005, Outcome; plan.md test table; tasks.md T006-T009. "Anywhere" is narrowed to the three texts the test reads (spec.md Assumptions) |
| Outcome bullet 4 (94-95) | Still to do at the next release: tag 0.3.1, move the sandbox's pin | Done the same day (`ATTIC/PLAN.md`; spec 002's Clarifications say the sandbox pinned 0.3.1), then superseded: spec.md Assumptions and Outcome; tasks.md T017, T018 |

## `ATTIC/PLAN.md`, "Collection stages"

| Source (lines) | What it says | Carried in |
| --- | --- | --- |
| Status (11-14) | "stages 3 and 4 executed 2026-11-14, 4 released as 0.3.1" | spec.md Status |
| Intro (16-20) | Stages planned one file each, executed on `do coll <n>` after decisions asked one at a time | spec.md Clarifications (the decisions, one at a time); the process itself is not carried (below) |
| Stage 4's line (37-39) | Say how to preview a long build; executed 2026-11-14; on `develop`; released as 0.3.1 with a fix, and the sandbox pins it | spec.md Status, Outcome, Assumptions |

## `ATTIC/COLL-INPROGRESS/COLL-STAGE-3.md`

| Source (lines) | What it says | Carried in |
| --- | --- | --- |
| Outcome, "Found about using `spack_env`" (304-309) | Ansible refuses async with check mode; a build wants `async`; the form for `async` and `poll`; the notes should say so, a documentation change for the next version | spec.md **Input**; research.md R1 (the finding and its Decision) |
| "What this stage is", last bullet (27-28) | The collection changes only if the move finds a defect, which would be fixed here, released as 0.3.1 and pinned there | Not carried: it is stage 3's plan and belongs to its retrospective. Spec 011 carries what happened: the defect came from stage 12, not stage 3, and was released as 0.3.1 with this work |

## Deliberately not carried

- **"do coll 4"** and the `do coll <n>` process: the trigger words of the
  retired planning process. Spec Kit's `/speckit-implement` replaces them,
  and nothing in the spec depends on them.
- **The link anchors** ("Decisions taken", "Outcome" as `#` links): the
  spec has its own sections.
- **The instruction "tag 0.3.1, then move the pin"** as an instruction: it
  is recorded as history and as done, not as work to do. The tag no longer
  exists, and the sandbox now installs 0.0.1 or later from Galaxy.
- **Stage 3's own plan** (the line above): stage 3's.

## Proposed row for `specs/README.md` (not written; the operator's call)

Retrospective specs are not yet in the index. If the operator wants them
there, a row in the style of the others:

| # | Spec | Converged | Serves | Ends in | State | Needs first | Branch | Tasks | Released in | Last converge check |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ? | [011 Say how to preview a long build](011-preview-long-builds/spec.md) | ❌ | a site that builds under `async` and previews with `--check` | a play copied from the documentation previewing without being refused, and an example with a plain number failing the unit tests | complete 2026-11-14 (retrospective, written 2026-11-27); released in the development version 0.3.1, withdrawn; in 0.0.1 ([tasks](011-preview-long-builds/tasks.md)) | nothing | `feature/coll-stage-4` (until the history reset of 2026-11-18) | 19 | 0.0.1 | never |

After this, `ATTIC/COLL-INPROGRESS/COLL-STAGE-4.md` adds nothing that spec
011 does not hold, except the four items listed as not carried.
