from pathlib import Path

import pytest

from parcoblatta.scanner.input.code import CodeInput
from parcoblatta.scanner.query.treesitter import TreesitterQuery
from parcoblatta.scanner.scanner import match_events, match_events_from_source


def test_match_events_from_source_scans_inline_text():
    events = list(
        match_events_from_source(
            "def example():\n    pass\n",
            file="stream/example.py",
            query_config=TreesitterQuery(text="(function_definition name: (identifier) @function.name)"),
        )
    )

    assert len(events) == 1
    assert events[0].file == Path("stream/example.py")
    assert events[0].captures[0].name == "function.name"
    assert events[0].captures[0].text == "example"
    assert events[0].quickfix == "stream/example.py:1:5:inline:0"


def test_match_events_from_source_scans_inline_bytes():
    events = list(
        match_events_from_source(
            b"class Example:\n    pass\n",
            file=Path("stream/example.py"),
            query_config=TreesitterQuery(text="(class_definition name: (identifier) @class.name)"),
        )
    )

    assert len(events) == 1
    assert events[0].captures[0].text == "Example"


def test_match_events_still_scans_code_input_files(tmp_path):
    code_file = tmp_path / "example.py"
    code_file.write_text("def example():\n    pass\n", encoding="utf-8")

    events = list(
        match_events(
            CodeInput(file=code_file),
            TreesitterQuery(text="(function_definition name: (identifier) @function.name)"),
        )
    )

    assert len(events) == 1
    assert events[0].file == code_file
    assert events[0].captures[0].text == "example"


def test_match_events_from_source_rejects_unsupported_language():
    with pytest.raises(ValueError, match="unsupported language: javascript"):
        list(
            match_events_from_source(
                "function example() {}",
                file="stream/example.js",
                query_config=TreesitterQuery(
                    text="(function_declaration) @function",
                    language="javascript",
                ),
            )
        )
