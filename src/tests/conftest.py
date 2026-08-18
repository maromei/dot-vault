"""Fixtures defined in this file are automatically discovered by pytest."""

from pathlib import Path

import pytest


@pytest.fixture
def mock_vault_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Sets up a temporary dot-vault directory for the test duration."""
    monkeypatch.setenv("DOT_VAULT_CONF_DIR", str(tmp_path))
    modules_dir: Path = tmp_path / "modules"
    modules_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path
