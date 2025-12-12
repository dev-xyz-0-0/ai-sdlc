"""Pytest configuration and shared fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Create a temporary directory simulating a project root.

    Args:
        tmp_path: Pytest fixture providing a temporary directory unique to the test.

    Returns:
        Path: Path to the temporary project directory.
    """
    # tmp_path is a pytest fixture providing a temporary directory unique to the test
    # For more complex setups, you might copy baseline files here
    return tmp_path
