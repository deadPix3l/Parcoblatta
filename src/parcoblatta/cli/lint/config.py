from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import BaseModel, BeforeValidator, Field

from parcoblatta import QUERIES_PATH
from parcoblatta.scanner.validators import ensure_list

DEFAULT_EXCLUDE = [
    ".git",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "site-packages",
    "venv",
]


class LintConfig(BaseModel):
    code: Annotated[list[Path], BeforeValidator(ensure_list)] = Field(
        default_factory=lambda: [Path(".")]
    )
    queries: Annotated[list[Path], BeforeValidator(ensure_list)] = Field(
        default_factory=lambda: [Path(QUERIES_PATH / "lint")]
    )
    select: Annotated[list[str], BeforeValidator(ensure_list)] = Field(default_factory=list)
    ignore: Annotated[list[str], BeforeValidator(ensure_list)] = Field(default_factory=list)
    exclude: Annotated[list[str], BeforeValidator(ensure_list)] = Field(
        default_factory=lambda: DEFAULT_EXCLUDE.copy()
    )
    format: Literal["human", "jsonl"] = "human"
    quiet: bool = False
    limit: int | None = None
    no_color: bool = False
    stats: bool = False
    fail: bool = True

    @classmethod
    def from_pyproject(cls, file: Path = Path("pyproject.toml")) -> Self:
        if not file.exists():
            return cls()

        data = tomllib.loads(file.read_text(encoding="utf-8"))
        lint_config = data.get("tool", {}).get("parcoblatta", {}).get("lint", {})
        config = cls(**lint_config)
        base = file.parent
        return config.model_copy(
            update={
                "code": [path if path.is_absolute() else base / path for path in config.code],
                "queries": [path if path.is_absolute() else base / path for path in config.queries],
            }
        )
