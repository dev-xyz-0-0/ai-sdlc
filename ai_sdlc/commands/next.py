"""`aisdlc next` – generate the next lifecycle file via AI agent."""

from __future__ import annotations

import sys

from ai_sdlc.utils import (
    DEFAULT_ACTIVE_DIR,
    DEFAULT_PROMPT_DIR,
    ROOT,
    load_config,
    read_lock,
    write_lock,
)

# Placeholder string used in prompt templates to inject previous step content
PLACEHOLDER = "<prev_step></prev_step>"


def run_next() -> None:
    """Generate the next step's prompt file and advance workflow state.

    Reads the previous step's output, merges it with the next step's prompt template,
    and creates a prompt file for the user to use with their AI tool. If the next
    step file already exists, automatically advances the workflow state.

    Raises:
        SystemExit: If required files are missing or configuration is invalid.
    """
    conf = load_config()
    steps = conf["steps"]
    lock = read_lock()

    if not lock:
        print("❌  No active workstream. Run `aisdlc new` first.")
        return

    try:
        slug = lock["slug"]
        current_step = lock["current"]
    except KeyError as e:
        print(f"❌  Error: Lock file missing required key: {e}")
        print("   Please run `aisdlc new` to create a new workstream.")
        return

    try:
        idx = steps.index(current_step)
    except ValueError:
        print(f"❌  Error: Current step '{current_step}' not found in configuration steps.")
        print(f"   Available steps: {', '.join(steps)}")
        return

    if idx + 1 >= len(steps):
        print("🎉  All steps complete. Run `aisdlc done` to archive.")
        return

    prev_step = steps[idx]
    next_step = steps[idx + 1]

    active_dir = conf.get("active_dir", DEFAULT_ACTIVE_DIR)
    prompt_dir = conf.get("prompt_dir", DEFAULT_PROMPT_DIR)

    workdir = ROOT / active_dir / slug
    prev_file = workdir / f"{prev_step}-{slug}.md"
    prompt_file = ROOT / prompt_dir / f"{next_step}.instructions.md"
    next_file = workdir / f"{next_step}-{slug}.md"

    if not prev_file.exists():
        print(f"❌ Error: The previous step's output file '{prev_file}' is missing.")
        print(f"   This file is required as input to generate the '{next_step}' step.")
        print(
            "   Please restore this file (e.g., from version control) or ensure it was correctly generated."
        )
        print(
            f"   If you need to restart the '{prev_step}', you might need to adjust '.aisdlc.lock' or re-run the command that generates '{prev_step}'."
        )
        sys.exit(1)
    if not prompt_file.exists():
        print(f"❌ Critical Error: Prompt template file '{prompt_file}' is missing.")
        print(f"   This file is essential for generating the '{next_step}' step.")
        print(f"   Please ensure it exists in your '{prompt_dir}/' directory.")
        print(
            "   You may need to restore it from version control or your initial 'aisdlc init' setup."
        )
        sys.exit(1)

    try:
        print(f"ℹ️  Reading previous step from: {prev_file}")
        prev_step_content = prev_file.read_text(encoding="utf-8")
        print(f"ℹ️  Reading prompt template from: {prompt_file}")
        prompt_template_content = prompt_file.read_text(encoding="utf-8")
    except OSError as e:
        print(f"❌ Error: Could not read required file: {e}")
        sys.exit(1)

    merged_prompt = prompt_template_content.replace(PLACEHOLDER, prev_step_content)

    # Create a prompt file for the user to use with their preferred AI tool
    prompt_output_file = workdir / f"_prompt-{next_step}.md"
    try:
        prompt_output_file.write_text(merged_prompt, encoding="utf-8")
    except OSError as e:
        print(f"❌ Error: Could not write prompt file '{prompt_output_file}': {e}")
        sys.exit(1)

    print(f"📝  Generated AI prompt file: {prompt_output_file}")
    print(
        f"🤖  Please use this prompt with your preferred AI tool to generate content for step '{next_step}'"
    )
    print(f"    Then save the AI's response to: {next_file}")
    print()
    print("💡  Options:")
    print(
        "    • Copy the prompt content and paste into any AI chat (Claude, ChatGPT, etc.)"
    )
    print("    • Use with Cursor: cursor agent --file " + str(prompt_output_file))
    print("    • Use with any other AI-powered editor or CLI tool")
    print()
    print(
        f"⏭️   After saving the AI response, the next step file should be: {next_file}"
    )
    print("    Once ready, run 'aisdlc next' again to continue to the next step.")

    # Check if the user has already created the next step file
    if next_file.exists():
        print(f"✅  Found existing file: {next_file}")
        print("    Proceeding to update the workflow state...")

        # Update the lock to reflect the current step
        lock["current"] = next_step
        write_lock(lock)
        print(f"✅  Advanced to step: {next_step}")

        # Clean up the prompt file since it's no longer needed
        if prompt_output_file.exists():
            prompt_output_file.unlink()
            print(f"🧹  Cleaned up prompt file: {prompt_output_file}")

        return
    else:
        print(f"⏸️   Waiting for you to create: {next_file}")
        print(
            "    Use the generated prompt with your AI tool, then run 'aisdlc next' again."
        )
        return
