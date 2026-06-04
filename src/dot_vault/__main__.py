from pathlib import Path

import doctyper as typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from dot_vault.paths import get_module_dir
from dot_vault.modules import Module, get_module


app = typer.DocTyper(help="Manage dot files and system setup.")

module_app = typer.DocTyper(help="Manage modules.")
app.add_typer(module_app, name="module")


@module_app.command(name="install")
def modules_install(module: str, script: str | None = None):
    """Install a module.

    Args:
        module: Name of the module.
        script: Name of the install script to use. If not specified, it is assumed to
            only contain one script, and that one is used.
    """

    module_obj: Module = get_module(name=module)
    module_obj.install(install_script=script)


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
