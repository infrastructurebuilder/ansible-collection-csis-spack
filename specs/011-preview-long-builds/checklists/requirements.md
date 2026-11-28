# Specification Quality Checklist: Say how to preview a long build

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-11-27 (retrospective)
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [ ] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Reviewed once, on 2026-11-27, when this retrospective was written; the
  work was done on 2026-11-14.
- The spec names Ansible's keywords (`async`, `poll`, `ansible_check_mode`,
  `--check`), the module's `DOCUMENTATION` and `EXAMPLES`, and the files the
  test reads. They are kept: the feature is how a site writes a task, and
  those names are what it types and reads. For an Ansible collection that is
  the interface, not an implementation detail, as in this repository's other
  specs.
- "Technology-agnostic" is left unticked: SC-004 names `ansible-doc`, and
  SC-001 to SC-003 are about Ansible's own behaviour. A success criterion
  that did not name Ansible would not say anything about this feature.
- "Written for non-technical stakeholders" is read for this repository as
  "for someone who uses Ansible and has not read the code".
- One edge case is open and recorded as not tried: a task that sets
  `check_mode: true` on itself together with the form (research R1). It is
  outside what the source did, and is not a [NEEDS CLARIFICATION]: nothing
  in this spec depends on it.
- FR-004 and SC-003 cover the three texts the test reads, not every example
  in the repository (spec, Assumptions). Principle II asks for every
  example; today no other example gives `async`, so the two agree in fact,
  not by a test.
