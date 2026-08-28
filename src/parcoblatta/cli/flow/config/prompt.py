from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel, model_validator, Field

from .output import Output

from parcoblatta.scanner.models import ResponseSchema


class PromptTemplate(BaseModel):
    text: str | None = None
    file: Path | None = None
    output: Output
    format: Literal["prompt", "openai"] = "prompt"
    model: str | None = None
    schema_: ResponseSchema | None = Field(default=None, exclude_if=lambda v: v is None, alias="schema")

    @model_validator(mode="after")
    def exactly_one_must_be_set(self) -> Self:
        if bool(self.text) == bool(self.file):
            raise ValueError("must set exactly one of: ['text', 'file']")
        return self

    def resolve_template(self) -> str:
        if self.text is not None:
            return self.text
        return self.file.read_text(encoding="utf-8")
