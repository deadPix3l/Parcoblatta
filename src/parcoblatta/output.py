from __future__ import annotations

from collections.abc import Iterable

from .flow import ParcoblattaOutput
from .models import CaptureEvent


def write_output(events: Iterable[CaptureEvent], output: ParcoblattaOutput) -> None:
    """Write capture events to configured outputs.

    :param events: Capture events to write.
    :param output: Output configuration.
    :return: None.
    """

    if output.topic:
        raise NotImplementedError("Kafka output is not implemented yet")

    file_handles = [path.open("a", encoding="utf-8") for path in output.file]
    try:
        for event in events:
            line = event.model_dump_json() + "\n"
            for file_handle in file_handles:
                file_handle.write(line)
    finally:
        for file_handle in file_handles:
            file_handle.close()
