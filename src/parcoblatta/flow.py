from typing import Annotated, Self, TypeVar
from pathlib import Path
import yaml

from pydantic import BaseModel, BeforeValidator, model_validator, Field

T = TypeVar("T")

def ensure_list(value: T | list[T] | tuple[T] | set[T] ) -> list[T]:
  """ wrap or convert value to a list. """
  if not isinstance(value, (list, tuple, set)):
      return [value]
  return list(value)

class CodeInput(BaseModel):
    file: Annotated[ list[Path], BeforeValidator(ensure_list)]

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

class ParcoblattaOutput(BaseModel):
  topic: Annotated[ list[str], BeforeValidator(ensure_list)] = Field(default_factory=list)
  file: Annotated[ list[Path], BeforeValidator(ensure_list)] = Field(default_factory=list)

  @model_validator(mode="after")
  def at_least_one_must_be_set(self) -> Self:
    if not any([self.topic, self.file]):
      raise ValueError("must set at least one topic or file")
    return self

class ParcoblattaFlow(BaseModel):
  code: CodeInput
  query: TreesitterQuery
  output: ParcoblattaOutput

  @classmethod
  def from_yaml(cls, file: Path | str) -> Self:
      return cls(**yaml.safe_load(Path(file).read_text()))


# for debugging
if __name__ == "__main__":
    from sys import argv
    from rich import print #noqa: A004

    x = ParcoblattaFlow.from_yaml(argv[1])
    print(x)

