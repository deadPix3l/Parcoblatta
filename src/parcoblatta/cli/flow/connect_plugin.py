from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ValidationError

from parcoblatta.scanner.query.treesitter import TreesitterQuery
from parcoblatta.scanner.scanner import match_events_from_source

try:
    import redpanda_connect
    lib_available = True
except ImportError:  # pragma: no cover - exercised in environments without the SDK
    class RedPandaUnavailable:
        """ If redpanda is not available """
        @staticmethod
        def Message(*args, **kwargs):
            raise RuntimeError("redpanda_connect is required to create processor messages")

        @staticmethod
        def processor(f: Callable) -> Callable:
            return f

        @staticmethod
        def processor_init(f: Callable) -> Callable:
            return f

    redpanda_connect = RedPandaUnavailable
    lib_available = False


logger = logging.getLogger(__name__)


class RedpandaConnectProcessorConfig(BaseModel):
    query: TreesitterQuery
    file_metadata_key: str = "file"
    default_file: str = "<redpanda-message>"


active_config: RedpandaConnectProcessorConfig | None = None


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


@redpanda_connect.processor_init
def init_processor(config: dict[str, Any]) -> None:
    global active_config

    try:
        active_config = RedpandaConnectProcessorConfig.model_validate(config.get("options", {}))
        logger.info("Parcoblatta Redpanda Connect processor config validated")
    except ValidationError as exc:
        logger.critical("Invalid Parcoblatta Redpanda Connect processor config: %s", exc)
        raise RuntimeError("Invalid Parcoblatta Redpanda Connect processor config") from exc


@redpanda_connect.processor
def process_message(msg) -> list:
    if active_config is None:
        raise RuntimeError("Processor executed before initialization")

    source = _message_payload(msg)
    file = _message_metadata_value(
        msg,
        active_config.file_metadata_key,
        active_config.default_file,
    )

    return [
        redpanda_connect.Message(payload=event.model_dump_json().encode("utf-8"))
        for event in match_events_from_source(
            source,
            file=file,
            query_config=active_config.query,
        )
    ]


if __name__ == "__main__":
    if not lib_available:
        raise RuntimeError("redpanda_connect is required to run this processor")

    logging.basicConfig(level=logging.INFO)
    asyncio.run(redpanda_connect.processor_main(process_message, init=init_processor))
