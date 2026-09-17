"""Compatibility wrapper for the backend server.

This lets the common command:
    uvicorn server:app
work from the repository root without forcing users to `cd` into
`acestep-engine/` first.
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_BACKEND_PATH = Path(__file__).resolve().parent / "acestep-engine" / "server.py"

if not _BACKEND_PATH.exists():
    raise FileNotFoundError(
        "The ACE-Step backend was not found at 'acestep-engine/server.py'. "
        "Follow the setup steps in README.md before starting the app."
    )

_SPEC = spec_from_file_location("melodai_acestep_server", _BACKEND_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Could not load backend module from {_BACKEND_PATH}")

_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

app = _MODULE.app
