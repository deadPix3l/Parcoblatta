from __future__ import annotations

from pathlib import Path
from typing import Annotated, Self

from pydantic import BaseModel, BeforeValidator, Field, model_validator

from parcoblatta.cli.flow.output.kafka import KafkaConfig
from parcoblatta.scanner.validators import ensure_list


class Output(BaseModel):
    topic: Annotated[list[str], BeforeValidator(ensure_list)] = Field(default_factory=list)
    file: Annotated[list[Path], BeforeValidator(ensure_list)] = Field(default_factory=list)
    stdout: bool = False
    kafka: KafkaConfig = Field(default_factory=KafkaConfig)

    @model_validator(mode="after")
    def at_least_one_must_be_set(self) -> Self:
        if not any([self.topic, self.file, self.stdout]):
            raise ValueError("must set at least one topic, file, or stdout")
        return self
