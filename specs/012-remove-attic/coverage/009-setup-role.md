# Coverage of `ATTIC/COLL-INPROGRESS/COLL-STAGE-2.md` by spec 009

For the operator; not part of the spec. Each row is a paragraph, bullet,
table row or block of the source (line numbers of the file as it is on
2026-11-27, 425 lines), and where it is now carried. "spec" is
`specs/009-setup-role/spec.md`, and so on for the spec's other files.

## The source, part by part

| Source (lines) | What it says | Carried in |
| --- | --- | --- |
| Status (3-10) | Planned 2026-11-14, revised the same day so the collection prescribes nothing; executed on "do coll 2" on `feature/coll-stage-2`; merged, released as 0.3.0 and pushed on the operator's word | spec: Status, Feature Branch, Input; Clarifications (the revision); tasks T001, T003, T050, T052 |
| Why (14-17) | 0.1.0 covers environments; set-up is still bash in the sandbox | spec: Why, first paragraph |
| Why table, row 1 (21) | `roles/spack/tasks/main.yml` L92-L119: commands, fingerprint by `spack python -c` and hashing, `grep` guard, no check mode | spec: Why, table row 1 |
| Why table, row 2 (22) | `roles/intel_oneapi`: `compiler find` with modules, YAML appended, five `config add`, keys; "undo each other"; a changed version never corrected | spec: Why, table row 2 (with a pointer to research R16, which found "undo each other" untrue) |
| Why table, row 3 (23) | `spack-pubkey.sh` by hand | spec: Why, table row 3 |
| Why, last paragraph (25-29) | The first plan's workflows would have built the sandbox's choices in | spec: Why, paragraph after the table; Clarifications (the revision); research Decisions #1 |
| The principle (33-38) | The collection knows how, not what; empty defaults; one list = the script as data | spec: Why, "The principle"; plan: Constitution Check, I |
| Principle bullets (40-47) | Each kind a module that tells change and previews; the order is the site's; anything else as a plain command | spec: "The principle", three bullets |
| Principle, nature (49-57) | Declared state vs discovery | spec: "The principle", last two bullets; data-model: "The kinds", what each nature means; US3 |
| Offers: `config get --json` (61-64) | One scope or merged; tried `{"mirrors":{}}`; replaces `spack python -c` | research R1 |
| Offers: `config add`/`remove` (65-66) | | research R2 |
| Offers: compilers (67-69) | `compiler find/list/remove`; a compiler is a package since 1.0 | research R3 |
| Offers: `external find` (70-71) | Its options | research R3 |
| Offers: mirrors (72-73) | `mirror add/set/remove/list` | research R4 (with the as-built difference: no `mirror set`) |
| Offers: keys (74-75) | `gpg trust`, `gpg list`, `buildcache keys` | research R5 |
| Offers: scopes (76-78) | Lowest to highest | research R6 |
| Item 1, intro (82-84) | Each kind a module usable alone; `spack` and `scope` | spec: US4, FR-007; contracts: "The modules, by kind" |
| Item 1 table: `spack_config` (88) | settings, present/absent, merge/replace; compare as data; list paths; check mode | spec FR-001; contracts `config`; research R8 (replace a key at a time) |
| Item 1 table: `spack_mirror` (89) | Missing: add; different: `mirror set`; says which | spec FR-002; contracts `mirror`; research R4 and plan "What changed" (removed and added, not `mirror set`) |
| Item 1 table: `spack_gpg_key` (90) | key with fingerprint, or from_mirrors; public only; change and check mode | spec FR-003; contracts `gpg_key`; research R13 |
| Item 1 table: `spack_detect` (91) | compilers, externals, not_buildable, exclude, paths, require; change as data; check mode | spec FR-004; contracts `detect`; research R16, R17 |
| Item 1 table: `spack_command` (92) | args; changes config/creates/always/never; check mode | spec FR-005; contracts `command` |
| Item 1, environment (94-95) | Environment from the task's `environment:`; none runs a shell | spec FR-007 |
| Item 1, decision (97-101) | Include `spack_command`? | spec: Clarifications, Q1 |
| Item 2, intro (103-106) | One variable, `spack_setup`; the role; defaults empty | spec FR-008; data-model: "The role's variables" |
| Item 2, decision (108-114) | List or fixed mapping? | spec: Clarifications, Q2 |
| Item 2, first YAML list (116-139) | The sandbox's `roles/spack` as a list | `docs/examples/cloud-sandbox.yml`, `spack_setup_base` (with `scope: user` on its settings step, research R20; `spack_setup_executable` for the plan's `spack_setup_spack`, spec 002); plan: "What changed" (two variables) |
| Item 2, second YAML list (141-175) | The sandbox's `roles/intel_oneapi` as a list | `docs/examples/cloud-sandbox.yml`, `spack_setup_intel` |
| Item 2, paragraph (177-180) | Every name is the sandbox's; `require` stops the accident | spec US2, FR-015; research R16 |
| Item 2, bullet: `name` (182-183) | A step's name in the output | spec FR-010 (built as `label`; plan "What changed") |
| Item 2, bullet: check first (184-187) | `meta/argument_specs.yml` and the kinds' checks; stop with the step's number, nothing changed | spec FR-011, FR-020; US1 scenario 3; research R21 |
| Item 2, bullet: results (188-189) | One line per step | spec FR-012; data-model: "The results" |
| Item 2, bullet: twice (190-192) | Apply twice with two lists; no state kept | spec FR-014; Edge Cases |
| Item 3 (194-206) | The environment decision | spec: Clarifications, Q3; FR-013 |
| Item 4, intro (208-211) | Examples as tested data | spec US5, FR-016 |
| Item 4 table, 7 rows (213-221) | What each example's list does | data-model: "The examples" (with where the examples differ from the plan's rows: toolset, unwanted compilers, site mirror) |
| Item 4, paragraph (223-230) | Each example applied by unit tests; the sandbox's held to its shell on a second stand-in; commands need not be identical | spec FR-016, FR-017, US5 scenario 2; tasks T039, T040 |
| Item 5, intro (232-234) | Tried first, on the local machine and the sandbox's container | research: opening paragraph |
| Item 5, four bullets (235-243) | When `compiler find` removes; round-trip and `mode: replace`; `gpg list --trusted`; `external find` and oneAPI | research: opening paragraph (the four questions and where each is answered); R7 (round-trip: no separate finding recorded) |
| Item 5, last line (245) | Findings recorded before the modules are written | research: opening paragraph; tasks Phase 2 |
| Item 6, bullet 1 (248-253) | Unit tests against the extended stand-in, and what they cover | spec SC-005; plan: Tests; tasks T010, T011-T016, T024, T025, T032, T036 |
| Item 6, bullet 2 (254-256) | The test for site knowledge | spec FR-015, SC-001; tasks T041 |
| Item 6, bullet 3 (257-259) | Integration against the real Spack: first example, a mirror in a directory, a key generated for the test; applied twice | plan: Tests (as built: a list of every kind, a directory mirror, the throwaway key fixture rather than a generated one); tasks T046 |
| Item 6, bullet 4 (260-262) | oneAPI proved in the sandbox's container; no compiler installed by the collection | spec: Assumptions, SC-004 |
| Item 7 (264-266) | Version decision | spec: Clarifications, Q4 |
| Decisions taken (268-276) | One at a time; four defaults taken | spec: Clarifications |
| Tried, intro (280-282) | Where: local machine; the container (AlmaLinux 10, oneAPI 2024.2.1 from dnf, Spack v1.2.0), kept then removed | research: opening paragraph |
| Configuration, bullet 1 (286-287) | One section per file; JSON | research R7 |
| Configuration, bullet 2 (288-291) | Lists merged; scalar replaced; remove first | research R8 |
| Configuration, bullet 3 (292-293) | `remove` of a missing path succeeds; last key removes the mapping | research R9 (the second half marked wrong, corrected in 0.3.1, spec 011) |
| Configuration, bullet 4 (294-296) | Schema refuses; module puts back | research R10; spec Edge Cases |
| Configuration, bullet 5 (297-300) | User scope with no directory; read as empty; found by the integration test | research R11; spec Edge Cases; tasks T046 |
| Mirrors and keys, bullet 1 (304-306) | Bare URL vs mapping; both types; adding twice fails | research R12 |
| Mirrors and keys, bullet 2 (307-311) | `gpg trust` asks without `-y`; exit 0 for no key; read `gpg list --trusted --fmt colons`; `gpg --show-keys` | research R13; spec Edge Cases |
| Mirrors and keys, bullet 3 (312) | `--fmt keys` runs them together | research R14 |
| Mirrors and keys, bullet 4 (313-314) | gpg agent socket path | research R15 |
| Detection, bullet 1 (318-324) | Never removes; "undo each other" not reproduced; the quiet half | research R16; spec Why (table, row 2), US2 |
| Detection, bullet 2 (325-326) | `packages.yaml` reordered | research R17; spec Edge Cases |
| Detection, bullet 3 (327-328) | `external find` misses dnf oneAPI MKL and MPI | research R18; `docs/examples/cloud-sandbox.yml` (its comment) |
| Detection, bullet 4 (329) | `compiler remove` adds an `id` | research R19; spec SC-004 |
| The sandbox's own script (333-338) | `config add` without `--scope` writes the user scope; the example says `scope: user` | research R20; spec Edge Cases; `docs/examples/cloud-sandbox.yml` (its comment) |
| What changed: `label` (342-343) | | spec FR-010; plan "What changed"; tasks T030 |
| What changed: `mode: replace` (344-345) | | spec FR-001; research R8; plan "What changed" |
| What changed: environment as a mapping (346-347) | | spec FR-013, Clarifications Q3; plan "What changed" |
| What changed: no `argument_specs` (348-352) | The ansible-core 2.16.20 warning; the first task checks; README documents the three variables | spec FR-020; research R21; plan "What changed"; tasks T027 |
| What changed: neutral examples of 0.1.0's modules (353-355) | | spec FR-018; plan "What changed"; tasks T042 |
| What changed: test time (356-357) | Two to three minutes; 193 tests | spec Assumptions, Status; plan Technical Context and "What changed" |
| Out of scope: the Cloud Sandbox (361-367) | Its lists become its roles' variables; shell tasks, `spack_fingerprint`, `spack_config_json` go; `spack-pubkey.sh` a third list; its container test | spec Out of Scope, first bullet (with a pointer to spec 010) |
| Out of scope: installing Spack or compilers (368-369) | | spec Out of Scope (noting spec 004 later added the install step) |
| Out of scope: per-user configuration (370-372) | | spec Out of Scope |
| Out of scope: private keys, signing (373) | | spec Out of Scope; FR-003 (public keys only) |
| Out of scope: a fork of Spack (374-376) | | spec Out of Scope |
| Acceptance, 4 bullets (380-387) | Tests pass; defaults empty and site-knowledge test; sandbox example vs shell; real Spack twice and check mode | spec SC-001 to SC-003, Status; tasks T047-T049 |
| Outcome: modules (391-393) | Six modules; shared code | plan: Summary, Design; Project Structure |
| Outcome: role (394-396) | Empty defaults; `tasks/kinds/<kind>.yml`; the two filters | plan: Design, "The role", "The filters" |
| Outcome: examples (397-398) | Seven, each on a stand-in machine | spec FR-016, SC-006; data-model "The examples" |
| Outcome: no site knowledge (399-402) | What the test takes out; caught one on its first run | spec FR-015, SC-001; tasks T041 |
| Outcome: sandbox vs shell on a stand-in (403-406) | | spec FR-017, SC-002; tasks T040 |
| Outcome: with the real oneAPI (407-416) | Dumped and wiped; 7, 0, 0; the `id` difference; a trial by hand | spec SC-004; research R19; plan Tests; tasks T051 |
| Outcome: tests (417-424) | 193 unit tests; the integration test's checks; `just test` and `just full-test` pass, sanity included | spec Status, SC-005; plan Testing, Tests; tasks T046-T048 |
| `ATTIC/PLAN.md`, "Collection stages", the stage-2 bullet (lines 27-31) and its Status (lines 10-15) | An ordered list of steps, each a module, carried out by a role that knows nothing about any site; released as 0.3.0 the same day as stage 1's 0.2.0 | spec: Status, Why, "The principle" |

