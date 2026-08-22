from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from parcoblatta.flow.config import ParcoblattaFlow
from parcoblatta.flow.output import write_output
from parcoblatta.flow.scanner import match_events

app = typer.Typer(no_args_is_help=True)


@app.command()
def run(
    config: Annotated[
        Path,
        typer.Argument(
            exists=True,
            dir_okay=False,
            readable=True,
            help="YAML flow config file.",
        ),
    ],
) -> None:
    """Run a Parcoblatta flow from YAML config."""
    flow = ParcoblattaFlow.from_yaml(config)
    for rule in flow.rules:
        write_output(
            match_events(flow.code, rule.query),
            rule.output,
            rule.prompt,
        )


def main() -> None:
    """Run the Typer CLI adapter."""
    app()


if __name__ == "__main__":
    main()
