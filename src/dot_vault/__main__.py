import doctyper as typer

from cflowpy import Some, Nothing, Ok, Err, Result
from dot_vault.errors import ModuleDirErrors
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

    target_opt = Some(target) if target is not None else Nothing()
    match get_module(name=module):
        case Ok(module_obj):
            match module_obj.install(target=target_opt):
                case Ok(_):
                    pass
                case Err(err):
                    raise err
        case Err(err):
            raise err


@module_check_app.command(name="installed")
def modules_check_installed(module: str, target: str | None = None):
    """Check if a module is installed

    Args:
        module: Name of the module.
        target: Target environment (e.g., OS or machine name) to check for. If not
            specified, it is assumed the module only contains one target script, and
            that one is used.
    """

    target_opt = Some(target) if target is not None else Nothing()
    module_result: Result[Module, ModuleDirErrors] = get_module(name=module)
    module_obj: Module = module_result.unwrap_or_raise()
    is_installed_result = module_obj.check_installed_toml(target=target_opt)
    is_installed_toml: ReturnFile = is_installed_result.unwrap_or_raise()

    table_data_any: list[tuple[str, bool]] = list(
        is_installed_toml.model_dump().items()
    )
    table_data: list[tuple[str, str]] = [(f[0], str(f[1])) for f in table_data_any]

    title = f"Is module '{module}' installed?"
    subtitle = f"Target: '{target_opt.unwrap_or('<NONE>')}'"

    print_two_column_table(table_data=table_data, title=title, subtitle=subtitle)


@module_app.command(name="list")
def modules_list():
    """List all available modules."""

    match get_module_dir():
        case Ok(module_dir):
            module_names: list[str] = [
                d.name for d in module_dir.iterdir() if d.is_dir()
            ]
            modules: list[Module] = []
            for name in module_names:
                match get_module(name):
                    case Ok(module):
                        modules.append(module)
                    case Err(err):
                        raise err

            table_data: list[tuple[str, str]] = [
                (module.name, module.config.description) for module in modules
            ]

            title = "Available Modules"
            subtitle: str = module_dir.as_posix()

            print_two_column_table(
                table_data=table_data, title=title, subtitle=subtitle
            )
        case Err(err):
            raise err


if __name__ == "__main__":
    app()
