# Quickstart: seeing it done

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Everything runs on your local machine, from the repository root, on the
branch `feature/remove-attic`.

## The coverage record is complete

Open [coverage/README.md](coverage/README.md). Every part of the ATTIC
(`ATTIC/PLAN.md` in three parts, and the five stage files) names its
record, and the record's "Could not place" says nothing. The README's
state is **complete**.

## The ATTIC is gone and nothing points at it

```sh
test ! -e ATTIC && echo "no ATTIC"
git grep -n ATTIC -- . ':!specs' ':!CHANGELOG.md'   # prints nothing
just unit tests/unit/test_no_attic.py               # the same, held by a test
```

## Its last state is recoverable

`specs/README.md` names the last commit that has `ATTIC/`. With that hash:

```sh
git show <hash>:ATTIC/PLAN.md | head -8
```

prints the old plan's "This file is closed" header.

## The rules and the tests

- `.specify/memory/constitution.md`: no section "The ATTIC". Its version
  line shows the new version and Last Amended date.
- `just test`, then `just full-test`: both pass. `just build` gives the same
  tarball contents as before.
