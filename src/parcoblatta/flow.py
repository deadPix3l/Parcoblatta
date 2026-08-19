from typing import Annotated, Any, Self
from pathlib import Path
import yaml

from pydantic import BaseModel, BeforeValidator, ValidationError, model_validator, Field

def ensure_list(value: Any) -> Any:  
  """ wrap or convert value to a list. """
  if not isinstance(value, (list, tuple, set)):
      return [value]
  else:
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
    from rich import print

    x = ParcoblattaFlow.from_yaml(argv[1])
    print(x)

