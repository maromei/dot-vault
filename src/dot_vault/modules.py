from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator, ValidationError

from dot_vault.errors import InstallFailed
from dot_vault.paths import get_module_dir
from dot_vault.shell import get_default_shell


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


def get_module_install_script(module_name: str, install_script: str | None) -> Path:
    """Get the path to the install script

    Searches the following of :func:`get_module_dir``{module_name}/install_scripts/`
    for the `{install_script}*` file. If `install_script` is `None`, it is assumed to
    only contain one file whose path will be returned. An error will be raised if
    multiple files are found for the given pattern.

    Raises:
        FileNotFoundError: :func:`get_module_dir``{module_name}/install_scripts/`
            directory does not exist, the given install script was not found, or
            more than one matching install script was found.

    Args:
        module_name: The name of the module.
        install_script: The name of the install script to use. The given string will
            be matched to the beginning of the filename. Supports 'glob' syntax.

    Returns:
        The path to the install script to use.
    """

    module_dir: Path = get_module_dir(module_name)
    install_script_dir: Path = module_dir / "install_scripts"
    if not install_script_dir.is_dir():
        raise FileNotFoundError("Install Script directory does not exist.")

    pattern: str = "*"
    if install_script is not None:
        pattern = f"{install_script}*"

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

    def install(self, install_script: str | None = None):

        # TODO: check for cyclic dependencies
        for dependency in self.config.dependencies:
            module: Module = get_module(dependency)
            module.install(install_script=install_script)

        install_script_path: Path = get_module_install_script(self.name, install_script)
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
