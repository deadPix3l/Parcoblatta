from __future__ import annotations

import typer

from parcoblatta.cli.flow.app import app as flow_app
from parcoblatta.cli.lint.app import app as lint_app

app = typer.Typer(no_args_is_help=True)
app.add_typer(flow_app)
app.add_typer(lint_app)


@app.callback()
def cli() -> None:
    """Parcoblatta command line interface."""


def main() -> None:
    """Run the Typer CLI adapter."""
    app()


if __name__ == "__main__":
    main()
