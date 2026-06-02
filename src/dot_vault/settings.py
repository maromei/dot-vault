import tomllib
from pathlib import Path
from pydantic import BaseModel


def get_dot_vault_dir() -> Path:
    """Get the directory containing the dot-vault config.

    Currently only searches for `~/config/dot-vault/`.
    Raises:
        FileNotFoundError: If the directory does not exist.

    Returns:
        Path to the dot-vault directory.
    """
    dotvault_dir = Path("~/.config/dot-vault/").resolve()
    if not dotvault_dir.is_dir():
        raise FileNotFoundError("The dot-vault directory does not exist.")
    return dotvault_dir


def get_module_dir(name: str | None = None) -> Path:
    """Get the directory containing the module config.

    Currently only searches for `modules/` in the directory given by
    :func:`get_dot_vault_dir`. If `name` is not `None`, the directory of the
    specific module will be returned `modules/{name}/`.

    Raises:
        FileNotFoundError: If the directory does not exist.

    Args:
        name: Optional name to a specific module directory. Otherwise return
            path to the general modules directory.

    Returns:
        Path to the module directory.
    """

    vault_dir: Path = get_dot_vault_dir()
    module_dir: Path = vault_dir / "modules/"
    if name is not None:
        module_dir = module_dir / name
    module_dir = module_dir.resolve()

    if not module_dir.is_dir():
        raise FileNotFoundError("Module directory does not exist.")
    return module_dir


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

    raise FileNotFoundError("The path to the module_config.toml could not be foud.")


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


class Module:
    name: str
    path: Path
    config: ModuleConfig

    def __init__(self, name: str):
        module_dir: Path = get_module_dir() / name

        self.name = name
        self.path = module_dir


class ModuleConfig(BaseModel):
    dependencies: list[str] = []  # Mutable defaults is a working feature in pydantic
