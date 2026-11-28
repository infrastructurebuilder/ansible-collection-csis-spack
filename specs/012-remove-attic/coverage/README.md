# Coverage of the ATTIC: where each part of it went

This is the record that spec 012's FR-001 asks for. It is kept before
`ATTIC/` is removed, and it stays as the record of what was there. For the
operator and for a reader; not part of the spec.

The ATTIC held six files of plans made before this repository adopted Spec
Kit (2026-11-13 to 2026-11-17): 1414 lines in all. They are counted below as
eight parts, because `ATTIC/PLAN.md` falls into three. Each part has a record
in this directory, seven records in all, and each record maps the part
paragraph by paragraph, or line by line, to the spec, file and section that
now carries it, or gives the reason it is not needed.

**State: complete** (2026-11-28). Every part has a record, and every
record's "Could not place" says nothing.

## The parts, and their records

| # | Part of the ATTIC | Lines | Carried by | Record |
| ---: | --- | ---: | --- | --- |
| 1 | `ATTIC/PLAN.md` lines 1–8, the header ("This file is closed…") | 8 | the constitution's Development Workflow; [CLAUDE.md](../../../CLAUDE.md); [specs/README.md](../../README.md) | [plan-header.md](plan-header.md) |
| 2 | `ATTIC/PLAN.md` lines 9–47, "Collection stages" (the index of the five stage plans) | 39 | specs 008–011 and 001, a line each | [plan-header.md](plan-header.md), which checks every line against the records below |
| 3 | `ATTIC/PLAN.md` lines 49–227, "The first modules" (2026-11-13, released as 0.1.0) | 179 | [spec 007](../../007-first-modules/spec.md) | [007-first-modules.md](007-first-modules.md) |
| 4 | `ATTIC/COLL-INPROGRESS/COLL-STAGE-1.md`, repeat runs that do nothing and say so | 209 | [spec 008](../../008-repeat-runs-say-so/spec.md) | [008-repeat-runs-say-so.md](008-repeat-runs-say-so.md) |
| 5 | `ATTIC/COLL-INPROGRESS/COLL-STAGE-2.md`, the `setup` role | 425 | [spec 009](../../009-setup-role/spec.md) | [009-setup-role.md](009-setup-role.md) |
| 6 | `ATTIC/COLL-INPROGRESS/COLL-STAGE-3.md`, the Cloud Sandbox moves to the `setup` role | 317 | [spec 010](../../010-sandbox-adopts-setup/spec.md) | [010-sandbox-adopts-setup.md](010-sandbox-adopts-setup.md) |
| 7 | `ATTIC/COLL-INPROGRESS/COLL-STAGE-4.md`, previewing a long build | 96 | [spec 011](../../011-preview-long-builds/spec.md) | [011-preview-long-builds.md](011-preview-long-builds.md) |
| 8 | `ATTIC/COLL-INPROGRESS/COLL-STAGE-5.md`, Ansible Galaxy | 140 | [spec 001](../../001-galaxy-publish/spec.md) | [001-galaxy-publish.md](001-galaxy-publish.md) |

Line 48 of `ATTIC/PLAN.md` is blank. The parts' lines add up to 1413, and
the blank line makes the 1414.

## What the records left open, and where each was settled

| Record | Its open items | Settled |
| --- | --- | --- |
| [007](007-first-modules.md) | Four places where the old plan and the code as built disagree (what was pushed; options and returns the plan did not list; how module roots were read in 0.1.0; check mode and module files) | Each carried as built, in spec 007 (FR-009, Assumptions, research R4–R6, a *Changed later* note on FR-005). "Nothing left unplaced" |
| [008](008-repeat-runs-say-so.md) | Six disagreements (`force: true`'s warning; the second-naming-scheme test; roots on Spack 1.0; "v1.2.0 only"; `version_added`; the README's summary of `when_needed`) | Each carried as built in spec 008, or noted there. "Could not place: nothing" |
| [009](009-setup-role.md) | Six disagreements (`config remove` and an emptied mapping; a different mirror; the site-mirror example; the test's key; the two `compiler find` steps; the role's variables), and three live files that pointed into the ATTIC | The disagreements carried as built in spec 009. The live files are spec 012's FR-005: `plugins/module_utils/spack.py`, `tests/unit/fake_spack_setup.py` and `CHANGELOG.md` now cite the specs |
| [010](010-sandbox-adopts-setup.md) | "Added, not from the source": a list for the operator | Nothing open |
| [011](011-preview-long-builds.md) | A proposed row for `specs/README.md` | The index has held spec 011's row since 2026-11-27 |
| [001](001-galaxy-publish.md) | Three disagreements (the first version; the workflow's tag; "it has not run") | Each carried as built in spec 001 (FR-013, Clarifications of 2026-11-18, Outcome). "Could not place: nothing" |
| [plan-header](plan-header.md) | None | "Could not place: nothing" |

## Why nothing is lost

The ATTIC's own rule (the constitution's former section on retired plans)
was that nothing in it could guide work, only the specs. Every part of it
that still mattered was carried into a spec when the spec was written, and
the records above show where. What was left out falls under one of a few
reasons ([../data-model.md](../data-model.md)):
- anchors and links within the ATTIC;
- withdrawn version numbers;
- pins that the history reset replaced;
- the Cloud Sandbox's own work, recorded in its repository;
- the form of the decision prompts.

The files themselves can still be read in git, at the commit that
[specs/README.md](../../README.md) names below its table.
