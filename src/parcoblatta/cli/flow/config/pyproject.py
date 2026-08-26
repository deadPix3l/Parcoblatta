from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import BeforeValidator, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)

from parcoblatta.cli.flow.output.kafka import KafkaConfig
from parcoblatta.scanner.validators import ensure_list

from .flow import Flow


def _resolve_path(value: str | Path, base: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else base / path


def _resolve_path_list(data: dict[str, Any], key: str, base: Path) -> None:
    if key in data:
        data[key] = [_resolve_path(value, base) for value in ensure_list(data[key])]


class FlowSettingsPyprojectSource(PyprojectTomlConfigSettingsSource):
    def __call__(self) -> dict[str, Any]:
        data = super().__call__()
        base = self.toml_file_path.parent
        for key in ("config_dir", "code_dir", "query_dir", "template_dir"):
            if key in data:
                data[key] = [
                    path if (path := Path(value)).is_absolute() else base / path
                    for value in ensure_list(data[key])
                ]
        if "output_dir" in data:
            data["output_dir"] = _resolve_path(data["output_dir"], base)
        return data


class FlowKafkaConfig(KafkaConfig):
    topic_prefix: str | None = None


class FlowConfig(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        pyproject_toml_depth=5,
        pyproject_toml_table_header=("tool", "parcoblatta", "flow"),
    )

    config_dir: Annotated[list[Path], BeforeValidator(ensure_list)] = Field(
        default_factory=lambda: [Path("flows")]
    )
    default: Path | None = None
    code_dir: Annotated[list[Path], BeforeValidator(ensure_list)] = Field(default_factory=list)
    query_dir: Annotated[list[Path], BeforeValidator(ensure_list)] = Field(default_factory=list)
    template_dir: Annotated[list[Path], BeforeValidator(ensure_list)] = Field(default_factory=list)
    output_dir: Path | None = None
    exclude: Annotated[list[str], BeforeValidator(ensure_list)] = Field(default_factory=list)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    kafka: FlowKafkaConfig = Field(default_factory=FlowKafkaConfig)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (init_settings, FlowSettingsPyprojectSource(settings_cls))

    def default_config_file(self) -> Path | None:
        if self.default is None:
            return None
        if self.default.is_absolute():
            return self.default
        candidates = [config_dir / self.default for config_dir in self.config_dir]
        return next((candidate for candidate in candidates if candidate.exists()), candidates[0])


def _resolve_first_existing(value: str | Path, base: Path, search_dirs: list[Path]) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path

    base_candidate = base / path
    if base_candidate.exists():
        return base_candidate

    return next(
        (candidate for directory in search_dirs if (candidate := directory / path).exists()),
        base_candidate,
    )


def _apply_topic_prefix(topic: str, prefix: str | None) -> str:
    if not prefix or topic.startswith(f"{prefix}."):
        return topic
    return f"{prefix}.{topic}"


def _apply_kafka_defaults(data: dict[str, Any], settings: FlowConfig) -> None:
    if not data.get("topic"):
        return
    data["topic"] = [
        _apply_topic_prefix(topic, settings.kafka.topic_prefix) for topic in ensure_list(data["topic"])
    ]
    kafka_defaults = settings.kafka.model_dump(exclude={"topic_prefix"})
    data["kafka"] = kafka_defaults | data.get("kafka", {})


def _resolve_flow_data(data: dict[str, Any], base: Path, settings: FlowConfig) -> dict[str, Any]:
    if code := data.get("code"):
        if "file" in code:
            code["file"] = [_resolve_path(value, base) for value in ensure_list(code["file"])]
        if settings.exclude and "exclude" not in code:
            code["exclude"] = settings.exclude

    for rule in ensure_list(data.get("rules", [])):
        if query := rule.get("query"):
            if "file" in query:
                query["file"] = [
                    _resolve_first_existing(value, base, settings.query_dir)
                    for value in ensure_list(query["file"])
                ]
        if output := rule.get("output"):
            _apply_kafka_defaults(output, settings)
            _resolve_path_list(output, "file", settings.output_dir or base)
        for prompt in ensure_list(rule.get("prompt", [])):
            if "file" in prompt:
                prompt["file"] = _resolve_first_existing(prompt["file"], base, settings.template_dir)
            if prompt_output := prompt.get("output"):
                _apply_kafka_defaults(prompt_output, settings)
                _resolve_path_list(prompt_output, "file", settings.output_dir or base)
    return data


def _flow_from_yaml_with_settings(file: Path | str, settings: FlowConfig, base: Path) -> Flow:
    data = yaml.safe_load(Path(file).read_text())
    return Flow(**_resolve_flow_data(data, base, settings))


def _load_flow_settings_with_base(file: Path | None = None) -> tuple[FlowConfig, Path]:
    source = FlowSettingsPyprojectSource(FlowConfig, file)
    base = source.toml_file_path.parent
    if not source.toml_file_path.exists():
        return FlowConfig(_build_sources=((), {})), base
    return FlowConfig(_build_sources=((source,), {})), base


def load_flow_settings(file: Path | None = None) -> FlowConfig:
    settings, _base = _load_flow_settings_with_base(file)
    return settings


def load_flow_config(file: Path | None = None) -> Flow:
    settings, base = _load_flow_settings_with_base()
    if file is not None and file.suffix in {".yaml", ".yml"}:
        return _flow_from_yaml_with_settings(file, settings, base)

    settings, base = _load_flow_settings_with_base(file)
    default_file = settings.default_config_file()
    if default_file is None:
        raise ValueError("must provide a flow config path or set [tool.parcoblatta.flow].default")
    return _flow_from_yaml_with_settings(default_file, settings, base)
