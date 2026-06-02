from pathlib import Path

import doctyper as typer

from dot_vault.settings import get_module_install_script


app = typer.Typer(help="Manage dot files and system setup.")

module_app = typer.Typer(help="Manage modules.")
app.add_typer(module_app, name="module")


@module_app.command(name="install")
def modules_install(module: str, script: str | None = None):
    """Install a module.

    Args:
        module_name: Name of the module.
        script: Name of the install script to use. If not specified, it is assumed to
            only contain one script, and that one is used.
    """

    install_script: Path = get_module_install_script(module, script)
    print(install_script)


if __name__ == "__main__":
    app()
