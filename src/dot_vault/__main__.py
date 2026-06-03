import doctyper as typer

from dot_vault.settings import Module, get_module


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

    module_obj: Module = get_module(name=module)
    module_obj.install(install_script=script)


if __name__ == "__main__":
    app()
