from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class CaptureEvent(BaseModel):
    """Public event schema emitted to JSONL/Kafka."""

    file: Path
    language: str = "python"
    query: str
    capture: str

    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    start_column: int = Field(ge=0)
    end_column: int = Field(ge=0)
    start_byte: int = Field(ge=0)
    end_byte: int = Field(ge=0)

    text: str
    node_type: str | None = None
