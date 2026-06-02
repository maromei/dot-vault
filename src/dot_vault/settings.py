from pathlib import Path


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


def get_module_dir() -> Path:
    """Get the directory containing the module config.

    Currently only searches for `modules/` in the directory given by
    :func:`get_dot_vault_dir`.

    Raises:
        FileNotFoundError: If the directory does not exist.

    Returns:
        Path to the module directory.
    """

    vault_dir: Path = get_dot_vault_dir()
    module_dir: Path = vault_dir / "modules/"
    module_dir = module_dir.resolve()

    if not module_dir.is_dir():
        raise FileNotFoundError("Module directory does not exist.")
    return module_dir


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

    module_dir: Path = get_module_dir() / module_name
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
