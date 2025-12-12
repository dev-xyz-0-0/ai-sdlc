"""Unit tests for ai_sdlc.commands.init module."""

from pathlib import Path

import pytest

from ai_sdlc.commands import init


def test_run_init(temp_project_dir: Path, mocker):
    """Test that init command creates necessary directories and files."""
    mocker.patch("ai_sdlc.utils.ROOT", temp_project_dir)

    # Mock package resources
    mock_files = mocker.patch("ai_sdlc.commands.init.pkg_resources.files")
    mock_scaffold = mocker.MagicMock()
    mock_files.return_value.joinpath.return_value = mock_scaffold
    mock_scaffold.joinpath.return_value.read_text.return_value = "test content"
    
    # Mock directory operations
    mock_mkdir = mocker.patch.object(Path, "mkdir")

    # Mock file writing operations
    mock_write_text = mocker.patch.object(Path, "write_text")

    init.run_init()

    # Verify directories would have been created
    assert mock_mkdir.called

    # Verify lock file would have been written
    assert mock_write_text.called
