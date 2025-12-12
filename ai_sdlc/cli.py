#!/usr/bin/env python
"""Entry-point for the `aisdlc` CLI."""

from __future__ import annotations

import sys
from collections.abc import Callable
from importlib import import_module

from .utils import CONFIG_FILE, load_config, read_lock

_COMMANDS: dict[str, str] = {
    "init": "ai_sdlc.commands.init:run_init",
    "new": "ai_sdlc.commands.new:run_new",
    "next": "ai_sdlc.commands.next:run_next",
    "status": "ai_sdlc.commands.status:run_status",
    "done": "ai_sdlc.commands.done:run_done",
}


def _resolve(dotted: str) -> Callable[..., None]:
    """Import a function from a module using dotted path notation.

    Args:
        dotted: String in format "module.path:function_name".

    Returns:
        Callable[..., None]: The imported function.

    Raises:
        ValueError: If the dotted path format is invalid.
        ImportError: If the module cannot be imported.
        AttributeError: If the function is not found in the module.
    """
    if ":" not in dotted:
        raise ValueError(f"Invalid dotted path format: {dotted}. Expected 'module:function'")
    module_name, func_name = dotted.split(":", 1)
    try:
        module = import_module(module_name)
    except ImportError as e:
        raise ImportError(f"Could not import module '{module_name}': {e}") from e
    if not hasattr(module, func_name):
        raise AttributeError(f"Module '{module_name}' has no attribute '{func_name}'")
    return getattr(module, func_name)  # type: ignore[no-any-return]


def _display_compact_status() -> None:
    """Display a compact version of the current workstream status.

    Shows the active feature slug, current step, and progress bar.
    Silently handles errors to avoid disrupting the main command output.
    """
    lock = read_lock()
    if not lock or "slug" not in lock:
        return  # No active workstream or invalid lock

    try:
        conf = load_config()
        steps = conf["steps"]
        slug = lock.get("slug", "N/A")
        current_step_name = lock.get("current", "N/A")

        if current_step_name in steps:
            idx = steps.index(current_step_name)
            # Steps are in format like "01-idea", take the part after the dash
            bar = " ▸ ".join(
                [
                    ("✅" if i <= idx else "☐") + s.split("-", 1)[1]
                    for i, s in enumerate(steps)
                ]
            )
            print(f"\n---\n📌 Current: {slug} @ {current_step_name}\n   {bar}\n---")
        else:
            print(
                f"\n---\n📌 Current: {slug} @ {current_step_name} (Step not in config)\n---"
            )
    except (FileNotFoundError, KeyError):  # .aisdlc missing or invalid config
        print(
            f"\n---\n📌 AI-SDLC config ({CONFIG_FILE}) not found or invalid. Cannot display status.\n---"
        )
    except Exception:  # Catch other potential errors during status display
        print(
            "\n---\n📌 Could not display current status due to an unexpected issue.\n---"
        )


def main() -> None:  # noqa: D401
    """Run the requested sub-command.

    Parses command-line arguments and routes to the appropriate command handler.
    Displays compact status after most commands (except status and init).
    """
    cmd, *args = sys.argv[1:] or ["--help"]
    if cmd not in _COMMANDS:
        valid = "|".join(_COMMANDS.keys())
        print(f"Usage: aisdlc [{valid}] [--help]")
        sys.exit(1)

    try:
        handler = _resolve(_COMMANDS[cmd])
        handler(args) if args else handler()
    except (ValueError, ImportError, AttributeError) as e:
        print(f"❌ Error: Failed to load command '{cmd}': {e}")
        sys.exit(1)

    # Display status after most commands, unless it's status itself or init (before lock exists)
    if cmd not in ["status", "init"]:
        _display_compact_status()


if __name__ == "__main__":
    main()
