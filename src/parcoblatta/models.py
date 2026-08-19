from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

class CaptureEventRange(BaseModel):
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    start_column: int = Field(ge=0)
    end_column: int = Field(ge=0)
    start_byte: int = Field(ge=0)
    end_byte: int = Field(ge=0)

class CaptureEvent(BaseModel):
    file: Path
    language: str = "python"
    query: str
    capture: str
    range: CaptureEventRange
    text: str
    node_type: str | None = None
