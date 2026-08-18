from __future__ import annotations

import os
import re
import subprocess
import logging
import tomllib
import tempfile
from pathlib import Path
from typing import Any, Literal, overload

from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError

from cflowpy import Option, Some, Result, Ok, Err, nothing, is_err
from dot_vault.errors import (
    ModuleDirErrors,
    GetScriptErrors,
    InstallFailed,
    CheckInstallFailed,
    InvalidReturnFileFormat,
    ModuleConfigDoesNotExist,
    ScriptRunFailed,
)
from dot_vault.paths import (
    get_module_dir,
    get_module_install_script,
    get_check_installed_script,
)
from dot_vault.shell import get_default_shell
from dot_vault.constants import RESULT_FILE_ENV_NAME


LOGGER: logging.Logger = logging.getLogger(__name__)


@overload
def get_module_config_path(
    module_name: str, not_exist_ok: Literal[True] = True
) -> Result[Path, ModuleDirErrors]: ...


@overload
def get_module_config_path(
    module_name: str, not_exist_ok: Literal[False]
) -> Result[Path, ModuleDirErrors | ModuleConfigDoesNotExist]: ...


def get_module_config_path(
    module_name: str, not_exist_ok: bool = True
) -> (
    Result[Path, ModuleDirErrors]
    | Result[Path, ModuleDirErrors | ModuleConfigDoesNotExist]
):
    """Get the path to a modules config file.

    Expected path: :func:`get_module_dir``{module_name}/module_config.toml`.

    Args:
        module_name:
        not_exist_ok: Returns the path to the file, even if it does not exist.

    Returns:
        Result containing the Path to the module config file or a relevant error.
    """

    match get_module_dir(Some(module_name)):
        case Ok(module_dir):
            config_path: Path = module_dir / "module_config.toml"

            if not_exist_ok or config_path.is_file():
                return Ok(config_path.resolve())

            msg = (
                "The path to the module_config.toml could not be found: "
                f"{config_path.as_posix()}"
            )

            return Err(ModuleConfigDoesNotExist(msg=msg, file_path=config_path))
        case Err(err):
            return Err(err)


def get_module(
    name: str,
) -> Result[Module, ModuleDirErrors]:
    """Create a :class:`Module` object from the name.

    Args:
        name:

    Returns:
        A :class:`Module` object if succesfull. Even if no config file could be
        found, a default object will be created.
    """

    module_dir_result = get_module_dir(Some(name))
    match module_dir_result:
        case Err() as err: return err  # fmt: off
        case Ok(module_dir): pass  # fmt: off

    config_path_result = get_module_config_path(module_name=name, not_exist_ok=True)
    match config_path_result:
        case Err() as err: return err  # fmt: off
        case Ok(module_config_path): pass  # fmt: off

    if module_config_path.is_file():
        with open(module_config_path, "rb") as f:
            module_config_dict: dict[str, Any] = tomllib.load(f)
        config = ModuleConfig.model_validate(module_config_dict)
    else:
        config = ModuleConfig()
    return Ok(Module(name, module_dir, config))


