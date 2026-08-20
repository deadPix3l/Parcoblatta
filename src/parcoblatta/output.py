from __future__ import annotations

from contextlib import ExitStack
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import TextIO

    from pydantic import BaseModel

    from .flow import ParcoblattaOutput
    from .models import MatchEvent


def write_output(
    events: Iterable[MatchEvent],
    output: ParcoblattaOutput,
    prompt: PromptTemplate | None = None,
) -> None:
    """Write match events and optional prompt events to configured outputs.

    The intended semantics are fan-out: every event is written to every configured
    file and published to every configured topic.

    :param events: Match events to write.
    :param output: Match event output configuration.
    :param prompt: Optional prompt template and prompt output configuration.
    :return: None.
    """
    with ExitStack() as stack:
        files = open_files(stack, output)

        for event in events:
            write_single_event(event, output, files)

def open_files(stack: ExitStack, output: ParcoblattaOutput) -> list[TextIO]:
    return [
        stack.enter_context(file.open("a", encoding="utf-8"))
        for file in output.file
    ]


def write_single_event(event: BaseModel, output: ParcoblattaOutput, files: list[TextIO]) -> None:
    line = event.model_dump_json() + "\n"
    for file in files:
        file.write(line)

    for topic in output.topic:
        publish_kafka_event(topic, event)


def publish_kafka_event(topic: str, event: BaseModel) -> None:
    """Publish one event to a Kafka topic.

    This intentionally preserves the planned shape from the original sketch:
    ``broker.publish(topic, event)``. The missing piece is choosing/configuring
    the concrete broker or producer object.

    :param topic: Kafka topic to publish to.
    :param event: Event to publish.
    :return: None.
    """
    raise NotImplementedError("Kafka output is not implemented yet")
