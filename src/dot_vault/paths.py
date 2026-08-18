"""Contains function retrieving the default or expected project dot-vault structure.

F.e. eventhough a :mod:`dot_vault.modules` module exists, the :func:`get_module_dir`
function is still found here, since it retrieves the path within the default
structure.
"""

from __future__ import annotations

from pathlib import Path

from cflowpy import Option, Some, Result, Ok, Err, nothing, Nothing
from dot_vault.errors import (
    GetScriptErrors,
    ModuleDirDoesNotExist,
    ModuleDirErrors,
    MoreThanOneFileFound,
    DotVaultDirDoesNotExist,
    ScriptDirDoesNotExist,
    ScriptFileDoesNotExist,
)
from dot_vault.settings import EnvironmentSettings


def get_dot_vault_dir() -> Result[Path, DotVaultDirDoesNotExist]:
    """Get the directory containing the dot-vault config.

    Currently only searches for `~/config/dot-vault/`.

    Returns:
        Result containing the Path to the dot-vault directory or FileNotFoundError.
    """

    dotvault_dir: Path = EnvironmentSettings().conf_dir
    dotvault_dir = dotvault_dir.resolve()

    if not dotvault_dir.is_dir():
        msg = f"The dot-vault directory does not exist. '{dotvault_dir.as_posix()}'"
        return Err(DotVaultDirDoesNotExist(msg))
    return Ok(dotvault_dir)


def get_module_dir(
    name: Option[str] = nothing,
) -> Result[Path, ModuleDirErrors]:
    """Get the directory containing the module config.

    Currently only searches for `modules/` in the directory given by
    :func:`get_dot_vault_dir`. If `name` is `Some`, the directory of the
    specific module will be returned `modules/{name}/`.

    Args:
        name: Optional name to a specific module directory. Otherwise return
            path to the general modules directory.

    Returns:
        Result containing the Path to the module directory or relevant exceptions.
    """

    dot_vault_dir_res: Result[Path, DotVaultDirDoesNotExist] = get_dot_vault_dir()
    match dot_vault_dir_res:
        case Err(err):
            return Err(err)
        case Ok(dot_vault_dir):
            pass

    module_dir: Path = dot_vault_dir / "modules/"
    for specific_module in name:
        module_dir = module_dir / specific_module
    module_dir = module_dir.resolve()

    if not module_dir.is_dir():
        msg = f"Module directory does not exist. ({module_dir.as_posix()})"
        return Err(ModuleDirDoesNotExist(msg))
    return Ok(module_dir)


def get_check_installed_script(
    module_name: str,
    target: Option[str] = nothing,
) -> Result[Path, GetScriptErrors]:
    """Get the path to the script to check if a module is installed.

    Searches the following of :func:`get_module_dir``{module_name}/check_installed/`
    for the `{target}*` file. If `target` is `Nothing`, it is assumed to
    only contain one file whose path will be returned.

    Args:
        module_name:
        target: target to check for. If `Nothing`, assumes only a single script exists.

    Returns:
        Result containing the Path to the script, or the appropriate error of why the
        path could not be retrieved.
    """

    module_dir_res: Result[Path, DotVaultDirDoesNotExist | ModuleDirDoesNotExist] = (
        get_module_dir(Some(module_name))
    )
    match module_dir_res:
        case Err(DotVaultDirDoesNotExist() | ModuleDirDoesNotExist()) as err:
            return err
        case Ok(module_dir):
            pass

    script_dir: Path = module_dir / "check_installed"
    if not script_dir.is_dir():
        msg = f"Script directory does not exist. ({script_dir.as_posix()})"
        return Err(ScriptDirDoesNotExist(msg))

    pattern = "*"
    for t in target:
        pattern = f"{t}*"

    matching_files: list[Path] = list(script_dir.glob(pattern))
    if len(matching_files) == 0:
        msg = f"Could not find a check_installed script for {module_name}"
        for t in target:
            msg += f" with target {t}."
        msg += f" (script_dir: {script_dir.as_posix()})"
        return Err(ScriptFileDoesNotExist(msg, file_path=script_dir))

    if len(matching_files) > 1:
        file_list: list[str] = [f.as_posix() for f in matching_files]
        file_list_str: str = "\n".join(file_list)
        msg = f"Found more than one check_installed script:\n{file_list_str}"
        return Err(MoreThanOneFileFound(msg))

    return Ok(matching_files[0])


def get_module_install_script(
    module_name: str,
    target: Option[str] = nothing,
) -> Result[Path, GetScriptErrors]:
    """Get the path to the install script

    Searches the following of :func:`get_module_dir``{module_name}/install_scripts/`
    for the `{target}*` file. If `target` is `Nothing`, it is assumed to
    only contain one file whose path will be returned.

    Args:
        module_name: The name of the module.
        target: The name of the target script/environment to use.

    Returns:
        Result containing the Path to the install script to use or FileNotFoundError.
    """

    match get_module_dir(Some(module_name)):
        case Err(err):
            return Err(err)
        case Ok(module_dir):
            pass

    install_script_dir: Path = module_dir / "install_scripts"
    if not install_script_dir.is_dir():
        return Err(ScriptDirDoesNotExist("Install Script directory does not exist."))

    pattern: str = "*"
    match target:
        case Some(t):
            pattern = f"{t}*"
        case Nothing():
            pass

    matching_files: list[Path] = list(install_script_dir.glob(pattern))
    if len(matching_files) == 0:
        msg = (
            "The install script was not found. "
            f"Script Path: '{install_script_dir.as_posix()}', "
            f"target: '{target.unwrap_or('<NONE>')}'"
        )
        err = ScriptFileDoesNotExist(msg=msg, file_path=install_script_dir)
        return Err(err)

    if len(matching_files) > 1:
        filename_list: list[str] = [f.name for f in matching_files]
        filename_list_str: str = ", ".join(filename_list)
        msg = (
            "Found more than one relevant install script. "
            f"Script Path: '{install_script_dir.as_posix()}', "
            f"target: '{target.unwrap_or('<NONE>')}', "
            f"files found: [{filename_list_str}]"
        )
        err = MoreThanOneFileFound(msg=msg)
        return Err(err)

    return Ok(matching_files[0])
