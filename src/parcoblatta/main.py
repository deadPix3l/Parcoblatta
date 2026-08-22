from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from parcoblatta.cli.flow.config import Flow
from parcoblatta.cli.flow.output import write_output
from parcoblatta.cli.lint.lint import lint as run_lint
from parcoblatta.scanner.scanner import match_events

app = typer.Typer(no_args_is_help=True)


@app.callback()
def cli() -> None:
    """Parcoblatta command line interface."""


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
    flow = Flow.from_yaml(config)
    for rule in flow.rules:
        write_output(
            match_events(flow.code, rule.query),
            rule.output,
            rule.prompt,
        )


@app.command()
def lint(
    code_dir: Annotated[
        Path,
        typer.Argument(
            help="Python file or directory to lint.",
        ),
    ] = Path("src/"),
    query: Annotated[
        list[Path] | None,
        typer.Option(
            "--query",
            "-q",
            help="Query file or directory. May be passed multiple times.",
        ),
    ] = None,
    quiet: Annotated[bool, typer.Option("--quiet", help="Only print the final count.")] = False,
    limit: Annotated[int | None, typer.Option("--limit", help="Maximum violations to report.")] = None,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable ANSI colors.")] = False,
    stats: Annotated[bool, typer.Option("--stats", help="Show counts by rule.")] = False,
    jsonl: Annotated[bool, typer.Option("--jsonl", help="Emit JSON Lines.")] = False,
) -> None:
    """Scan Python files for tree-sitter lint violations."""
    violation_count = run_lint(
        code_dir=code_dir,
        query=query,
        quiet=quiet,
        limit=limit,
        no_color=no_color,
        stats=stats,
        jsonl=jsonl,
    )
    if violation_count:
        raise typer.Exit(1)


def main() -> None:
    """Run the Typer CLI adapter."""
    app()


if __name__ == "__main__":
    main()
