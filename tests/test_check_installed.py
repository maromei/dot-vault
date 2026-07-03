import stat
from pathlib import Path
import pytest
from dot_vault.errors import (
    CheckInstalledFailed,
    InvalidReturnFileFormat,
    MoreThanOneFileFound,
)
from dot_vault.modules import get_module


@pytest.fixture
def mock_vault_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Sets up a temporary dot-vault directory for the test duration."""
    monkeypatch.setenv("DOT_VAULT_CONF_DIR", str(tmp_path))
    modules_dir: Path = tmp_path / "modules"
    modules_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path


def create_mock_module(vault_dir: Path, name: str, config_content: str = "") -> Path:
    """Helper to create a module structure inside mock vault."""
    module_dir: Path = vault_dir / "modules" / name
    module_dir.mkdir(parents=True, exist_ok=True)
    if config_content:
        _ = (module_dir / "module_config.toml").write_text(config_content)
    return module_dir


def create_script(module_dir: Path, script_name: str, content: str) -> Path:
    """Helper to create check_installed script."""
    script_dir: Path = module_dir / "check_installed"
    script_dir.mkdir(parents=True, exist_ok=True)
    script_path: Path = script_dir / script_name
    _ = script_path.write_text(content)
    script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
    return script_path


def test_check_installed_no_script(mock_vault_dir: Path) -> None:
    """If no script directory/file, check_installed should return None."""
    _ = create_mock_module(mock_vault_dir, "test_mod")
    module = get_module("test_mod")
    assert module.check_installed(target=None) is None


def test_check_installed_success_true(mock_vault_dir: Path) -> None:
    """Script successfully writes installed = true to the toml file."""
    mod_dir: Path = create_mock_module(mock_vault_dir, "test_mod")
    script_content: str = "\n".join(
        [
            "#!/bin/sh",
            'echo "installed = true" > "$DOT_VAULT_RESULT_FILE"',
            "exit 0",
            "",
        ]
    )
    _ = create_script(mod_dir, "check.sh", script_content)
    module = get_module("test_mod")
    assert module.check_installed(target=None) is True


def test_check_installed_success_false(mock_vault_dir: Path) -> None:
    """Script successfully writes installed = false to the toml file."""
    mod_dir: Path = create_mock_module(mock_vault_dir, "test_mod")
    script_content: str = "\n".join(
        [
            "#!/bin/sh",
            'echo "installed = false" > "$DOT_VAULT_RESULT_FILE"',
            "exit 0",
            "",
        ]
    )
    _ = create_script(mod_dir, "check.sh", script_content)
    module = get_module("test_mod")
    assert module.check_installed(target=None) is False


def test_check_installed_exit_failure(mock_vault_dir: Path) -> None:
    """Script exits with non-zero status code, raising CheckInstalledFailed."""
    mod_dir: Path = create_mock_module(mock_vault_dir, "test_mod")
    script_content: str = "\n".join(
        [
            "#!/bin/sh",
            "exit 1",
            "",
        ]
    )
    _ = create_script(mod_dir, "check.sh", script_content)
    module = get_module("test_mod")
    with pytest.raises(CheckInstalledFailed):
        _ = module.check_installed(target=None)


def test_check_installed_invalid_format(mock_vault_dir: Path) -> None:
    """Script writes invalid structure to the result file, raising InvalidReturnFileFormat."""
    mod_dir: Path = create_mock_module(mock_vault_dir, "test_mod")
    script_content: str = "\n".join(
        [
            "#!/bin/sh",
            'echo "not_installed = true" > "$DOT_VAULT_RESULT_FILE"',
            "exit 0",
            "",
        ]
    )
    _ = create_script(mod_dir, "check.sh", script_content)
    module = get_module("test_mod")
    with pytest.raises(InvalidReturnFileFormat):
        _ = module.check_installed(target=None)


def test_check_installed_multiple_scripts(mock_vault_dir: Path) -> None:
    """Multiple scripts matching target should raise MoreThanOneFileFound."""
    mod_dir: Path = create_mock_module(mock_vault_dir, "test_mod")
    script_content: str = "\n".join(
        [
            "#!/bin/sh",
            'echo "installed = true" > "$DOT_VAULT_RESULT_FILE"',
            "exit 0",
            "",
        ]
    )
    _ = create_script(mod_dir, "check1.sh", script_content)
    _ = create_script(mod_dir, "check2.sh", script_content)
    module = get_module("test_mod")
    with pytest.raises(MoreThanOneFileFound):
        _ = module.check_installed(target=None)
