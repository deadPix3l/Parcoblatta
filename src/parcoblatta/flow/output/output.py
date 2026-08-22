from __future__ import annotations

from contextlib import ExitStack
from typing import TYPE_CHECKING

from parcoblatta.flow.prompts import render_prompt

from .kafka import flush_kafka, kafka_producer, publish_kafka_event

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import TextIO

    from confluent_kafka import Producer
    from pydantic import BaseModel

    from parcoblatta.flow.config import ParcoblattaOutput, PromptTemplate
    from parcoblatta.models.models import MatchEvent


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
    return [stack.enter_context(file.open("a", encoding="utf-8")) for file in output.file]


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


