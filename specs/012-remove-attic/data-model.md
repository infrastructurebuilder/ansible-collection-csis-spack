# Data model: the coverage record

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

There is no new data in the collection. The one structured thing this spec
makes is the coverage record that FR-001 asks for, in
[coverage/](coverage/).

## The record's files

| File | Covers | Into |
| --- | --- | --- |
| `coverage/README.md` (new) | the whole ATTIC, part by part: each part's record, and what is still open (nothing, or the item) | — |
| `coverage/007-first-modules.md` | `ATTIC/PLAN.md` lines 49–227, and lines 9–47 as context | spec 007 |
| `coverage/008-repeat-runs-say-so.md` | `COLL-STAGE-1.md`; `ATTIC/PLAN.md`'s stage-1 lines | spec 008 |
| `coverage/009-setup-role.md` | `COLL-STAGE-2.md`; `ATTIC/PLAN.md`'s stage-2 lines | spec 009 |
| `coverage/010-sandbox-adopts-setup.md` | `COLL-STAGE-3.md`; `ATTIC/PLAN.md`'s stage-3 lines | spec 010 |
| `coverage/011-preview-long-builds.md` | `COLL-STAGE-4.md`; `ATTIC/PLAN.md`'s stage-4 lines | spec 011 |
| `coverage/001-galaxy-publish.md` (new) | `COLL-STAGE-5.md`; `ATTIC/PLAN.md`'s stage-5 lines (13–15, 40–44) | spec 001 |
| `coverage/plan-header.md` (new) | `ATTIC/PLAN.md` lines 1–8, and anything of lines 9–47 that no record above places | the constitution's Development Workflow, and the index |

## A row of a record

Each record is a table, one row per paragraph, bullet, table row or block
of its source, in the source's order:

| Field | What it holds |
| --- | --- |
| Lines | the source's line numbers on 2026-11-27 |
| Source | what the lines say, in a few words |
| Carried in | the spec, file and section that holds it now, as a link; or **Not carried**, with the reason |

A reason for **Not carried** is one of:

- an anchor or a link within the ATTIC;
- a withdrawn version number;
- a pin that the history reset replaced;
- the Cloud Sandbox's work, recorded in that repository;
- the form of a decision prompt.

Each record ends with "Could not place", which lists the items with no
place, or says "nothing".

## States

| State | When |
| --- | --- |
| open | a part of the ATTIC has no record, or a record's "Could not place" lists something |
| complete | all seven parts have a record, and every "Could not place" says nothing |

`coverage/README.md` says which state the record is in. The removal (FR-003)
waits for "complete".
