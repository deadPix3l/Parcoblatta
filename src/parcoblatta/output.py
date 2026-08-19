from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .flow import ParcoblattaOutput
    from .models import CaptureEvent


def write_output(events: Iterable[CaptureEvent], output: ParcoblattaOutput) -> None:
    """Write capture events to configured outputs.

    The intended semantics are fan-out: every event is written to every configured
    file and published to every configured topic.

    :param events: Capture events to write.
    :param output: Output configuration.
    :return: None.
    """
    for event in events:
        line = event.model_dump_json() + "\n"
        for file in output.file:
            with file.open("a", encoding="utf-8") as file_handle:
                file_handle.write(line)

        for topic in output.topic:
            publish_kafka_event(topic, event)


def publish_kafka_event(topic: str, event: CaptureEvent) -> None:
    """Publish one capture event to a Kafka topic.

    This intentionally preserves the planned shape from the original sketch:
    ``broker.publish(topic, event)``. The missing piece is choosing/configuring
    the concrete broker or producer object.

    :param topic: Kafka topic to publish to.
    :param event: Capture event to publish.
    :return: None.
    """
    raise NotImplementedError("Kafka output is not implemented yet")
