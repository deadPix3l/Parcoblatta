import json
from types import SimpleNamespace

import pytest

from parcoblatta.cli.flow.redpanda import plugin as connect_plugin


class FakeMessage:
    def __init__(self, payload: bytes | str, metadata=None):
        self.payload = payload
        self.metadata = metadata or {}


def setup_function():
    connect_plugin.active_config = None


def test_redpanda_rule_accepts_query_without_code_input_or_output():
    config = connect_plugin.RedPandaRule.model_validate(
        {
            "query": {"text": "(function_definition) @function"},
        }
    )

    assert config.query.language == "python"
    assert config.output is None


def test_redpanda_flow_accepts_multiple_rules():
    config = connect_plugin.RedPandaFlow.model_validate(
        {
            "rules": [
                {"query": {"text": "(function_definition) @function"}},
                {"query": {"text": "(class_definition) @class"}},
            ],
            "file_metadata_key": "path",
        }
    )

    assert len(config.rules) == 2
    assert config.file_metadata_key == "path"


def test_redpanda_flow_accepts_and_ignores_code_config():
    config = connect_plugin.RedPandaFlow.model_validate(
        {
            "code": {"file": "src"},
            "rules": [{"query": {"text": "(function_definition) @function"}}],
        }
    )

    assert config.code == {"file": "src"}
    assert "code" not in config.model_dump()


def test_redpanda_rule_accepts_and_ignores_output_config():
    config = connect_plugin.RedPandaRule.model_validate(
        {
            "query": {"text": "(function_definition) @function"},
            "output": {"stdout": True},
        }
    )

    assert config.output == {"stdout": True}
    assert "output" not in config.model_dump()


def test_redpanda_rule_accepts_prompt_without_output_config():
    config = connect_plugin.RedPandaRule.model_validate(
        {
            "query": {"text": "(function_definition) @function"},
            "prompt": {"text": "Review $quickfix"},
        }
    )

    assert len(config.prompt) == 1
    assert config.prompt[0].output is None
    assert config.prompt[0].text == "Review $quickfix"


def test_init_processor_validates_options():
    connect_plugin.init_processor(
        {
            "options": {
                "rules": [{"query": {"text": "(function_definition) @function"}}],
            }
        }
    )

    assert connect_plugin.active_config is not None
    assert connect_plugin.active_config.default_file == "<redpanda-message>"


def test_init_processor_rejects_invalid_options():
    with pytest.raises(RuntimeError, match="Invalid Parcoblatta Redpanda Connect processor config"):
        connect_plugin.init_processor({"options": {}})


def test_process_message_scans_payload_and_uses_metadata_file(monkeypatch):
    monkeypatch.setattr(connect_plugin, "redpanda_connect", SimpleNamespace(Message=FakeMessage))
    connect_plugin.init_processor(
        {
            "options": {
                "rules": [
                    {
                        "query": {
                            "text": "(function_definition name: (identifier) @function.name)",
                        },
                    }
                ],
                "file_metadata_key": "path",
                "default_file": "fallback.py",
            }
        }
    )

    messages = connect_plugin.process_message(
        FakeMessage(b"def example():\n    pass\n", metadata={"path": "stream/example.py"})
    )

    assert len(messages) == 1
    payload = json.loads(messages[0].payload.decode("utf-8"))
    assert payload["file"] == "stream/example.py"
    assert payload["captures"][0]["name"] == "function.name"
    assert payload["captures"][0]["text"] == "example"


def test_process_message_uses_default_file_when_metadata_is_absent(monkeypatch):
    monkeypatch.setattr(connect_plugin, "redpanda_connect", SimpleNamespace(Message=FakeMessage))
    connect_plugin.init_processor(
        {
            "options": {
                "rules": [
                    {"query": {"text": "(class_definition name: (identifier) @class.name)"}}
                ],
                "default_file": "fallback.py",
            }
        }
    )

    messages = connect_plugin.process_message(FakeMessage("class Example:\n    pass\n"))

    payload = json.loads(messages[0].payload.decode("utf-8"))
    assert payload["file"] == "fallback.py"
    assert payload["captures"][0]["text"] == "Example"


def test_process_message_emits_prompt_events_when_prompt_is_configured(monkeypatch):
    monkeypatch.setattr(connect_plugin, "redpanda_connect", SimpleNamespace(Message=FakeMessage))
    connect_plugin.init_processor(
        {
            "options": {
                "rules": [
                    {
                        "query": {
                            "text": "(function_definition name: (identifier) @function.name)",
                        },
                        "prompt": {
                            "text": "Review $quickfix: $compact_text",
                        },
                    }
                ],
                "default_file": "stream/example.py",
            }
        }
    )

    messages = connect_plugin.process_message(FakeMessage("def example():\n    pass\n"))

    assert len(messages) == 1
    payload = json.loads(messages[0].payload.decode("utf-8"))
    assert payload == {
        "quickfix": "stream/example.py:1:5:inline:0",
        "prompt": "Review stream/example.py:1:5:inline:0: def example():",
    }


def test_process_message_runs_multiple_rules(monkeypatch):
    monkeypatch.setattr(connect_plugin, "redpanda_connect", SimpleNamespace(Message=FakeMessage))
    connect_plugin.init_processor(
        {
            "options": {
                "rules": [
                    {
                        "query": {
                            "name": "functions",
                            "text": "(function_definition name: (identifier) @function.name)",
                        },
                    },
                    {
                        "query": {
                            "name": "classes",
                            "text": "(class_definition name: (identifier) @class.name)",
                        },
                    },
                ],
                "default_file": "stream/example.py",
            }
        }
    )

    messages = connect_plugin.process_message(
        FakeMessage("class Example:\n    pass\n\ndef example():\n    pass\n")
    )

    payloads = [json.loads(message.payload.decode("utf-8")) for message in messages]
    assert [payload["name"] for payload in payloads] == ["functions", "classes"]
    assert [payload["captures"][0]["text"] for payload in payloads] == ["example", "Example"]
