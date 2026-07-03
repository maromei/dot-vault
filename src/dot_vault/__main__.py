from pathlib import Path

import doctyper as typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from dot_vault.paths import get_module_dir
from dot_vault.modules import Module, get_module, ReturnFile
from dot_vault.pretty_print import print_two_column_table


app = typer.DocTyper(help="Manage dot files and system setup.")

module_app = typer.DocTyper(help="Manage modules.")
app.add_typer(module_app, name="module")

module_check_app = typer.DocTyper(help="Check the status of modules.")
module_app.add_typer(module_check_app, name="check")


@module_app.command(name="install")
def modules_install(module: str, target: str | None = None):
    """Install a module.

    Args:
        module: Name of the module.
        target: Target environment (e.g., OS or machine name) to install for. If not
            specified, it is assumed the module only contains one target script, and
            that one is used.
    """

    module_obj: Module = get_module(name=module)
    module_obj.install(target=target)


@module_check_app.command(name="installed")
def modules_check_installed(module: str, target: str | None = None):
    """Check if a module is installed

    Args:
        module: Name of the module.
        target: Target environment (e.g., OS or machine name) to check for. If not
            specified, it is assumed the module only contains one target script, and
            that one is used.
    """

    module_obj: Module = get_module(name=module)
    toml_content: ReturnFile | None = module_obj.check_installed_toml(target)
    if toml_content is None:
        raise typer.BadParameter(
            f"The target '{target}' was not found for module '{module}'."
        )

    # since it is a pydantic model where all values need to be serializable,
    # it is assumed that the `str(v)` function will always result in
    # valid usable values.
    table_data: list[tuple[str, str]] = [(k, str(v)) for k, v in toml_content]  # pyright: ignore[reportAny]

    title: str = f"Is {module} installed?"
    print_two_column_table(table_data = table_data, title = title)


@module_app.command(name="list")
def modules_list():
    """List all available modules."""

    module_dir: Path = get_module_dir()
    module_names: list[str] = [d.name for d in module_dir.iterdir() if d.is_dir()]
    modules: list[Module] = [get_module(name) for name in module_names]

    table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))

    table.add_column(style="bold cyan")
    table.add_column()

    for module in modules:
        table.add_row(module.name, module.config.description)

    title = "Available Modules"
    subtitle: str = module_dir.as_posix()

    panel = Panel(
        table, title=title, title_align="left", border_style="dim", subtitle=subtitle
    )

    console = Console()
    console.print(panel)


if __name__ == "__main__":
    app()
