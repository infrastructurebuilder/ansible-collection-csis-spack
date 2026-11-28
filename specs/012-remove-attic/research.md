# Research: Remove the ATTIC, because the specs hold everything in it

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Done on 2026-11-27 on `feature/remove-attic`, with `develop` (455b053)
merged in. The ATTIC was read on the operator's word of 2026-11-27 ("It's
OK to read ATTIC/ to create these specs"), for this spec only.

## R1. What the existing coverage records leave out

The ATTIC holds six files (1414 lines):

| File | Lines | Covered by |
| --- | ---: | --- |
| `ATTIC/PLAN.md` | 227 | lines 49–227, "The first modules": [coverage/007-first-modules.md](coverage/007-first-modules.md). Lines 9–47, "Collection stages": each stage's bullet and the section's Status and intro, in the records for 007, 008, 009, 010 and 011. **Not yet covered:** lines 1–8 (the "closed" header) and the stage-5 lines (13–15, 40–44). |
| `ATTIC/COLL-INPROGRESS/COLL-STAGE-1.md` | 209 | [coverage/008-repeat-runs-say-so.md](coverage/008-repeat-runs-say-so.md) |
| `ATTIC/COLL-INPROGRESS/COLL-STAGE-2.md` | 425 | [coverage/009-setup-role.md](coverage/009-setup-role.md) |
| `ATTIC/COLL-INPROGRESS/COLL-STAGE-3.md` | 317 | [coverage/010-sandbox-adopts-setup.md](coverage/010-sandbox-adopts-setup.md) |
| `ATTIC/COLL-INPROGRESS/COLL-STAGE-4.md` | 96 | [coverage/011-preview-long-builds.md](coverage/011-preview-long-builds.md) |
| `ATTIC/COLL-INPROGRESS/COLL-STAGE-5.md` | 140 | **No record.** Carried as the spec [001-galaxy-publish](../001-galaxy-publish/spec.md), which was made from it on 2026-11-17, but never mapped line by line. |

**Stage 5 against spec 001, spot-checked.** Each of these is found in spec
001's `spec.md`, `plan.md` or `tasks.md`:

- the comparison of a git tag and Galaxy, and version ranges;
- the two decisions (publish; from both the operator's machine and a
  workflow);
- the change to the plan (the first upload is the next release, not 0.3.1);
- `just import-check`, `tools/publish.py` and the refusal of a version
  already there;
- the workflow's `galaxy` environment, and `tests/unit/test_publish.py`;
- ruff's 73 pylint rules and the two it cannot check (`disallowed-name`,
  `dangerous-default-value`);
- the Cloud Sandbox's `requirements.yml` and `units.toml`;
- the out-of-scope item, and the acceptance on a clean machine.

One item is not found: lines 9–12, why stage 5 came before the Cloud
Sandbox's relocation (a relocated `sandbox-provisioning` names the
collection's source in its `requirements.yml`). That is the Cloud Sandbox's
ordering, recorded in its own `PLAN.md`, so it is "not needed here".

