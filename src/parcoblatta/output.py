from __future__ import annotations

from contextlib import ExitStack
from typing import TYPE_CHECKING

from .prompts import render_prompt

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import TextIO

    from confluent_kafka import Producer
    from pydantic import BaseModel

    from .flow import KafkaConfig, ParcoblattaOutput, PromptTemplate
    from .models import MatchEvent


def write_output(
    events: Iterable[MatchEvent],
    output: ParcoblattaOutput | None,
    prompts: Iterable[PromptTemplate] = (),
) -> None:
    """Write match events and optional prompt events to configured outputs.

    The intended semantics are fan-out: every event is written to every configured
    file and published to every configured topic.

    :param events: Match events to write.
    :param output: Optional match event output configuration.
    :param prompts: Optional prompt templates and prompt output configurations.
    :return: None.
    """
    prompts = list(prompts)
    with ExitStack() as stack:
        files = open_files(stack, output) if output else []
        producer = kafka_producer(output.kafka) if output and output.topic else None
        prompt_files = [open_files(stack, prompt.output) for prompt in prompts]
        prompt_producers = [
            kafka_producer(prompt.output.kafka) if prompt.output.topic else None
            for prompt in prompts
        ]

        for event in events:
            if output is not None:
                write_single_event(event, files, output.topic, producer)

            for prompt, files, producer in zip(
                prompts,
                prompt_files,
                prompt_producers,
                strict=True,
            ):
                write_single_event(
                    render_prompt(event, prompt),
                    files,
                    prompt.output.topic,
                    producer,
                )

        flush_kafka(producer)
        for producer in prompt_producers:
            flush_kafka(producer)


def open_files(stack: ExitStack, output: ParcoblattaOutput) -> list[TextIO]:
    return [
        stack.enter_context(file.open("a", encoding="utf-8"))
        for file in output.file
    ]


def write_single_event(
    event: BaseModel,
    files: list[TextIO],
    topics: list[str],
    producer: Producer | None,
) -> None:
    line = event.model_dump_json() + "\n"
    for file in files:
        file.write(line)

    for topic in topics:
        publish_kafka_event(producer, topic, event)


def kafka_producer(config: KafkaConfig) -> Producer:
    from confluent_kafka import Producer

    return Producer(
        {
            "bootstrap.servers": ",".join(config.bootstrap_servers),
            "client.id": config.client_id,
        },
    )


def publish_kafka_event(producer: Producer | None, topic: str, event: BaseModel) -> None:
    """Publish one event to a Kafka topic.

    :param producer: Kafka producer.
    :param topic: Kafka topic to publish to.
    :param event: Event to publish.
    :return: None.
    """
    if producer is None:
        raise ValueError("producer is required when topics are configured")

    producer.produce(
        topic,
        value=event.model_dump_json().encode("utf-8"),
    )
    producer.poll(0)


def flush_kafka(producer: Producer | None) -> None:
    if producer is not None:
        producer.flush()
