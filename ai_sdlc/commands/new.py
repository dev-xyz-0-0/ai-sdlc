"""`aisdlc new` – start a work-stream from an idea title."""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from ai_sdlc.utils import (
    DEFAULT_ACTIVE_DIR,
    ROOT,
    load_config,
    slugify,
    write_lock,
)


def run_new(args: list[str]) -> None:
    """Create the work-stream folder and first markdown file.

    Args:
        args: List of command-line arguments. The first argument should be the idea title.

    Raises:
        SystemExit: If no arguments provided or if work-stream already exists.
    """
    if not args:
        print('Usage: aisdlc new "Idea title"')
        sys.exit(1)

    # Load configuration to get the first step
    config = load_config()
    first_step = config["steps"][0]

    idea_text = " ".join(args)
    slug = slugify(idea_text)

    config = load_config()
    active_dir = config.get("active_dir", DEFAULT_ACTIVE_DIR)
    workdir = ROOT / active_dir / slug
    if workdir.exists():
        print(f"❌  Work-stream '{slug}' already exists.")
        sys.exit(1)

    try:
        workdir.mkdir(parents=True, exist_ok=False)
        idea_file = workdir / f"{first_step}-{slug}.md"
        idea_file.write_text(
            f"# {idea_text}\n\n## Problem\n\n## Solution\n\n## Rabbit Holes\n",
            encoding="utf-8",
        )

        write_lock(
            {
                "slug": slug,
                "current": first_step,
                "created": datetime.now(timezone.utc).isoformat(),
            },
        )
        print(f"✅  Created {idea_file}.  Fill it out, then run `aisdlc next`.")
    except OSError as e:
        print(f"❌  Error creating work-stream files for '{slug}': {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"❌  Error: Invalid configuration - missing key: {e}")
        print("   Please ensure your .aisdlc file has a 'steps' key with at least one step.")
        sys.exit(1)
