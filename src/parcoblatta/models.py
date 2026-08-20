from __future__ import annotations

from pathlib import Path  # noqa: TC003 - Pydantic needs Path at runtime to build this model.
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, Field, computed_field

if TYPE_CHECKING:
    from tree_sitter import Node


class CaptureEventRange(BaseModel):
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    start_column: int = Field(ge=0)
    end_column: int = Field(ge=0)
    start_byte: int = Field(ge=0)
    end_byte: int = Field(ge=0)

    @classmethod
    def from_node(cls, node: Node) -> Self:
        return cls(
            start_line=node.start_point.row + 1,
            end_line=node.end_point.row + 1,
            start_column=node.start_point.column,
            end_column=node.end_point.column,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
        )


class Capture(BaseModel):
    name: str
    range: CaptureEventRange
    text: str
    node_type: str | None = None

    @classmethod
    def from_node(cls, name: str, node: Node, source: bytes) -> Self:
        return cls(
            name=name,
            range=CaptureEventRange.from_node(node),
            text=source[node.start_byte : node.end_byte].decode("utf-8", errors="replace"),
            node_type=node.type,
        )


class MatchEvent(BaseModel):
    file: Path
    language: str = "python"
    query: str
    match_index: int = Field(ge=0)
    pattern_index: int = Field(ge=0)
    full_text: str
    compact_text: str
    captures: list[Capture] = Field(min_length=1)

    @computed_field
    @property
    def quickfix(self) -> str:
        first_capture = min(
            self.captures,
            key=lambda capture: capture.range.start_byte,
        )
        capture_names = ", ".join(capture.name for capture in self.captures)
        return (
            f"{self.file}:{first_capture.range.start_line}:"
            f"{first_capture.range.start_column + 1}: {self.query} ({capture_names})"
        )


class PromptEvent(BaseModel):
    match: MatchEvent
    prompt: str
    template: str
