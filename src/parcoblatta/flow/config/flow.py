from __future__ import annotations

from pathlib import Path
from typing import Annotated, Self

import yaml
from pydantic import BaseModel, BeforeValidator, Field, model_validator

from parcoblatta.validators import ensure_list

from .code import CodeInput
from .output import ParcoblattaOutput
from .prompt import PromptTemplate
from .query import TreesitterQuery


class ParcoblattaRule(BaseModel):
    query: TreesitterQuery
    output: ParcoblattaOutput | None = None
    prompt: Annotated[list[PromptTemplate], BeforeValidator(ensure_list)] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def at_least_one_output_must_be_set(self) -> Self:
        if not any([self.output, self.prompt]):
            raise ValueError("must set output and/or prompt")
        return self


class ParcoblattaFlow(BaseModel):
    code: CodeInput
    rules: Annotated[list[ParcoblattaRule], BeforeValidator(ensure_list)]

    @classmethod
    def from_yaml(cls, file: Path | str) -> Self:
        return cls(**yaml.safe_load(Path(file).read_text()))
