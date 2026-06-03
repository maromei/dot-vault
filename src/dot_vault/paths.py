"""Contains function retrieving the default or expected project dot-vault structure.

F.e. eventhough a :mod:`dot_vault.modules` module exists, the :func:`get_module_dir`
function is still found here, since it retrieves the path within the default
structure.
"""

from __future__ import annotations

from pathlib import Path


def get_dot_vault_dir() -> Path:
    """Get the directory containing the dot-vault config.

    Currently only searches for `~/config/dot-vault/`.
    Raises:
        FileNotFoundError: If the directory does not exist.

    Returns:
        Path to the dot-vault directory.
    """

    dotvault_dir = Path.home() / ".config/dot-vault/"
    dotvault_dir = dotvault_dir.resolve()

    if not dotvault_dir.is_dir():
        raise FileNotFoundError(
            f"The dot-vault directory does not exist. '{dotvault_dir.as_posix()}'"
        )
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
