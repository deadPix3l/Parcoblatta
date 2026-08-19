from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Iterable, Literal

import fire


def load_queries(paths: Iterable[Path], *, language: LanguageName = "python") -> list[QuerySpec]:
    """Load Tree-sitter query files.

    :param paths: Query files or directories containing ``*.scm`` files.
    :param language: Language the queries target.
    :return: Loaded query specs.
    """

    specs: list[QuerySpec] = []
    for path in paths:
        query_files = sorted(path.rglob("*.scm")) if path.is_dir() else [path]
        for query_file in query_files:
            specs.append(
                QuerySpec(
                    name=query_file.stem,
                    path=query_file,
                    source=query_file.read_text(encoding="utf-8"),
                    language=language,
                )
            )
    return specs


def write_output(events: Iterable[CaptureEvent], output: ParcoblattaOutput) -> None:
    """Write capture events as JSON Lines and/or kafka.

    :param events: Capture events to serialize.
    :param output: Where to write events to.
    :return: None.
    """

    for event in events:
        for file in output.file:
            with file.open(mode="a", encoding="utf-8") as f:
                f.write(event)

        for topic in output.topic:
            broker.publish(topic, event)


def run_scan(config: ScanConfig) -> None:
    """Run a scan from validated configuration.

    :param config: Validated scan configuration.
    :return: None.
    """

    raise NotImplementedError("Tree-sitter scanning is not implemented yet")


class Parcoblatta:
    """Fire-exposed CLI adapter."""

    def scan(
        self,
        path: str,
        query: str | list[str],
        sink: Literal["jsonl", "kafka"] = "jsonl",
        output: str | None = None,
        topic: str | None = None,
    ) -> None:
        """Build a ScanConfig from CLI flags and run it.

        :param path: File or directory to scan.
        :param query: Query file/directory, or a list of them.
        :param sink: Sink type.
        :param output: JSONL output path.
        :param topic: Kafka topic.
        :return: None.
        """

        queries = [query] if isinstance(query, str) else query
        sink_config: Sink
        if sink == "jsonl":
            sink_config = JsonlSink(output=Path(output) if output else None)
        else:
            if topic is None:
                raise ValueError('topic is required when sink="kafka"')
            sink_config = KafkaSink(topic=topic)

        run_scan(
            ScanConfig(
                path=Path(path),
                queries=[Path(item) for item in queries],
                sink=sink_config,
            )
        )


if __name__ == "__main__":
    fire.Fire(Parcoblatta)
