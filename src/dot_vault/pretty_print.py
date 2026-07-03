from rich.console import Console
from rich.table import Table
from rich.panel import Panel


def get_two_column_table_panel(
    table_data: list[tuple[str, str]],
    title: str | None = None,
    subtitle: str | None = None,
) -> Panel:
    """Build a rich panel mimicing typers two column table for parameters

    Args:
        table_data: List of row entries for the table. One value for each column.
        title: Title displayed above the table (see :class:`rich:rich.panel.Panel`)
        subtitle: subtitle displayed below the table
            (see :class:`rich:rich.panel.Panel`)

    Returns:
        Built :class:`rich:rich.Panel.Panel`.
    """

    table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))

    table.add_column(style="bold cyan")
    table.add_column()

    for key, value in table_data:
        table.add_row(key, value)

    panel = Panel(
        table, title=title, title_align="left", border_style="dim", subtitle=subtitle
    )
    return panel


def print_two_column_table(
    table_data: list[tuple[str, str]],
    title: str | None = None,
    subtitle: str | None = None,
    console: Console | None = None,
):
    """Print a rich panel mimicing typers two column table for parameters

    Args:
        table_data: List of row entries for the table. One value for each column.
        title: Title displayed above the table (see :class:`rich:rich.panel.Panel`)
        subtitle: subtitle displayed below the table
            (see :class:`rich:rich.panel.Panel`)
        console: Console object to use for printing. Will be created if `None`.

    Returns:
        Built :class:`rich:rich.Panel.Panel`.
    """

    panel = get_two_column_table_panel(
        table_data=table_data, title=title, subtitle=subtitle
    )

    if console is None:
        console = Console()

    console.print(panel)
