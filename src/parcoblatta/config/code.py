from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, BeforeValidator

from parcoblatta.validators import ensure_list

if TYPE_CHECKING:
    from collections.abc import Generator


class CodeInput(BaseModel):
    file: Annotated[list[Path], BeforeValidator(ensure_list)]

    def resolve_files(self) -> Generator[Path, None, None]:
        for path in self.file:
            if path.is_dir():
                yield from sorted(path.rglob("*.py"))
            else:
                yield path
