# Coverage: `ATTIC/COLL-INPROGRESS/COLL-STAGE-3.md` into spec 010

For the operator, not part of the spec. Every paragraph, bullet and table row
of the source, and its line in `ATTIC/PLAN.md`, with where it is now carried.
Line numbers are the source file's. "CS" means the item is Cloud-Sandbox's
work: it is recorded in the spec as a hand-off, and its full record is
Cloud-Sandbox's `INPROGRESS/STAGE-11.md` and `exportit/MAP.md`.

## The stage file

| Source (lines) | What it says | Carried in |
| --- | --- | --- |
| Title (1) | Stage 3: the Cloud Sandbox moves to 0.3.0 | spec.md title, Input; plan.md Summary |
| *Status* (3-8) | Planned 2026-11-14 on `feature/coll-stage-3`; decisions asked the same day; executed on "do coll 3" in Cloud-Sandbox on `feature/stage-11-csis-spack-0.3.0`; committed locally in both, nothing merged or pushed; the collection did not change | spec.md Feature Branch, Created, Status, Input; plan.md Branch line; tasks.md T001, T004, T028 |
| What this stage is (12-17) | Stages 1 and 2 changed the collection; this one changes its first user, `sandbox-provisioning` under `exportit/`, pinned at 0.1.0, still bash; kept here because it proves 0.2.0 and 0.3.0 | spec.md Why (first and last paragraphs) |
| Bullet (19-23) | Changes made in Cloud-Sandbox on its branch, under its rules: copies byte-identical, traceability to `funcs-setup-instance.sh`, its root `just test` / `just full-test`, nothing pushed to IOOS | spec.md FR-018, SC-007, US4; plan.md Technical Context, Constraints |
| Bullet (24-26) | Cloud-Sandbox records it as stage 11: `INPROGRESS/STAGE-11.md`, a row in `TODO.md` | spec.md Clarifications (sixth Q), FR-018; tasks.md T004, T025 |
| Bullet (27-28) | The collection changes only for a defect; fixed here, released as 0.3.1, pinned there | spec.md FR-007; research.md R1, Decisions row 1 |
| Why, intro (32-33) | `sandbox-provisioning` uses `spack_env` from 0.1.0 (sandbox's stage 10) | spec.md Why, first bullet |
| Why, 0.2.0 (35-38) | Module files regenerated only when needed; the role passes `modules: [tcl]` only, so the pin changes behaviour | spec.md Why, first bullet; US2 |
| Why, 0.3.0 (39-41) | Can replace one task in `spack`, three in `intel_oneapi`, each hashing the configuration through `spack python -c` | spec.md Why, second bullet |
| Why, stage 2 (42-43) | Three things about the sandbox its records miss or get wrong | spec.md Why, third bullet; research.md R6-R8 |
| What exists: the pin (49) | `requirements.yml`, `units.toml`, the `exportit/tools` test; 0.1.0 | plan.md "What was done where" table; spec.md FR-009 |
| What exists: the environment (50) | `roles/spack_environment/tasks/main.yml`, no `refresh_modules` | plan.md table; FR-010 |
| What exists: setting Spack up (51) | `roles/spack/tasks/main.yml` L92-L119, `funcs-setup-instance.sh` L661-L700 | plan.md table; FR-011 |
| What exists: the Intel part (52) | `roles/intel_oneapi/tasks/main.yml`, three tasks and their lines | plan.md table; FR-013 |
| What exists: the fingerprint (53) | `group_vars/all.yml` `spack_config_json`, `spack_fingerprint`; `verify.yml` | plan.md table; FR-014 |
| What exists: parity tests (54) | `tests/test_parity.py`, its two tests | plan.md table; FR-015 |
| What exists: traceability (55) | `tests/test_traceability.py`, `tests/not_carried.yml` | plan.md table; FR-015 |
| What exists: container test (56) | `converge.sh` twice with real oneAPI; `verify.yml` greps | plan.md table; FR-016 |
| What exists: site mirror's key (57) | `sandbox-ops/bin/spack-pubkey.sh`, byte-identical, steps commented out | plan.md table; spec.md Clarifications (fifth Q) |
| Stage 2 found, intro (59) | To be acted on or recorded | research.md opening paragraph |
| Finding 1 (61-65) | The two `compiler find` steps do not undo each other; detection never removes (v1.2.0) | research.md R6; spec.md Edge Cases; FR-011; tasks.md T009, T023 |
| Finding 2 (66-68) | `config add` without `--scope` writes the user scope; the padding and Tcl modules are only there | research.md R7; spec.md Clarifications (third Q) |
| Finding 3 (69-70) | `external find` does not detect the dnf MKL and MPI; they stay declared | research.md R8 |
| Item 1 (74-76) | Pin to 0.3.0; `just init` installs; container and first-boot template already install `requirements.yml` | spec.md FR-009; plan.md (sentence after the table); tasks.md T005 |
| Item 2 (78-80) | `spack_env` gets `refresh_modules`, with a comment on the difference | spec.md FR-010, US2; tasks.md T006 |
| Item 2, decision (82-86) | `when_needed` (default) or `always` | spec.md Clarifications (first Q) |
| Item 3 (88-94) | Shell task becomes one `include_role`, `apply` as login user, same `when`, the example's `spack_setup_base` with the sandbox's variables | spec.md FR-011, US3; tasks.md T008 |
| Item 3, bullet (95-97) | Conditional loading of Intel modules goes; comment replaced | spec.md FR-011; tasks.md T009 |
| Item 3, bullet (98) | `buildcache keys` needs the network | spec.md Edge Cases |
| Item 3, decision (100-105) | Lists as `vars:` in tasks files, or in `defaults/main.yml` | spec.md Clarifications (second Q) |
| Item 3, decision (107-113) | Scope user (default) or site, noted in step and `not_carried.yml` | spec.md Clarifications (third Q) |
| Item 4 (115-121) | Second list from four variables; environment step runs two shell variables; detect requires `intel-oneapi-compilers@{{ oneapi_version }}` | spec.md FR-013, FR-003, Edge Cases; tasks.md T011 |
| Item 4, bullet (122-123) | `intel_oneapi_spack_packages_file` goes | spec.md FR-013; tasks.md T012 |
| Item 4, bullet (124-126) | A changed external is now corrected; the here-document skipped it | spec.md Edge Cases; research.md R9 |
| Item 5 (128-130) | Fingerprint variables go; `verify.yml` uses `spack config get --json` | spec.md FR-014, SC-004; tasks.md T013 |
| Item 6, traceability (133-136) | `# Replaces` / `# New:` per step; every line replaced or not carried | spec.md FR-015, SC-005; tasks.md T014 |
| Item 6, parity (137-145) | Parity test reads the script's commands (L661-L700, L919-L959), command for step, in order | spec.md FR-015; tasks.md T015 |
| Item 7 (147-149) | Container from a fresh clone, so first application is both lists | spec.md FR-016; research.md R5 |
| Item 7, bullet (150) | Applied twice; second changes nothing | spec.md FR-006, FR-016, US1 AS2 |
| Item 7, bullet (151-156) | `verify.yml` compares data per scope; `spack compiler list` | spec.md FR-016; tasks.md T016 |
| Item 7, bullet (157) | Check mode after the second run, no change | spec.md FR-006, US1 AS3 |
| Item 7, decision (159-165) | Side-by-side proof with `expected-spack-config.json`, or `verify.yml` alone | spec.md Clarifications (fourth Q) |
| Item 8, decision (167-176) | Leave `spack-pubkey.sh`, or a third list `spack_setup_site_mirror` | spec.md Clarifications (fifth Q) |
| Item 9 (178-186) | Records: `MAP.md` (four points), `STAGE-11.md`, `TODO.md`, `README.md` | spec.md FR-018; tasks.md T023-T025 |
| Decisions taken, intro (190) | Asked one at a time, 2026-11-14, before execution | spec.md Clarifications (session line); plan.md Constitution Check V |
| Decisions 1-6 (192-204) | `when_needed`; tasks files; site (after the scope question); yes; third list off by default; stage 11 | spec.md Clarifications, six Qs in order, with the operator's question nested under the third |
| Changes, item 3 (208-216) | First step has no `scope`; comment `L672-L673`; `not_carried.yml`; `MAP.md`; parity holds scope to `site` | spec.md FR-012; tasks.md T010, T015 |
| Changes, item 3, sub-bullet (217-221) | Older head nodes keep the settings in the user scope; not removed; `MAP.md` says so | spec.md Edge Cases, FR-012, Out of Scope; tasks.md T023 |
| Changes, item 7 (222-228) | `expected-spack-config.json` dumped before, unedited; exactly one stated difference | spec.md FR-016; tasks.md T007, T016 |
| Changes, item 8 (229-232) | Third list in the `spack` role, second `include_role`, `spack_site_mirror` false by default | spec.md FR-017; tasks.md T017 |
| Changes, item 8, steps (233-240) | `gpg_key` with URL and `spack_key_fingerprint` (the `.pub` file's name); `mirror` `s3-mirror`; `gpg_key` `from_mirrors`; `# Replaces scripts/spack-pubkey.sh L<n>` | spec.md FR-017; plan.md "The third list, as planned" (the key file's name) |
| Changes, item 8, `spack_key` (241-242) | `spack_key` goes | plan.md "The third list, as planned"; the outcome (it stays): spec.md Outcome, tasks.md T017 |
| Changes, item 8, superseded (243-251) | Catalogue rows, map lines, counts (15 in use, 27 superseded), shellcheck count; key file stays | plan.md "The third list, as planned"; what was done instead: spec.md Outcome, plan.md, tasks.md T018 |
| Changes, item 8, not proved (252-256) | Needs the real bucket and key; parity and unit tests cover it; first applied on AWS; said in `MAP.md` | spec.md Out of Scope, Edge Cases; research.md R11; tasks.md T023 |
| Changes, item 9 (257-259) | The branch name; `STAGE-11.md` short, points here | spec.md Feature Branch, Clarifications (sixth Q); tasks.md T004 |
| Out of scope (263-268) | Five bullets | spec.md Out of Scope, all five |
| Acceptance (272-285) | Six bullets | spec.md SC-007, SC-002, SC-004, SC-005, SC-003, SC-006, in that order; US1, US4 |
| Outcome, intro (289-290) | Recorded in full in `STAGE-11.md` and `MAP.md` | spec.md Outcome, intro |
| Outcome, no change (292-297) | 0.3.0 needed no change; `--tags` (tried first); `apply: become` | spec.md Outcome, SC-001, FR-005, US3; research.md R1, R3, R4 |
| Outcome, real oneAPI (298-303) | From tag 0.3.0; 55 / 0 / 0; same as data but one difference | spec.md Outcome, SC-002, SC-003; research.md R5; tasks.md T021 |
| Outcome, `async` (304-309) | Async and check mode refused together; the form; a documentation change for the next version | spec.md Outcome, FR-008, Edge Cases; research.md R10; tasks.md T027 |
| Outcome, what differs (310-315) | Five differences | spec.md Outcome; plan.md "What was done instead"; tasks.md T010, T016, T017, T018 |
| Outcome, not proved (316) | The site mirror's list against the bucket | spec.md Outcome, Out of Scope |

## `ATTIC/PLAN.md`, "Collection stages"

| Source | What it says | Carried in |
| --- | --- | --- |
| Section *Status* | Stages 3 and 4 executed 2026-11-14 | spec.md Status; tasks.md note |
| Section intro | Stages planned one file per stage, executed on `do coll <n>` after decisions asked one at a time | spec.md Input ("do coll 3"), Clarifications |
| Stage 3 bullet | The pin, `refresh_modules`, the shell replaced by the `setup` role with two lists, validated in the container with real oneAPI; work in Cloud-Sandbox; executed 2026-11-14; 0.3.0 needed no change | spec.md Why, Status and Outcome; plan.md Summary. The bullet says "two lists"; the stage made three (the third off by default), which the spec says |

## Not carried, on purpose

- **The source's internal links** (`[Decisions taken](#decisions-taken)`,
  `[Outcome](#outcome)`): navigation within the old file.
