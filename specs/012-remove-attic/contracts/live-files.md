# Contract: what each live file says after the removal

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)

Nothing a playbook passes or receives changes, and nothing in the tarball
changes, because `ATTIC/` was never in it. What changes is what the
repository's rules, build and comments say.

| File | Before | After |
| --- | --- | --- |
| `ATTIC/` | six files of retired plans | gone from the working tree; in history up to the commit the index names |
| `.specify/memory/constitution.md` | section "The ATTIC"; `ATTIC/` in the tarball's exclusions; "retired to the ATTIC on 2026-11-17" | no section; not in the exclusions; the `PLAN.md` bullet says the plans made before Spec Kit are recorded in specs 007–011 and 001. Version 1.1.0 (proposed), Last Amended the date of the amendment |
| `CLAUDE.md` | the bullet "Nothing in ATTIC/ can affect you…" | no such bullet |
| `galaxy.yml` | `build_ignore`: `ATTIC`, under "…and what was retired" | no `ATTIC`; the comment reads "Planning and agent material: Spec Kit and its specs" |
| `Justfile` | the sanity tree leaves out `':!ATTIC'` | no `':!ATTIC'` |
| `plugins/module_utils/spack.py` | "see this repository's ATTIC/COLL-INPROGRESS/COLL-STAGE-2.md" | "see specs/009-setup-role/research.md, R7 to R9" |
| `tests/unit/fake_spack_setup.py` | "see ATTIC/COLL-INPROGRESS/COLL-STAGE-2.md" | "see specs/009-setup-role/research.md (R7 to R9, R12, R13, R16, R17)" |
| `CHANGELOG.md` | "Their plans are kept, as history only, in ATTIC/COLL-INPROGRESS/" (a link) | "Their plans are recorded in the specs 007 to 011 and 001" (links to them) |
| `specs/README.md` | a paragraph on work before Spec Kit | the same, saying the work before Spec Kit is in specs 007–011 and 001, and naming the last commit with `ATTIC/` (FR-006) |
| `specs/001`–`011`, `013` | rows and notes naming the ATTIC | as written: history (the spec's edge case) |
| `tests/unit/test_no_attic.py` (new, proposed) | — | fails if `ATTIC/` exists, or if a tracked file outside `specs/` and `CHANGELOG.md` contains the word `ATTIC` |

## Not changed

- The tarball's contents: `just build` gives the same files.
- Every module's options, returns and behaviour.
- Spec 012's coverage record, which names ATTIC files and line numbers as
  the record of what was there.
