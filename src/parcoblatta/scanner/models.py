from __future__ import annotations

from enum import StrEnum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    computed_field,
    model_serializer,
    model_validator,
)

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
    name: str | None = None
    file: Path
    language: str = "python"
    query: str
    match_index: int = Field(ge=0)
    pattern_index: int = Field(ge=0)
    full_text: str
    compact_text: str
    captures: list[Capture] = Field(min_length=1)
    settings: dict[str, str] = Field(default_factory=dict)

    def captures_named(self, name: str) -> list[Capture]:
        return [capture for capture in self.captures if capture.name == name]

    def first_capture(self, name: str | None = None) -> Capture | None:
        captures = self.captures_named(name) if name is not None else self.captures
        if not captures:
            return None
        return min(captures, key=lambda capture: capture.range.start_byte)

    def setting(self, name: str, default: str) -> str:
        return self.settings.get(name, default)

    @computed_field
    @property
    def quickfix(self) -> str:
        first_capture = self.first_capture("quickfix") or self.first_capture("target") or self.first_capture()
        if first_capture is None:
            return f"{self.file}:::{self.name or self.query}"
        return (
            f"{self.file}:{first_capture.range.start_line}:"
            f"{first_capture.range.start_column + 1}:"
            f"{self.name or self.query}"
        )


class PromptEvent(BaseModel):
    quickfix: str | None = None
    format: Literal["prompt", "openai"] = Field(default="prompt", exclude=True)
    model: str | None = Field(default=None, exclude_if=lambda v: v is None)
    prompt: str
    schema_: ResponseSchema | None = Field(default=None, exclude_if=lambda v: v is None, alias="schema")

    @model_validator(mode="before")
    @classmethod
    def handle_prompt_section(cls, data: Any) -> Any:
        if isinstance(data, dict) and isinstance(data.get("prompt"), dict):
            data = {**data, **data["prompt"]}
            if "text" in data:
                data["prompt"] = data.pop("text")
        return data


class OpenAIMessage(BaseModel):
    role: str = "user"
    content: str


class SupportedSchemaType(StrEnum):
    """ see: developers.openai.com/api/docs/guides/structured-outputs#supported-schemas """
    string = auto()
    number = auto()
    boolean = auto()
    int = auto()
    object = auto()
    array = auto()
    enum = auto()
    anyof = auto()


class ResponseSchemaItem(BaseModel):
    model_config = ConfigDict(extra='allow')

    type: SupportedSchemaType
    description: str | None = Field(default=None, exclude_if=lambda v: v is None)

class ResponseSchema(RootModel[dict[str, ResponseSchemaItem]]):

    @model_serializer(mode="wrap")
    def serialize_with_static_fields(self, handler) -> dict[str, Any]:
        # normal serialization
        data = handler(self)
        # openai requires specific values and structure
        return {
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": data,
                        "additionalProperties": False,
                        "required": list(data.keys())
                    }
                }
            }
        }


class PromptEventOpenAI(BaseModel):
    quickfix: str | None = None
    format: Literal["openai"] = Field(default="openai", exclude=True)
    model: str | None = Field(default=None, exclude_if=lambda v: v is None)
    messages: list[OpenAIMessage]
    schema_: ResponseSchema | None = Field(default=None, exclude_if=lambda v: v is None, alias="schema")

    #@model_serializer(mode="wrap")
    #def serialize_with_response_format(self, handler) -> dict[str, Any]:
        #data = handler(self)
        #if self.schema_ is not None:
            #data.update(self.schema_.model_dump())
        #return data

    @model_validator(mode="before")
    @classmethod
    def handle_shortcut_prompt(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if isinstance(data.get("prompt"), dict):
                data = {**data, **data["prompt"]}
                data.pop("prompt", None)
                if "text" in data:
                    data["prompt"] = data.pop("text")
            if isinstance(data.get("prompt"), str):
                data["messages"] = data.pop("messages", []) + [{"role": "user", "content": data.pop("prompt")}]
        return data
