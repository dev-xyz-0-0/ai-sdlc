"""`aisdlc done` – validate finished stream and archive it."""

import shutil
import sys

from ai_sdlc.utils import (
    DEFAULT_ACTIVE_DIR,
    DEFAULT_DONE_DIR,
    ROOT,
    load_config,
    read_lock,
    write_lock,
)


def run_done() -> None:
    """Validate that all steps are complete and archive the workstream.

    Checks that:
    - An active workstream exists
    - The current step is the last step
    - All step files exist

    Then moves the workstream from doing/ to done/ and clears the lock file.

    Raises:
        SystemExit: If validation fails or archiving encounters an error.
    """
    conf = load_config()
    try:
        steps = conf["steps"]
    except KeyError:
        print("❌  Error: Configuration missing required 'steps' key.")
        print("   Please ensure your .aisdlc file has a 'steps' key.")
        sys.exit(1)
    
    active_dir = conf.get("active_dir", DEFAULT_ACTIVE_DIR)
    done_dir = conf.get("done_dir", DEFAULT_DONE_DIR)

    lock = read_lock()
    if not lock:
        print("❌  No active workstream.")
        return

    try:
        slug = lock["slug"]
        current_step = lock["current"]
    except KeyError as e:
        print(f"❌  Error: Lock file missing required key: {e}")
        print("   Please run `aisdlc new` to create a new workstream.")
        return

    if current_step != steps[-1]:
        print("❌  Workstream not finished yet. Complete all steps before archiving.")
        return

    workdir = ROOT / active_dir / slug
    missing = [s for s in steps if not (workdir / f"{s}-{slug}.md").exists()]
    if missing:
        print("❌  Missing files:", ", ".join(missing))
        return

    dest = ROOT / done_dir / slug
    try:
        shutil.move(str(workdir), str(dest))
        write_lock({})
        print(f"🎉  Archived to {dest}")
    except OSError as e:
        print(f"❌  Error archiving work-stream '{slug}': {e}")
        sys.exit(1)
