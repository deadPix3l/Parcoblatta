from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, BeforeValidator, Field

from parcoblatta.scanner.validators import ensure_list

if TYPE_CHECKING:
    from collections.abc import Generator


class CodeInput(BaseModel):
    file: Annotated[list[Path], BeforeValidator(ensure_list)]
    exclude: Annotated[list[str], BeforeValidator(ensure_list)] = Field(default_factory=list)

    def resolve_files(self) -> Generator[Path, None, None]:
        for path in self.file:
            if path.is_dir():
                yield from (
                    file
                    for file in sorted(path.rglob("*.py"))
                    if not self.is_excluded(file, base=path)
                )
            elif not self.is_excluded(path):
                yield path

    def is_excluded(self, path: Path, base: Path | None = None) -> bool:
        candidates = path.relative_to(base).parts if base is not None else path.parts
        return any(
            fnmatch(part, pattern) or fnmatch(str(path), pattern)
            for pattern in self.exclude
            for part in candidates
        )
