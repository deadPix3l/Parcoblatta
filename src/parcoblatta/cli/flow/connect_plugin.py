from __future__ import annotations

import asyncio
import logging
from typing import Annotated, Any, Self

from pydantic import BeforeValidator, Field, ValidationError, model_validator

from parcoblatta.cli.flow.config.flow import Flow, Rule
from parcoblatta.cli.flow.config.prompt import PromptTemplate
from parcoblatta.cli.flow.prompts import render_prompt
from parcoblatta.scanner.scanner import match_events_from_source
from parcoblatta.scanner.validators import ensure_list

try:
    import redpanda_connect

    lib_available = True
except ImportError:  # pragma: no cover - exercised in environments without the SDK

    class RedPandaUnavailable:
        """Fallback object used when the Redpanda Connect SDK is unavailable."""

        @staticmethod
        def Message(*args: Any, **kwargs: Any) -> None:
            raise RuntimeError("redpanda_connect is required to create processor messages")

        @staticmethod
        def processor_main(*args: Any, **kwargs: Any) -> None:
            raise RuntimeError("redpanda_connect is required to run this processor")

    redpanda_connect = RedPandaUnavailable
    lib_available = False


logger = logging.getLogger(__name__)


class RedPandaPromptTemplate(PromptTemplate):
    output: Any = Field(default=None, exclude=True)


class RedPandaRule(Rule):
    output: Any = Field(default=None, exclude=True)
    prompt: Annotated[list[RedPandaPromptTemplate], BeforeValidator(ensure_list)] = Field(
        default_factory=list
    )

    # redefining to remove validator
    @model_validator(mode="after")
    def at_least_one_output_must_be_set(self) -> Self:
        return self


class RedPandaFlow(Flow):
    code: Any = Field(default=None, exclude=True)
    rules: Annotated[list[RedPandaRule], BeforeValidator(ensure_list)]
    file_metadata_key: str = "file"
    default_file: str = "<redpanda-message>"


active_config: RedPandaFlow | None = None


def _message_payload(msg: Any) -> bytes | str:
    payload = msg.payload
    return payload() if callable(payload) else payload


def _message_metadata_value(msg: Any, key: str, default: str) -> str:
    metadata = getattr(msg, "metadata", None)
    metadata = metadata() if callable(metadata) else metadata

    if metadata is None:
        return default

    if hasattr(metadata, "get"):
        value = metadata.get(key, default)
    else:
        value = getattr(metadata, key, default)

    return str(value) if value is not None else default


def init_processor(config: dict[str, Any]) -> None:
    global active_config

    try:
        options = config.get("options", config)
        active_config = RedPandaFlow.model_validate(options)
        logger.info("Parcoblatta Redpanda Connect processor config validated")
    except ValidationError as exc:
        logger.critical("Invalid Parcoblatta Redpanda Connect processor config: %s", exc)
        raise RuntimeError("Invalid Parcoblatta Redpanda Connect processor config") from exc


def process_message(msg: Any) -> list[Any]:
    if active_config is None:
        raise RuntimeError("Processor executed before initialization")

    source = _message_payload(msg)
    file = _message_metadata_value(
        msg,
        active_config.file_metadata_key,
        active_config.default_file,
    )

    output_messages = []
    logger.debug("Processing Redpanda Connect message with %d rule(s)", len(active_config.rules))
    for rule in active_config.rules:
        events = match_events_from_source(
            source,
            file=file,
            query_config=rule.query,
        )

        if rule.prompt:
            output_messages.extend(
                redpanda_connect.Message(
                    payload=render_prompt(event, prompt).model_dump_json().encode("utf-8")
                )
                for event in events
                for prompt in rule.prompt
            )
        else:
            output_messages.extend(
                redpanda_connect.Message(payload=event.model_dump_json().encode("utf-8"))
                for event in events
            )

    logger.debug("Emitted %d Redpanda Connect message(s)", len(output_messages))
    return output_messages


def process_batch(batch: list[Any]) -> list[list[Any]]:
    return [[message for input_message in batch for message in process_message(input_message)]]


class ParcoblattaProcessor:
    async def process(self, batch: list[Any]) -> list[list[Any]]:
        return process_batch(batch)

    async def close(self) -> None:
        pass


def parcoblatta_processor(config: Any) -> ParcoblattaProcessor:
    init_processor(config if isinstance(config, dict) else {"options": config})
    return ParcoblattaProcessor()


if __name__ == "__main__":
    if not lib_available:
        raise RuntimeError("redpanda_connect is required to run this processor")

    logging.basicConfig(level=logging.INFO)
    asyncio.run(redpanda_connect.processor_main(parcoblatta_processor))
