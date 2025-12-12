"""Unit tests for ai_sdlc.utils module."""

import json
from pathlib import Path

import pytest

from ai_sdlc import utils


def test_slugify_basic():
    """Test basic slugify functionality."""
    assert utils.slugify("Hello World!") == "hello-world"
    assert utils.slugify("  Test Slug with Spaces  ") == "test-slug-with-spaces"
    assert utils.slugify("Special!@#Chars") == "special-chars"
    assert utils.slugify("") == "idea"  # As per current implementation


def test_slugify_unicode():
    """Test slugify with unicode characters."""
    assert utils.slugify("Café") == "caf"
    assert utils.slugify("Müller") == "mller"
    assert utils.slugify("日本語") == "idea"  # Non-ASCII only, falls back to "idea"


def test_slugify_edge_cases():
    """Test slugify with edge cases."""
    assert utils.slugify("---") == "idea"  # Only separators
    assert utils.slugify("123") == "123"
    assert utils.slugify("a" * 100) == "a" * 100  # Long strings


def test_load_config_success(temp_project_dir: Path, mocker):
    """Test successful loading of valid .aisdlc configuration."""
    mock_aisdlc_content = """
    version = "0.1.0"
    steps = ["01-idea", "02-prd"]
    prompt_dir = "prompts"
    active_dir = "doing"
    done_dir = "done"
    """
    aisdlc_file = temp_project_dir / ".aisdlc"
    aisdlc_file.write_text(mock_aisdlc_content, encoding="utf-8")

    mocker.patch(
        "ai_sdlc.utils.ROOT", temp_project_dir
    )  # Ensure ROOT points to test dir

    config = utils.load_config()
    assert config["version"] == "0.1.0"
    assert config["steps"] == ["01-idea", "02-prd"]
    assert config["prompt_dir"] == "prompts"


def test_load_config_missing(temp_project_dir: Path, mocker):
    """Test that load_config exits when .aisdlc file is missing."""
    mocker.patch("ai_sdlc.utils.ROOT", temp_project_dir)
    with pytest.raises(SystemExit) as exc_info:
        utils.load_config()
    assert exc_info.value.code == 1


def test_load_config_corrupted(temp_project_dir: Path, mocker):
    """Test that load_config handles corrupted TOML gracefully."""
    aisdlc_file = temp_project_dir / ".aisdlc"
    aisdlc_file.write_text("this is not valid toml content {", encoding="utf-8")  # Corrupted TOML
    mocker.patch("ai_sdlc.utils.ROOT", temp_project_dir)
    mock_exit = mocker.patch("sys.exit")  # Prevent test suite from exiting

    # Should call sys.exit(1)
    utils.load_config()
    mock_exit.assert_called_once_with(1)


def test_read_write_lock(temp_project_dir: Path, mocker):
    """Test reading and writing lock files."""
    mocker.patch("ai_sdlc.utils.ROOT", temp_project_dir)
    lock_data = {"slug": "test-slug", "current": "01-idea", "created": "2025-01-01T00:00:00"}

    # Test write_lock
    utils.write_lock(lock_data)
    lock_file = temp_project_dir / ".aisdlc.lock"
    assert lock_file.exists()
    assert json.loads(lock_file.read_text(encoding="utf-8")) == lock_data

    # Test read_lock
    read_data = utils.read_lock()
    assert read_data == lock_data

    # Test read_lock when file doesn't exist
    lock_file.unlink()
    assert utils.read_lock() == {}

    # Test read_lock with corrupted JSON
    lock_file.write_text("not json {", encoding="utf-8")
    assert utils.read_lock() == {}  # Should return empty dict on corruption


def test_read_lock_empty_file(temp_project_dir: Path, mocker):
    """Test reading an empty lock file."""
    mocker.patch("ai_sdlc.utils.ROOT", temp_project_dir)
    lock_file = temp_project_dir / ".aisdlc.lock"
    lock_file.write_text("", encoding="utf-8")
    # Empty file should cause JSONDecodeError and return {}
    assert utils.read_lock() == {}


def test_write_lock_os_error(temp_project_dir: Path, mocker):
    """Test that write_lock raises OSError on write failure."""
    mocker.patch("ai_sdlc.utils.ROOT", temp_project_dir)
    # Create a directory with the lock file name to cause write error
    lock_file = temp_project_dir / ".aisdlc.lock"
    lock_file.mkdir()
    
    with pytest.raises(OSError):
        utils.write_lock({"slug": "test"})
