from __future__ import annotations

import logging
from contextlib import ExitStack
from typing import TYPE_CHECKING

from parcoblatta.cli.flow.prompts import render_prompt

from .kafka import flush_kafka, kafka_producer, publish_kafka_event

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import TextIO

    from confluent_kafka import Producer
    from pydantic import BaseModel

    from parcoblatta.cli.flow.config import Output, PromptTemplate
    from parcoblatta.scanner.models import MatchEvent


def write_output(
    events: Iterable[MatchEvent],
    output: Output | None,
    prompts: Iterable[PromptTemplate] = (),
) -> int:
    """Write match events and optional prompt events to configured outputs.

    The intended semantics are fan-out: every event is written to every configured
    file and published to every configured topic.

    :param events: Match events to write.
    :param output: Optional match event output configuration.
    :param prompts: Optional prompt templates and prompt output configurations.
    :return: Number of match events processed.
    """
    count = 0
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
            count += 1
            if output is not None:
                write_single_event(event, files, output.topic, producer, output.stdout)

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

    return count


def open_files(stack: ExitStack, output: Output) -> list[TextIO]:
    return [stack.enter_context(file.open("a", encoding="utf-8")) for file in output.file]


def write_single_event(
    event: BaseModel,
    files: list[TextIO],
    topics: list[str],
    producer: Producer | None,
    stdout: bool = False,
) -> None:
    line = event.model_dump_json() + "\n"

    logger.debug(line)

    if stdout:
        print(line)

    for file in files:
        file.write(line)

    for topic in topics:
        publish_kafka_event(producer, topic, event)


