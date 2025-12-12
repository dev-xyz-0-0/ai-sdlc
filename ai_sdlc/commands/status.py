"""`aisdlc status` – show progress through lifecycle steps."""

from ai_sdlc.utils import load_config, read_lock


def run_status() -> None:
    """Display the current status of active workstreams.

    Shows the workstream slug, current step, and a progress bar indicating
    which steps have been completed.
    """
    try:
        conf = load_config()
        steps = conf["steps"]
    except KeyError:
        print("❌  Error: Configuration missing 'steps' key.")
        print("   Please ensure your .aisdlc file is properly configured.")
        return

    lock = read_lock()
    print("Active workstreams\n------------------")
    if not lock:
        print("none – create one with `aisdlc new`")
        return

    try:
        slug = lock["slug"]
        cur = lock["current"]
    except KeyError as e:
        print(f"❌  Error: Lock file missing required key: {e}")
        print("   Please run `aisdlc new` to create a new workstream.")
        return

    try:
        idx = steps.index(cur)
    except ValueError:
        print(f"❌  Error: Current step '{cur}' not found in configuration steps.")
        print(f"   Available steps: {', '.join(steps)}")
        return

    # Steps are in format like "01-idea", take the part after the dash
    bar = " ▸ ".join([("✅" if i <= idx else "☐") + s.split("-", 1)[1] if "-" in s else s[2:] for i, s in enumerate(steps)])
    print(f"{slug:20} {cur:12} {bar}")
