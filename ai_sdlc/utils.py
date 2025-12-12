"""Shared helpers for AI-SDLC CLI commands."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

# Configuration file names
CONFIG_FILE = ".aisdlc"
LOCK_FILE = ".aisdlc.lock"

# Default directories
DEFAULT_ACTIVE_DIR = "doing"
DEFAULT_DONE_DIR = "done"
DEFAULT_PROMPT_DIR = "prompts"

# Default fallback slug
DEFAULT_SLUG = "idea"


def find_project_root() -> Path:
    """Find project root by searching for .aisdlc file in current and parent directories.

    Returns:
        Path: The project root directory containing .aisdlc, or current directory if not found.
    """
    current_dir = Path.cwd()
    for parent in [current_dir] + list(current_dir.parents):
        if (parent / CONFIG_FILE).exists():
            return parent
    # For init command, return current directory if no .aisdlc found
    # Other commands will check for .aisdlc existence separately
    return current_dir


ROOT = find_project_root()

# --- TOML loader (Python ≥3.11 stdlib) --------------------------------------
try:
    import tomllib as _toml  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover – fallback for < 3.11
    import tomli as _toml  # type: ignore[import-not-found,no-redef]  # noqa: D401  # `uv pip install tomli`


def load_config() -> dict[str, Any]:
    """Load and parse the .aisdlc configuration file.

    Returns:
        dict[str, Any]: Parsed TOML configuration as a dictionary.

    Raises:
        SystemExit: If the config file is missing or corrupted.
    """
    cfg_path = ROOT / CONFIG_FILE
    if not cfg_path.exists():
        print(
            f"Error: {CONFIG_FILE} not found. Ensure you are in an ai-sdlc project directory."
        )
        print("Run `aisdlc init` to initialize a new project.")
        sys.exit(1)
    try:
        return _toml.loads(cfg_path.read_text(encoding="utf-8"))
    except _toml.TOMLDecodeError as e:
        print(f"❌ Error: '{CONFIG_FILE}' configuration file is corrupted: {e}")
        print(f"Please fix the {CONFIG_FILE} file or run 'aisdlc init' in a new directory.")
        sys.exit(1)
    except OSError as e:
        print(f"❌ Error: Could not read '{CONFIG_FILE}' configuration file: {e}")
        sys.exit(1)


def slugify(text: str) -> str:
    """Convert text to a kebab-case ASCII-only slug.

    Args:
        text: The text to convert to a slug.

    Returns:
        str: A kebab-case slug (e.g., "Hello World!" -> "hello-world").
             Returns DEFAULT_SLUG if the result would be empty.
    """
    slug = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", slug).strip("-").lower()
    return slug or DEFAULT_SLUG


def read_lock() -> dict[str, Any]:
    """Read and parse the .aisdlc.lock file.

    Returns:
        dict[str, Any]: Lock file contents as a dictionary.
                       Returns empty dict if file doesn't exist or is corrupted.
    """
    path = ROOT / LOCK_FILE
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        print(
            f"⚠️  Warning: '{LOCK_FILE}' file is corrupted or not valid JSON. Treating as empty."
        )
        return {}
    except OSError as e:
        print(f"⚠️  Warning: Could not read '{LOCK_FILE}' file: {e}. Treating as empty.")
        return {}


def write_lock(data: dict[str, Any]) -> None:
    """Write lock data to .aisdlc.lock file.

    Args:
        data: Dictionary to write as JSON to the lock file.

    Raises:
        OSError: If the file cannot be written.
    """
    lock_path = ROOT / LOCK_FILE
    try:
        lock_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as e:
        print(f"❌ Error: Could not write to '{LOCK_FILE}' file: {e}")
        raise
