from __future__ import annotations

import os
import re
import subprocess
import tomllib
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError

from dot_vault.errors import (
    InstallFailed,
    CheckInstalledFailed,
    InvalidReturnFileFormat,
)
from dot_vault.paths import get_module_dir, get_check_installed_script
from dot_vault.shell import get_default_shell
from dot_vault.constants import RESULT_FILE_ENV_NAME


def get_module_config_path(module_name: str, not_exist_ok: bool = True) -> Path:
    """Get the path to a modules config file.

    Expected path: :func:`get_module_dir``{module_name}/module_config.toml`.

    Raises:
        FileNotFoundError: If `not_exist_ok = False` and the file does not exist.

    Args:
        module_name:
        not_exist_ok: Returns the path to the file, even if it does not exist.

    Returns:
        Path to the module config file.
    """

    module_dir: Path = get_module_dir(module_name)
    config_path: Path = module_dir / "module_config.toml"

    if not_exist_ok or config_path.is_file():
        return config_path.resolve()

    raise FileNotFoundError("The path to the module_config.toml could not be found.")


def get_module_install_script(module_name: str, target: str | None) -> Path:
    """Get the path to the install script

    Searches the following of :func:`get_module_dir``{module_name}/install_scripts/`
    for the `{target}*` file. If `target` is `None`, it is assumed to
    only contain one file whose path will be returned. An error will be raised if
    multiple files are found for the given pattern.

    Raises:
        FileNotFoundError: :func:`get_module_dir``{module_name}/install_scripts/`
            directory does not exist, the given install script was not found, or
            more than one matching install script was found.

    Args:
        module_name: The name of the module.
        target: The name of the target script/environment to use. The given string
            will be matched to the beginning of the filename. Supports 'glob' syntax.

    Returns:
        The path to the install script to use.
    """

    module_dir: Path = get_module_dir(module_name)
    install_script_dir: Path = module_dir / "install_scripts"
    if not install_script_dir.is_dir():
        raise FileNotFoundError("Install Script directory does not exist.")

    pattern: str = "*"
    if target is not None:
        pattern = f"{target}*"

    matching_files: list[Path] = list(install_script_dir.glob(pattern))
    if len(matching_files) == 0:
        raise FileNotFoundError("The install script name was not found.")

    if len(matching_files) > 1:
        raise FileNotFoundError("Found more than 1 relevant install script.")

    return matching_files[0]


def get_module(name: str) -> Module:
    return Module(name)


class Module:
    """Representation of a module with all its content and functions."""

    name: str
    path: Path
    config: ModuleConfig

    def __init__(self, name: str):
        module_dir: Path = get_module_dir(name)
        module_config_path: Path = get_module_config_path(name, not_exist_ok=True)

        if module_config_path.is_file():
            with open(module_config_path, "rb") as f:
                module_config_dict: dict[str, Any] = tomllib.load(f)  # pyright: ignore[reportExplicitAny]
            self.config = ModuleConfig.model_validate(module_config_dict)
        else:
            self.config = ModuleConfig()

        self.name = name
        self.path = module_dir

    def check_installed_toml(self, target: str | None) -> ReturnFile | None:
        """Check if the module is installed.

        Args:
            target: target to check for. If `None`, assumes only a single script exists.

        Returns:
            Toml content of the script if the module is installed,
            or `None` if no `check_installed` script exists.
        """

        script_path: Path | None = get_check_installed_script(
            module_name=self.name, target=target
        )
        if script_path is None:
            return None

        script_path_str: str = script_path.as_posix()

        fd, temp_file_path_str = tempfile.mkstemp(suffix=".toml")
        os.close(fd)
        temp_file_path = Path(temp_file_path_str)

        child_env: dict[str, Any] = os.environ.copy()  # pyright: ignore[reportExplicitAny]
        child_env[RESULT_FILE_ENV_NAME] = temp_file_path.as_posix()

        completed_process = subprocess.run(
            [script_path_str], shell=True, executable=self.config.shell, env=child_env
        )

        try:
            completed_process.check_returncode()
            with open(temp_file_path, "rb") as f:
                return_file_content: dict[str, Any] = tomllib.load(f)  # pyright: ignore[reportExplicitAny]
        except subprocess.CalledProcessError as e:
            raise CheckInstalledFailed(
                "Failed to run check_installed script for module "
                f"'{self.name}' with target '{target}'."
            ) from e
        finally:
            temp_file_path.unlink()

        try:
            return_file: ReturnFile = ReturnFile.model_validate(return_file_content)
        except ValidationError as e:
            raise InvalidReturnFileFormat(
                "The return file format from the check_installed script of module "
                f"'{self.name}' with target '{target}' is invalid."
            ) from e

        return return_file

    def check_installed(self, target: str | None) -> bool | None:
        """Check if the module is installed.

        Args:
            target: target to check for. If `None`, assumes only a single script exists.

        Returns:
            If the module is installed, or `None` if no `check_installed` script exists.
        """

        return_file: ReturnFile | None = self.check_installed_toml(target)
        if return_file is None:
            return None
        return return_file.installed

    def install(self, target: str | None = None):
        # TODO: check for cyclic dependencies
        for dependency in self.config.dependencies:
            module: Module = get_module(dependency)
            module.install(target=target)

        install_script_path: Path = get_module_install_script(self.name, target)
        path_str: str = install_script_path.as_posix()
        completed_process = subprocess.run(
            [path_str],
            shell=True,
            executable=self.config.shell,
        )
        try:
            completed_process.check_returncode()
        except subprocess.CalledProcessError as e:
            raise InstallFailed(f"Unable to install the module '{self.name}'") from e


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
    def unwrap_top_category(cls, data: Any) -> Any:  # pyright: ignore[reportExplicitAny, reportAny]
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
