from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path  # noqa: TC003 - Pydantic/from_yaml need Path at runtime.
from typing import TYPE_CHECKING, Annotated, Self

import yaml

from pydantic import BaseModel, BeforeValidator, Field, model_validator

if TYPE_CHECKING:
    from collections.abc import Generator

from .validators import ensure_list


@dataclass(frozen=True)
class QuerySpec:
  name: str
  source: str
  language: str = "python"


class CodeInput(BaseModel):
    file: Annotated[ list[Path], BeforeValidator(ensure_list)]

    def resolve_files(self) -> Generator[Path, None, None]:
        for path in self.file:
            if path.is_dir():
                yield from sorted(path.rglob("*.py"))
            else:
                yield path

class TreesitterQuery(BaseModel):
  file: Annotated[ list[Path], BeforeValidator(ensure_list)] = Field(default_factory=list)
  text: Annotated[ list[str], BeforeValidator(ensure_list)] = Field(default_factory=list)
  language: str = "python"
  recursive: bool = False

  @model_validator(mode="after")
  def at_least_one_must_be_set(self) -> Self:
    if not any([self.file, self.text]):
        raise ValueError("must set at least one of: ['text', 'file']")
    return self

  def resolve_queries(self) -> Generator[QuerySpec, None, None]:
    for index, text in enumerate(self.text):
        yield QuerySpec(name=f"inline:{index}", source=text, language=self.language)

    for path in self.file:
        if path.is_dir():
            query_files = sorted(path.rglob("*.scm") if self.recursive else path.glob("*.scm"))
        else:
            query_files = [path]

        for query_file in query_files:
            yield QuerySpec(
                name=query_file.stem,
                source=query_file.read_text(encoding="utf-8"),
                language=self.language,
            )

class ParcoblattaOutput(BaseModel):
  topic: Annotated[ list[str], BeforeValidator(ensure_list)] = Field(default_factory=list)
  file: Annotated[ list[Path], BeforeValidator(ensure_list)] = Field(default_factory=list)

  @model_validator(mode="after")
  def at_least_one_must_be_set(self) -> Self:
    if not any([self.topic, self.file]):
      raise ValueError("must set at least one topic or file")
    return self


class ParcoblattaRule(BaseModel):
  query: TreesitterQuery
  output: ParcoblattaOutput


class ParcoblattaFlow(BaseModel):
  code: CodeInput
  rules: Annotated[list[ParcoblattaRule], BeforeValidator(ensure_list)]

  @classmethod
  def from_yaml(cls, file: Path | str) -> Self:
      return cls(**yaml.safe_load(Path(file).read_text()))


# for debugging
if __name__ == "__main__":
    from sys import argv

    from rich import print  # noqa: A004

    x = ParcoblattaFlow.from_yaml(argv[1])
    print(x)

