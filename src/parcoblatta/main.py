from __future__ import annotations

from pathlib import Path

import fire

from .flow import ParcoblattaFlow
from .output import write_output
from .scanner import match_events


class Parcoblatta:
    """Fire-exposed CLI adapter."""

    def run(self, config: Path | str) -> None:
        """Run a Parcoblatta flow from YAML config.

        :param config: YAML config file.
        :return: None.
        """
        flow = ParcoblattaFlow.from_yaml(Path(config))
        for rule in flow.rules:
            write_output(
                match_events(flow.code, rule.query),
                rule.output,
            )


def main() -> None:
    """Run the Fire CLI adapter.

    :return: None.
    """
    fire.Fire(Parcoblatta)


if __name__ == "__main__":
    main()
