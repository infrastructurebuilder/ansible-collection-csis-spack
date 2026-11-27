# infrastructurebuilder.csis_spack: an Ansible collection for managing Spack environments.

set shell := ["bash", "-euo", "pipefail", "-c"]

version := `sed -n 's/^version: //p' galaxy.yml`
tarball := "dist/infrastructurebuilder-csis_spack-" + version + ".tar.gz"
# ansible-test needs the collection at ansible_collections/<namespace>/<name>.
sanity_tree := ".tmp/ansible_collections/infrastructurebuilder/csis_spack"

# List the targets.
default:
    @just --justfile {{ justfile() }} --list

# Create the tool environment (ansible-core 2.16, ruff, pyright, pytest).
init:
    uv sync

# Build the collection tarball into dist/.
build:
    mkdir -p dist
    uv run ansible-galaxy collection build --force --output-path dist
    @echo "built {{ tarball }}"

# Put the collection where Ansible and the tests look for it: .tmp/collections/ansible_collections/infrastructurebuilder/csis_spack.
tree:
    mkdir -p .tmp/collections/ansible_collections/infrastructurebuilder
    ln -sfn ../../../.. .tmp/collections/ansible_collections/infrastructurebuilder/csis_spack

# ruff on the plugins, the tests and the release tools.
lint:
    uv run ruff check plugins tests tools
    uv run ruff format --check plugins tests tools

# Rewrite the plugins, the tests and the release tools in ruff's format, which lint checks.
format:
    uv run ruff format plugins tests tools

# Type-check; any error fails.
typecheck: tree
    uv run pyright

# Lint, type-check, the unit tests against a stand-in spack (a few minutes: each runs Ansible), and a build that installs.
test: lint typecheck tree
    uv run pytest -q -n auto
    just --justfile {{ justfile() }} install-check

# Only the unit tests, or some of them (arguments go to pytest: just unit -k checkout), for seeing a new test fail or pass while working. Not a substitute for test: no lint, no type-check, no build.
[positional-arguments]
unit *args: tree
    uv run pytest -q -n auto "$@"

# Build the tarball and install it into a throw-away collections path.
install-check: build
    rm -rf .tmp/installed
    uv run ansible-galaxy collection install --force -p .tmp/installed {{ tarball }}
    test -f .tmp/installed/ansible_collections/infrastructurebuilder/csis_spack/MANIFEST.json

# Everything in test, then the modules and the setup role against the real Spack v1.2.0 (cloned into .tmp/ once), then ansible-test sanity and Galaxy's own import checks (both need the network the first time).
full-test: test import-check
    just --justfile {{ justfile() }} integration
    rm -rf .tmp/ansible_collections
    mkdir -p {{ sanity_tree }}
    # Without the planning and agent material, which galaxy.yml keeps out of the tarball too: sanity checks what is shipped, and Spec Kit's own scripts are not ours to hold to shellcheck.
    git ls-files --cached --others --exclude-standard -z -- . ':!.specify' ':!.claude' ':!specs' ':!ATTIC' ':!CLAUDE.md' | rsync -a --from0 --files-from=- ./ {{ sanity_tree }}/
    # A repository of its own: inside this one, ansible-test would ask this repository's git for its files, and .tmp/ is ignored.
    cd {{ sanity_tree }} && git init -q && git add -A
    cd {{ sanity_tree }} && uv run --project {{ justfile_directory() }} ansible-test sanity --venv --python 3.12

# Only the modules and the setup role against the real Spack 1.0.0, 1.1.0 and 1.2.0 (cloned into .tmp/ once), without the rest of full-test: for seeing a new integration test fail before the change it tests. Not a substitute for test or full-test. Arguments go to pytest, to run some of them: just integration -k checkout (full-test passes none).
[positional-arguments]
integration *args: tree
    uv run pytest -q -m integration tests/integration "$@"

# Build the tarball and run galaxy-importer on it, the checks Galaxy runs when a version is uploaded (ansible-doc and ansible-lint).
import-check: build
    mkdir -p .tmp/importer
    cd .tmp/importer && uv run --no-project --python 3.12 --with galaxy-importer python -I -m galaxy_importer.main {{ justfile_directory() }}/{{ tarball }} | tee import.log
    grep -q "Importer processing completed successfully" .tmp/importer/import.log

# A release is cut by hand: full-test, then the tarball. Publishing is a separate step, `just publish`, from the tag.
release: full-test build
    @echo "{{ tarball }} is ready; tag it {{ version }}, then publish from the tag with just publish"

# Upload the tarball to Galaxy (GALAXY_SERVER for another server). Needs GALAXY_API_KEY in the environment and HEAD at the tag of galaxy.yml's version; a version already there is left alone. Also run by .github/workflows/publish.yml when a tag is pushed.
publish: import-check
    uv run python tools/publish.py {{ tarball }}
