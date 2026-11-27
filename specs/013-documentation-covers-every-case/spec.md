# Feature Specification: The documentation covers every case of the collection

**Feature Branch**: `feature/documentation-covers-every-case`

**Created**: 2026-11-27

**Status**: Draft

**Input**: The operator, 2026-11-27: "Make a spec 013 for ensuring that
documentation covers all the cases of this project."

## Clarifications

### Session 2026-11-27

- Q: Which cases must the documentation cover? → A: Everything: the
  interface (every module option, return value, role variable and step
  kind), the behaviour (every failure and refusal a task can report, what
  check mode and a repeat run do, every difference by Spack version), and
  every kind of site, each with an example the tests carry out, with the
  role's behaviour under `--tags` and `apply: become` among the cases.
- Q: Which documents count as "the documentation"? → A: What a site reads:
  each module's and filter's `ansible-doc` (`DOCUMENTATION`, `EXAMPLES`,
  `RETURN`), the `setup` role's README, the README, and `docs/examples/`.
  Not `CHANGELOG.md`, and not the specs.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A site finds every case it can meet in the documentation (Priority: P1)

Someone writing a playbook reads the collection's documentation (each
module's `ansible-doc`, the `setup` role's README, the README, the examples)
and finds, for each module option, each step kind and each role variable,
what it does, what its default is, what each value does, and what happens in
check mode and on a repeat run. For each way a task can fail, they find what
the failure says and what to do. Nothing the code does is found only by
reading the code.

**Why this priority**: it is the whole of the feature. The constitution
already makes documentation part of every change, and asks for "a little
more explanation over a little less"; this spec makes sure nothing has been
missed, across all the work done so far, and keeps it so.

**Independent Test**: take each case listed in this spec's inventory and
find it in the documentation; find none missing. Then change the code so that
it has a case the documentation lacks, and see a test fail.

**Acceptance Scenarios**:

1. **Given** each module, **When** its `ansible-doc` is read, **Then** every
   option, every return value and every failure it can report are described,
   with what check mode and a repeat run do.
2. **Given** the `setup` role, **When** its README is read, **Then** every
   variable, every step kind, every rule that refuses a list before any step
   runs, and what the role records in `spack_setup_results`, are described.
3. **Given** the cases that depend on the Spack version (the differences in
   `BEHAVIOUR`, Spack 1.1's missing scope directories), **When** the
   documentation is read, **Then** each is said where a site would look for
   it.
4. **Given** a new option, step kind, return value or failure added later,
   **When** it lacks documentation, **Then** `just test` fails.

---

### User Story 2 - A site finds a complete example for each kind of site (Priority: P2)

A site looks for an example close to its own: a system compiler, a compiler
behind environment modules, a compiler Spack builds, a site mirror with a
key, Spack installed by the role, a Spack moved to a new version. Each
example is run by the tests, so none is out of date.

**Why this priority**: examples are how most sites start; a case with no
example is learned the hard way.

**Independent Test**: list the kinds of site the documentation names; find
an example for each under `docs/examples/`, and each carried out by
`tests/unit/test_examples.py`.

**Acceptance Scenarios**:

1. **Given** the situations this spec's inventory names, **When**
   `docs/examples/` is read, **Then** each has an example, or the inventory
   says why none is needed.
2. **Given** an example, **When** `just test` runs, **Then** the example is
   carried out against the stand-in `spack`.

---

### Edge Cases

- **A case the code handles that no one should rely on** (an internal
  detail): it is not documented as behaviour, and the inventory says so.
- **A failure that comes from Spack or git, not from the module**: the
  documentation says that the module passes the message on, and where to
  look.
- **Documentation that describes a case the code no longer has**: as much a
  gap as a missing one; the tests find it the same way.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: An inventory MUST list every case of the collection, of three
  kinds: (1) the interface: every module option, return value, role variable
  and step kind; (2) the behaviour: every failure and refusal a task can
  report, what check mode and a repeat run do, and every difference by Spack
  version; (3) every kind of site the collection serves, and the role's
  behaviour where it is included (under `--tags`, with `apply: become`).
- **FR-002**: Each case in the inventory MUST be described in the
  documentation a site reads: each module's and filter's `ansible-doc`
  (`DOCUMENTATION`, `EXAMPLES`, `RETURN`), the `setup` role's README, the
  README, or `docs/examples/`, in the one a site would look in first for it.
  `CHANGELOG.md` and the specs do not count towards coverage.
- **FR-003**: Wherever it can be, the coverage MUST be held by a test that
  fails when a case is undocumented or documented wrongly, in the spirit of
  the constitution's principle IV ("What the documentation promises is held
  by a test where it can be") [NEEDS CLARIFICATION: how far: (a) tests that
  every option, return value, kind and variable appears in the documentation;
  (b) those, plus tests that every failure message the code can raise appears
  in it; or (c) a review checklist only, with no new tests?].
- **FR-004**: Every gap the inventory finds MUST be closed in the
  documentation, and recorded in `CHANGELOG.md`.
- **FR-005**: The documentation MUST keep saying what the constitution asks
  of examples: every `async` example in the form that previews (principle
  II), no site's names in the collection's own documentation (principle I).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every case in the inventory is found in the documentation: zero
  gaps.
- **SC-002**: A case added later without documentation makes `just test`
  fail, for every kind of case FR-003 covers.
- **SC-003**: Every example under `docs/examples/` is carried out by the
  tests.

## Assumptions

- "The documentation" is what a site reads: what `ansible-doc` shows for each
  module and filter, the role's README, the README, and the examples. The
  specs are the repository's planning record, not a site's documentation.
- Specs 006 (the two known limits) and 012 (removing the ATTIC) come first, so
  that the inventory is taken of the collection as it will be.
- No release is cut by this spec. Its documentation goes out with the next
  release, on the operator's word.

## Gaps already found

Writing the retrospective specs 007–011 on 2026-11-27 found these, which the
inventory starts from:

- `tests/unit/test_async_and_check_mode.py` reads only `spack_env`'s
  `EXAMPLES`, `README.md` and `roles/setup/README.md`: neither the examples
  under `docs/examples/` nor the other modules' `EXAMPLES` are held to the
  `async` form (spec 011). Principle II's "every example" holds today only
  because none of them uses `async`.
- No test holds the README's examples free of a site's names: the test for
  site knowledge reads only `plugins/` and `roles/` (spec 011).
- How the `setup` role behaves when it is included under `--tags`, and with
  `apply: {become: true, become_user: ...}` (every step runs, as that user),
  is documented nowhere and held by no test of this repository (spec 010).
- `docs/examples/cloud-sandbox.yml` sets two settings in the user scope, as
  the sandbox's script did, though the sandbox itself chose the site scope;
  the example does not say why (spec 010).
- `README.md`'s "Building an environment" leaves out one reason `spack_env`
  regenerates module files, a missing module root, which the option's own
  documentation gives (spec 008).
- No test runs `ansible-doc` on a module by name; the notes are read from
  `DOCUMENTATION`, and galaxy-importer in `just full-test` runs `ansible-doc`
  on every plugin (spec 011).