- **The "YOUR DECISION" form and the word "default"** for the proposals:
  carried as the options of each Clarifications question, with the
  proposal marked "proposed", since the constitution's voice asks the
  question and records the answer.
- **"the bar"** for Cloud-Sandbox's `just test` and `just full-test`: said
  as its acceptance tests, by the operator's standing preference.
- **The 0.3.0 pin as a live instruction**: carried as history, with what
  replaced it (spec.md Assumptions).
- **Anything of Cloud-Sandbox beyond what the stage file said**: its files
  were not read. Where only `STAGE-11.md` holds a result (whether its root
  `just test` and `just full-test` passed), the spec says so instead of
  claiming it.

## Added, not from the source

So the operator can tell them from what the stage file said:

- spec.md Assumptions: the withdrawn versions and 0.0.1 (from spec 001);
  `spack_setup_spack` renamed (spec 002); the example still keeping
  `scope: user`; the later `from_mirrors` defect (spec 003).
- spec.md Outcome and research.md R10: where the `async` finding is today
  (`spack_env`'s notes, `tests/unit/test_async_and_check_mode.py`,
  principle II) and that stage 4 released it as 0.3.1 (from
  `ATTIC/PLAN.md`).
- research.md R2, R3, R6: "Today" notes on the current code; R3 and R4:
  that the role's README does not state the tags and `become` behaviour.
- plan.md Constitution Check: against today's constitution.
