from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Self

from pydantic import BaseModel, BeforeValidator, Field, model_validator

from parcoblatta.models.validators import ensure_list

if TYPE_CHECKING:
    from collections.abc import Generator


@dataclass(frozen=True)
class QuerySpec:
    name: str
    source: str
    language: str = "python"


class TreesitterQuery(BaseModel):
    name: str | None = None
    file: Annotated[list[Path], BeforeValidator(ensure_list)] = Field(default_factory=list)
    text: Annotated[list[str], BeforeValidator(ensure_list)] = Field(default_factory=list)
    language: str = "python"
    recursive: bool = False

    @model_validator(mode="after")
    def at_least_one_must_be_set(self) -> Self:
        if not any([self.file, self.text]):
            raise ValueError("must set at least one of: ['text', 'file']")
        return self

    def resolve_queries(self) -> Generator[QuerySpec, None, None]:
        for index, text in enumerate(self.text):
            yield QuerySpec(
                name=(self.name or f"inline:{index}"),
                source=text,
                language=self.language,
            )

        for path in self.file:
            if path.is_dir():
                query_files = sorted(path.rglob("*.scm") if self.recursive else path.glob("*.scm"))
            else:
                query_files = [path]

            for query_file in query_files:
                yield QuerySpec(
                    name=(self.name or query_file.stem),
                    source=query_file.read_text(encoding="utf-8"),
                    language=self.language,
                )
