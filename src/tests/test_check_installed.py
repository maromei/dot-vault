from pathlib import Path
import pytest
from cflowpy import Ok, Err, Nothing, Some
from dot_vault.errors import (
    InvalidReturnFileFormat,
    MoreThanOneFileFound,
    CheckInstallFailed,
    ScriptDirDoesNotExist,
    ScriptFileDoesNotExist,
    ScriptRunFailed,
)
from dot_vault.modules import get_module

from tests.mock import create_mock_module, create_script


def test_check_installed_no_script(mock_vault_dir: Path) -> None:
    """If no script directory/file, check_installed should return an error."""

    _ = create_mock_module(mock_vault_dir, "test_mod")
    match get_module("test_mod"):
        case Ok(module):
            res = module.check_installed(Nothing())
            match res:
                case Err(err):
                    assert isinstance(err, CheckInstallFailed)
                    assert isinstance(err.source, ScriptDirDoesNotExist)
                case Ok(_):
                    pytest.fail("Expected Err, got Ok")
        case Err(err):
            pytest.fail(f"get_module failed: {err}")


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
    match get_module("test_mod"):
        case Ok(module):
            res = module.check_installed(Nothing())
            assert res.is_ok()
            opt = res.unwrap()
            assert opt
        case Err(err):
            pytest.fail(f"get_module failed: {err}")


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
    match get_module("test_mod"):
        case Ok(module):
            res = module.check_installed(Nothing())
            assert res.is_ok()
            opt = res.unwrap()
            assert not opt
        case Err(err):
            pytest.fail(f"get_module failed: {err}")


def test_check_installed_exit_failure(mock_vault_dir: Path) -> None:
    """
    Script exits with non-zero status code, returning
    `Err(CheckInstallFailed)` with source `ScriptRunFailed`.
    """

    mod_dir: Path = create_mock_module(mock_vault_dir, "test_mod")
    script_content: str = "\n".join(
        [
            "#!/bin/sh",
            "exit 1",
            "",
        ]
    )
    _ = create_script(mod_dir, "check.sh", script_content)
    match get_module("test_mod"):
        case Ok(module):
            match module.check_installed(Nothing()):
                case Err(err):
                    assert isinstance(err, CheckInstallFailed)
                    assert isinstance(err.source, ScriptRunFailed)
                case Ok(_):
                    pytest.fail("Expected Err, got Ok")
        case Err(err):
            pytest.fail(f"get_module failed: {err}")


def test_check_installed_invalid_format(mock_vault_dir: Path) -> None:
    """
    Script writes invalid structure to the result file,
    returning `Err(CheckInstallFailed)` with source `InvalidReturnFileFormat`.
    """

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
    match get_module("test_mod"):
        case Ok(module):
            match module.check_installed(Nothing()):
                case Err(err):
                    assert isinstance(err, CheckInstallFailed)
                    assert isinstance(err.source, InvalidReturnFileFormat)
                case Ok(_):
                    pytest.fail("Expected Err, got Ok")
        case Err(err):
            pytest.fail(f"get_module failed: {err}")


def test_check_installed_multiple_scripts(mock_vault_dir: Path) -> None:
    """
    Multiple scripts matching target should return
    `Err(CheckInstallFailed)` with source `MoreThanOneFileFound`.
    """

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
    match get_module("test_mod"):
        case Ok(module):
            match module.check_installed(Nothing()):
                case Err(err):
                    assert isinstance(err, CheckInstallFailed)
                    assert isinstance(err.source, MoreThanOneFileFound)
                case Ok(_):
                    pytest.fail("Expected Err, got Ok")
        case Err(err):
            pytest.fail(f"get_module failed: {err}")


def test_check_installed_with_target_success(mock_vault_dir: Path) -> None:
    """Target-specific script successfully matched and run."""

    mod_dir: Path = create_mock_module(mock_vault_dir, "test_mod")
    script_content: str = "\n".join(
        [
            "#!/bin/sh",
            'echo "installed = true" > "$DOT_VAULT_RESULT_FILE"',
            "exit 0",
            "",
        ]
    )
    _ = create_script(mod_dir, "ubuntu.sh", script_content)
    match get_module("test_mod"):
        case Ok(module):
            res = module.check_installed(Some("ubuntu"))
            assert res.is_ok()
            assert res.unwrap() is True
        case Err(err):
            pytest.fail(f"get_module failed: {err}")


def test_check_installed_with_target_no_match(mock_vault_dir: Path) -> None:
    """Target-specific script search has no match, returning ScriptFileDoesNotExist."""

    mod_dir: Path = create_mock_module(mock_vault_dir, "test_mod")
    script_content: str = "\n".join(
        [
            "#!/bin/sh",
            'echo "installed = true" > "$DOT_VAULT_RESULT_FILE"',
            "exit 0",
            "",
        ]
    )
    _ = create_script(mod_dir, "ubuntu.sh", script_content)
    match get_module("test_mod"):
        case Ok(module):
            res = module.check_installed(Some("fedora"))
            match res:
                case Err(err):
                    assert isinstance(err, CheckInstallFailed)
                    assert isinstance(err.source, ScriptFileDoesNotExist)
                case Ok(_):
                    pytest.fail("Expected Err, got Ok")
        case Err(err):
            pytest.fail(f"get_module failed: {err}")


def test_check_installed_multiple_scripts_resolved_by_target(
    mock_vault_dir: Path,
) -> None:
    """Multiple scripts in the directory, but distinct targets resolve uniquely."""

    mod_dir: Path = create_mock_module(mock_vault_dir, "test_mod")
    ubuntu_content: str = "\n".join(
        [
            "#!/bin/sh",
            'echo "installed = true" > "$DOT_VAULT_RESULT_FILE"',
            "exit 0",
            "",
        ]
    )
    fedora_content: str = "\n".join(
        [
            "#!/bin/sh",
            'echo "installed = false" > "$DOT_VAULT_RESULT_FILE"',
            "exit 0",
            "",
        ]
    )
    _ = create_script(mod_dir, "ubuntu.sh", ubuntu_content)
    _ = create_script(mod_dir, "fedora.sh", fedora_content)
    match get_module("test_mod"):
        case Ok(module):
            res_ubuntu = module.check_installed(Some("ubuntu"))
            assert res_ubuntu.is_ok()
            assert res_ubuntu.unwrap() is True

            res_fedora = module.check_installed(Some("fedora"))
            assert res_fedora.is_ok()
            assert res_fedora.unwrap() is False

            res_none = module.check_installed(Nothing())
            match res_none:
                case Err(err):
                    assert isinstance(err, CheckInstallFailed)
                    assert isinstance(err.source, MoreThanOneFileFound)
                case Ok(_):
                    pytest.fail("Expected Err, got Ok")
        case Err(err):
            pytest.fail(f"get_module failed: {err}")
