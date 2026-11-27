"""A stand-in for Spack's own ``spack.util.spack_yaml``, for the tests only.

The stand-in ``spack`` (``tests/unit/fake_spack.py``) runs a script given to
``spack python <script>`` with this directory first on ``sys.path``, so that
the script's ``import spack.util.spack_yaml`` finds this module, as the real
Spack's would find its own. It reads and writes YAML with PyYAML. It is
never part of the collection.
"""

from __future__ import annotations

from typing import IO, Any

import yaml


def load(stream: IO[str]) -> Any:
    return yaml.safe_load(stream)


def dump(data: Any, stream: IO[str]) -> None:
    yaml.safe_dump(data, stream, sort_keys=False)