## Not carried, and why

- **The detailed work of using the role in the Cloud Sandbox** (lines
  361-367, beyond the out-of-scope bullet): it is the Cloud Sandbox's work,
  recorded in that repository and in the retrospective spec 010. The bullet
  itself is carried, as out of scope.
- **The sandbox's two YAML lists verbatim** (lines 119-175): not copied into
  the spec, because `docs/examples/cloud-sandbox.yml` holds them, tested,
  with the differences named in plan.md "What changed". Copying them would
  give two versions to keep the same.
- **The anchors** ("see Decisions taken", "see Outcome", lines 8-10): links
  within the source; nothing to carry.

Nothing else in the source was left out.

## Live files that still point into the ATTIC

The operator may want these changed before `ATTIC/` is deleted, so that no
live file points at a file that is gone:

- `plugins/module_utils/spack.py`, the comment above "Configuration, as
  data" (line 423): "see this repository's
  ATTIC/COLL-INPROGRESS/COLL-STAGE-2.md". Its findings are now research R7
  to R9 here.
- `tests/unit/fake_spack_setup.py`, its docstring (line 4): "see
  ATTIC/COLL-INPROGRESS/COLL-STAGE-2.md". Now research R7 to R9, R12, R13,
  R16, R17 here.
- `CHANGELOG.md`, "Before 0.0.1" (line 180): a link to
  `ATTIC/COLL-INPROGRESS/`. That is the whole ATTIC's, not this spec's
  alone.

