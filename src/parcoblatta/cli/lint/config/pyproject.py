from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal, Self

from pydantic import BeforeValidator, Field, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)

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


class LintPyprojectSource(PyprojectTomlConfigSettingsSource):
    def __call__(self) -> dict[str, Any]:
        data = super().__call__()
        base = self.toml_file_path.parent
        for key in ("code_dir", "query_dir"):
            if key in data:
                data[key] = [
                    path if (path := Path(value)).is_absolute() else base / path
                    for value in ensure_list(data[key])
                ]
        return data


class LintConfig(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        pyproject_toml_depth=5,
        pyproject_toml_table_header=("tool", "parcoblatta", "lint"),
    )

    code_dir: Annotated[list[Path], BeforeValidator(ensure_list)] = Field(
        default_factory=lambda: [Path(".")]
    )
    query_dir: Annotated[list[Path], BeforeValidator(ensure_list)] = Field(default_factory=list)
    default_rules: bool = True
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

    @model_validator(mode="after")
    def add_default_rules(self) -> Self:
        default_query_dir = Path(QUERIES_PATH / "lint")
        if self.default_rules and default_query_dir not in self.query_dir:
            self.query_dir.append(default_query_dir)
        return self

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (init_settings, LintPyprojectSource(settings_cls))


def load_lint_config(file: Path | None = None) -> LintConfig:
    if file is None:
        return LintConfig()
    if not file.exists():
        return LintConfig(_build_sources=((), {}))
    return LintConfig(_build_sources=((LintPyprojectSource(LintConfig, file),), {}))
