"""
Small runtime helpers for reproducible local execution.
"""
from __future__ import annotations

import os
from pathlib import Path


def configure_matplotlib_env(repo_root: str | Path) -> Path:
    """
    Ensure matplotlib uses a writable cache directory inside the repo unless the
    caller explicitly overrides ``MPLCONFIGDIR``.
    """
    current = os.environ.get("MPLCONFIGDIR")
    target = Path(current) if current else Path(repo_root) / ".mplconfig"
    target.mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(target)
    return target