## Where the source and the code disagree

- **`config remove` and an emptied mapping** (source line 292-293): the
  source says removing a mapping's last key removes the mapping. Spack
  v1.2.0 leaves it behind, empty; corrected in 0.3.1 (spec 011). Carried in
  research R9 with the correction; spec FR-001 notes it.
- **A different mirror** (source line 89): the source says `mirror set`. The
  code, as released in 0.0.1 and today, removes the mirror and adds it again
  (`replaced`). Carried in research R4 and plan "What changed".
- **The site-mirror example** (source line 220): the source lists a final
  `gpg_key` with `from_mirrors`; the example ends with a `command` step
  instead. Carried in data-model "The examples".
- **The integration test's key** (source line 258): "a key generated for the
  test"; the test, as released in 0.0.1, uses a throwaway key kept in
  `tests/fixtures/`. Carried in plan "Tests".
- **"The two `compiler find` steps undo each other"** (source line 22): the
  source itself found this untrue (line 318-324). Carried in spec Why with
  the pointer to research R16.
- **The role's variables**: the source names `spack_setup_spack` and "the
  three variables"; today there are four (`spack_setup_yes_to_all`, spec
  003) and the executable is `spack_setup_executable` (spec 002). Carried as
  notes in spec FR-008 and data-model.