class Module:
    """Representation of a module with all its content and functions."""

    name: str
    path: Path
    config: ModuleConfig

    def __init__(self, name: str, path: Path, config: ModuleConfig):
        self.name = name
        self.path = path
        self.config = config

    def check_installed_toml(
        self,
        target: Option[str] = nothing,
    ) -> Result[ReturnFile, CheckInstallFailed]:
        """Check if the module is installed.

        Args:
            target: target to check for.
            If `Nothing`, assumes only a single script exists.

        Returns:
            Result containing Option[ReturnFile], or error.
        """

        script_result: Result[Path, GetScriptErrors] = get_check_installed_script(
            module_name=self.name, target=target
        )

        match script_result:
            case Err(err):
                target_str = target.unwrap_or("<NONE>")
                msg = (
                    f"Failed to check whether the module '{self.name}' is installed. "
                    f"(target: '{target_str}')"
                )
                return_err = CheckInstallFailed(msg=msg, source=err)
                LOGGER.error(msg, exc_info=return_err)
                return Err(return_err)
            case Ok(script_path):
                pass

        script_path_str: str = script_path.as_posix()

        fd, temp_file_path_str = tempfile.mkstemp(suffix=".toml")
        os.close(fd)
        temp_file_path = Path(temp_file_path_str)

        child_env: dict[str, Any] = os.environ.copy()
        child_env[RESULT_FILE_ENV_NAME] = temp_file_path.as_posix()

        completed_process = subprocess.run(
            [script_path_str],
            shell=True,
            executable=self.config.shell,
            env=child_env,
        )

        try:
            completed_process.check_returncode()
            with open(temp_file_path, "rb") as f:
                return_file_content: dict[str, Any] = tomllib.load(f)
        except subprocess.CalledProcessError as e:
            target_str = target.unwrap_or("<NONE>")
            msg = (
                f"Failed to run check_installed script for module '{self.name}' "
                f"with target '{target_str}'."
            )
            run_error = ScriptRunFailed(msg=msg, source=e)
            return_error = CheckInstallFailed(msg=msg, source=run_error)
            LOGGER.error(msg, exc_info=return_error)
            return Err(return_error)
        finally:
            temp_file_path.unlink()

        try:
            return_file: ReturnFile = ReturnFile.model_validate(return_file_content)
        except ValidationError as e:
            target_str = target.unwrap_or("<NONE>")
            msg = (
                "The return file format from the check_installed script of module "
                f"'{self.name}' with target '{target_str}' is invalid."
            )
            format_error = InvalidReturnFileFormat(msg=msg, source=e)
            return_error = CheckInstallFailed(msg=msg, source=format_error)
            LOGGER.error(msg, exc_info=return_error)
            return Err(return_error)

        return Ok(return_file)

    def check_installed(
        self, target: Option[str] = nothing
    ) -> Result[bool, CheckInstallFailed]:
        """Check if the module is installed.

        Args:
            target: target to check for.
                If `Nothing`, assumes only a single script exists.

        Returns:
            Result containing Option[bool], or error.
        """

        match self.check_installed_toml(target):
            case Ok(file):
                return Ok(file.installed)
            case err:
                return err

    def install(
        self,
        target: Option[str] = nothing,
    ) -> Result[None, InstallFailed]:
        # TODO: check for cyclic dependencies
        for dependency in self.config.dependencies:
            match get_module(dependency):
                case Err(err):
                    msg = (
                        f"Unable to install the module '{dependency}' as a "
                        f"dependency of '{self.name}'."
                    )
                    return Err(InstallFailed(msg=msg, source=err))
                case Ok(module): pass  # fmt: off

            install_result = module.install(target=target)
            if is_err(install_result):
                return install_result

        match get_module_install_script(self.name, target):
            case Err(err):
                target_str = target.unwrap_or("<NONE>")
                msg = (
                    f"Failed getting install script for module '{self.name}'"
                    f" with target '{target_str}'."
                )
                return Err(InstallFailed(msg=msg, source=err))

            case Ok(install_script_path): pass  # fmt: off

        path_str: str = install_script_path.as_posix()
        completed_process = subprocess.run(
            [path_str],
            shell=True,
            executable=self.config.shell,
        )
        try:
            completed_process.check_returncode()
        except subprocess.CalledProcessError as e:
            target_str = target.unwrap_or("<NONE>")
            msg = (
                f"Install script failed for module '{self.name}'"
                f" with target '{target_str}'."
            )
            script_err = ScriptRunFailed(msg=msg, source=e)
            err = InstallFailed(
                f"Unable to install the module '{self.name}'", source=script_err
            )
            return Err(err)
        return Ok(None)


class ModuleConfig(BaseModel):
    """Pydantic Model for the module config"""

    dependencies: list[str] = []  # Mutable defaults is a working feature in pydantic
    shell: str = Field(default_factory=get_default_shell)
    description: str = ""

    @field_validator("description", mode="after")
    @classmethod
    def clean_description(cls, value: str) -> str:
        """Remove leading whitspace consistent through all lines."""

        match: re.Match[str] | None = re.search(r"^\s+(?=\S)", value)
        if match is not None:
            string_to_replace = r"(^|\n)?" + match.group()
            value = re.sub(string_to_replace, "\n", value)

        value = value.strip(" \t\r\n")
        return value

    @model_validator(mode="before")
    @classmethod
    def unwrap_top_category(cls, data: Any) -> Any:  # pyright: ignore[reportAny]
        """Removes outer `[dot-vault.module]` category if present.

        Ensures that the toml file to be parsed either has no top category, or
        `[dot-vault.module]`.

        Raises:
            ValidationError: When the 'dot-vault' category is present without the
                'module' subcategory.

        Args:
            data: object to validate

        Returns:
            Input object with the `[dot-vault.module]` category stripped.
        """

        if not isinstance(data, dict) or "dot-vault" not in data.keys():
            return data  # pyright: ignore[reportUnknownVariableType]

        data = data["dot-vault"]  # pyright: ignore[reportUnknownVariableType]
        if not isinstance(data, dict) or "module" not in data.keys():
            raise ValidationError(
                "The config contains the 'dot-vault' category, "
                "without the 'module' category. Either [dot-vault.module] needs "
                "to be the top level category, or nothing at all."
            )

        return data["module"]  # pyright: ignore[reportUnknownVariableType]


class ReturnFile(BaseModel):
    """Pydantic model for the file containing output of the check_installed process."""

    installed: bool
