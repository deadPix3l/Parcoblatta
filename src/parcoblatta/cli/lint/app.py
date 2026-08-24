from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from parcoblatta.cli.lint.config import LintConfig
from parcoblatta.cli.lint.lint import lint as run_lint

app = typer.Typer()


@app.command()
def lint(
    code_dir: Annotated[
        Path | None,
        typer.Argument(
            help="Python file or directory to lint. Defaults to configured code paths.",
        ),
    ] = None,
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
    config: Annotated[
        Path,
        typer.Option("--config", help="Project config file containing Parcoblatta lint settings."),
    ] = Path("pyproject.toml"),
    select: Annotated[
        list[str] | None,
        typer.Option("--select", help="Only run rules with this name. May be passed multiple times."),
    ] = None,
    ignore: Annotated[
        list[str] | None,
        typer.Option("--ignore", help="Skip rules with this name. May be passed multiple times."),
    ] = None,
    exclude: Annotated[
        list[str] | None,
        typer.Option(
            "--exclude",
            help="Skip files or directories matching this name or glob. May be passed multiple times.",
        ),
    ] = None,
    no_fail: Annotated[bool, typer.Option("--no-fail", help="Exit 0 even when violations exist.")] = False,
) -> None:
    """Scan Python files for tree-sitter lint violations."""
    lint_config = LintConfig.from_pyproject(config)
    violation_count = run_lint(
        code=[code_dir] if code_dir is not None else lint_config.code,
        query=query or lint_config.queries,
        quiet=quiet or lint_config.quiet,
        limit=limit if limit is not None else lint_config.limit,
        no_color=no_color or lint_config.no_color,
        stats=stats or lint_config.stats,
        jsonl=jsonl or lint_config.format == "jsonl",
        select=select or lint_config.select,
        ignore=ignore or lint_config.ignore,
        exclude=exclude or lint_config.exclude,
    )
    if violation_count and lint_config.fail and not no_fail:
        raise typer.Exit(1)
