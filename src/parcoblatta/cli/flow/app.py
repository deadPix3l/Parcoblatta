from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer

from parcoblatta.cli.flow.config import load_flow_config, load_flow_settings
from parcoblatta.cli.flow.output import write_output
from parcoblatta.scanner.scanner import match_events

logger = logging.getLogger(__name__)
app = typer.Typer()


@app.command()
def run(
    config: Annotated[
        Path | None,
        typer.Argument(
            dir_okay=False,
            readable=True,
            help="YAML flow config file. If omitted, uses [tool.parcoblatta.flow].default.",
        ),
    ] = None,
    log_level: Annotated[
        str | None,
        typer.Option("--log-level", help="Python logging level for flow execution."),
    ] = None,
) -> None:
    """Run a Parcoblatta flow from YAML config."""
    flow_settings = load_flow_settings(config) if config is None or config.suffix == ".toml" else None
    effective_log_level = log_level or (flow_settings.log_level if flow_settings else "INFO")
    logging.basicConfig(level=effective_log_level.upper(), format="%(levelname)s %(message)s")
    logger.info("loading flow config: %s", config)
    flow = load_flow_config(config)
    logger.info("loaded flow with %d rule(s)", len(flow.rules))
    logger.debug(flow.model_dump_json(indent=4))

    total = 0
    for index, rule in enumerate(flow.rules, start=1):
        logger.info("running rule %d/%d: %s", index, len(flow.rules), rule.query.name or "<unnamed>")
        count = write_output(
            match_events(flow.code, rule.query),
            rule.output,
            rule.prompt,
        )
        total += count
        logger.info("finished rule %d/%d: %d match event(s)", index, len(flow.rules), count)

    logger.info("flow complete: %d total match event(s)", total)