**Decision:** the coverage record gains two files: one for
`COLL-STAGE-5.md` into spec 001, line by line like the others, and one for
`ATTIC/PLAN.md` lines 1–8 and the stage-5 lines. A `coverage/README.md`
names all eight parts (in seven records) and the record for each, so that FR-001 and SC-001 can
be checked from one page. If the line-by-line pass finds anything of stage 5
that spec 001 does not hold and that is still wanted, it is carried into
spec 001 first (the spec's first edge case).

## R2. What the existing records left open

Each record ends with what it could not place, or where the source and the
code disagree:

- **007, 008, 009:** every "disagree" item was carried as the code was built,
  with a note in the retrospective spec; "Could not place: nothing".
- **009:** it lists three live files that point into the ATTIC
  (`plugins/module_utils/spack.py` line 423, `tests/unit/fake_spack_setup.py`
  line 4, `CHANGELOG.md`), which FR-005 covers.
- **010:** "Added, not from the source" is a list for the operator; nothing
  is open.
- **011:** a proposed row for `specs/README.md`, which the index has held
  since 2026-11-27.

**Decision:** nothing open blocks the removal. `coverage/README.md` says so,
item by item.

## R3. Which live files name the ATTIC

A search of every file outside `ATTIC/` and `.git/` (2026-11-27):

| File | What it says | Kind |
| --- | --- | --- |
| `.specify/memory/constitution.md` | the section "The ATTIC" (lines 110–135); `ATTIC/` in the tarball's exclusions (148); "retired to the ATTIC on 2026-11-17" under Development Workflow (171–172) | a rule |
| `CLAUDE.md` | line 14, the bullet "Nothing in ATTIC/ can affect you…", with a link | a rule |
| `galaxy.yml` | `build_ignore`: `ATTIC` (line 44), under the comment "…and what was retired" | build |
| `Justfile` | line 64, the sanity tree's `':!ATTIC'` | build |
| `plugins/module_utils/spack.py` | line 423, a comment citing `ATTIC/COLL-INPROGRESS/COLL-STAGE-2.md` | comment; its findings are spec 009's research R7–R9 |
| `tests/unit/fake_spack_setup.py` | line 4, the docstring citing the same file | comment; spec 009's research R7–R9, R12, R13, R16, R17 |
| `CHANGELOG.md` | line 208, a link to `ATTIC/COLL-INPROGRESS/` | history |
| `specs/001`–`011`, `013` | Constitution Check rows ("The ATTIC: not consulted"), Input lines, coverage notes | history (the spec's edge case: left as written) |
| `specs/012-remove-attic/` | this spec, its checklist and its coverage record | this spec |
| `specs/README.md` | the paragraph on work before Spec Kit | the index |

Only two of these are markdown links that would break: `CLAUDE.md` and
`CHANGELOG.md`. The specs name ATTIC files as text, not as links. No test
holds `ATTIC` in `build_ignore` (`tests/unit/test_publish.py` checks only
`tools`, `.github` and `.envrc`), and no workflow names it.

## R4. Git history

`ATTIC/` was last changed in 7a42380 ("Init", the history reset of
2026-11-18). Removing it from the working tree leaves every version in
history. The commit to name in the index (FR-006) is the last one that
still has `ATTIC/`: the parent of the removal commit, whose hash is known
only once the removal is committed. So the index's note is written in the
same task as the removal, and it is checked with
`git show <that commit>:ATTIC/PLAN.md`.

## R5. The constitution's amendment

The constitution's Governance section ties the version to what changes:
MAJOR when a principle is removed or redefined so that earlier work would
break it; MINOR when a principle or section is added or materially widened;
PATCH for wording. The amendment would:

- remove the section "The ATTIC", which is not one of the five principles;
- drop `ATTIC/` from the tarball's exclusions under Technical Constraints;
- reword the "There is no `PLAN.md`" bullet, which says the old one "was
  retired to the ATTIC".

No earlier work breaks, so this is not MAJOR. A whole section is removed,
which is more than wording, so it is not PATCH either. Governance names no
level for a removal; MINOR is the nearest, for a material change that is not
a principle's. **Proposed: 1.0.1 → 1.1.0.** This is the operator's call
(plan, "Decisions to confirm").

The amendment goes through `/speckit-constitution` on the operator's
instruction (FR-004). The "what changed and why" it must record is kept in
this spec's tasks and in the commit, so that the constitution's own text
does not name the ATTIC again (SC-002).

## R6. Holding SC-002 with a test

Principle IV asks that what the work promises be held by a test where it
can be. SC-002 can be: a unit test that `ATTIC/` does not exist, and that
no tracked file outside `specs/` and `CHANGELOG.md` contains the word
`ATTIC`. Like `tests/unit/test_no_site_knowledge.py`, it uses `git ls-files`.
It fails if the directory comes back, or if a rule or comment starts
pointing at it again.

**Decision (to confirm):** add it, as
`tests/unit/test_no_attic.py`.

## Decisions

| # | Decision | Alternatives considered |
| --- | --- | --- |
| 1 | Complete the coverage record with stage 5 and `ATTIC/PLAN.md` lines 1–8, and gather all eight parts, in seven records, in `coverage/README.md` (R1, R2) | Rely on spec 001 having been made from stage 5: SC-001 asks for zero items unaccounted, which only a record shows |
| 2 | Name the last commit holding `ATTIC/` in the same task as the removal (R4) | Name it beforehand: its hash is not known until the removal is committed |
| 3 | Constitution 1.0.1 → 1.1.0, with the change recorded outside its text (R5); the operator decides | 2.0.0: no principle is removed; 1.0.2: a section's removal is more than wording |
| 4 | A unit test holds SC-002 (R6) | A one-off search in the quickstart: it would not stop the ATTIC coming back |
