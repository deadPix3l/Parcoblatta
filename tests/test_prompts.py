import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from parcoblatta.cli.flow.config import Output, PromptTemplate
from parcoblatta.cli.flow.prompts import render_prompt
from parcoblatta.scanner.models import (
    Capture,
    CaptureEventRange,
    MatchEvent,
    OpenAIJsonSchema,
    OpenAIObjectSchema,
    PromptEventOpenAI,
    ResponseSchema,
)


def _match_event() -> MatchEvent:
    return MatchEvent(
        file=Path("src/example.py"),
        language="python",
        query="functions",
        match_index=0,
        pattern_index=0,
        full_text="def example():\n    pass\n",
        compact_text="def example(): ...",
        captures=[
            Capture(
                name="function.name",
                range=CaptureEventRange(
                    start_line=1,
                    end_line=1,
                    start_column=4,
                    end_column=11,
                    start_byte=4,
                    end_byte=11,
                ),
                text="example",
                node_type="identifier",
            )
        ],
    )


def test_render_prompt_defaults_to_simple_prompt_format():
    event = render_prompt(
        _match_event(),
        PromptTemplate(text="Review $compact_text", output=Output(stdout=True)),
    )

    assert event.format == "prompt"
    assert event.prompt == "Review def example(): ..."
    assert event.quickfix == "src/example.py:1:5:functions"


def test_render_prompt_supports_openai_format():
    event = render_prompt(
        _match_event(),
        PromptTemplate(
            text="Review $compact_text",
            format="openai",
            model="gpt-4.1-mini",
            output=Output(stdout=True),
        ),
    )

    assert isinstance(event, PromptEventOpenAI)
    assert event.format == "openai"
    assert event.model == "gpt-4.1-mini"
    assert event.messages[0].role == "user"
    assert event.messages[0].content == "Review def example(): ..."
    assert event.quickfix == "src/example.py:1:5:functions"


def test_render_prompt_includes_openai_response_format_schema():
    event = render_prompt(
        _match_event(),
        PromptTemplate(
            text="Review $compact_text",
            format="openai",
            model="gpt-4.1-mini",
            output=Output(stdout=True),
            schema=ResponseSchema.model_validate(
                {
                    "reason": {"type": "string"},
                    "keep": {"type": "boolean"},
                },
            ),
        ),
    )

    payload = event.model_dump(mode="json")

    assert "schema" not in payload
    assert payload["response_format"] == {
        "type": "json_schema",
        "json_schema": {
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                    "keep": {"type": "boolean"},
                },
                "additionalProperties": False,
                "required": ["reason", "keep"],
            },
            "name": "parcoblatta_4ac739f0b060b61d",
        },
    }


def test_openai_schema_required_is_always_derived_from_properties():
    schema = OpenAIObjectSchema(
        properties={
            "reason": {"type": "string"},
            "keep": {"type": "boolean"},
        },
    )

    assert schema.model_dump(mode="json", by_alias=True)["required"] == ["reason", "keep"]

    with pytest.raises(ValidationError):
        OpenAIObjectSchema(
            properties={"reason": {"type": "string"}, "keep": {"type": "boolean"}},
            required=["reason"],
        )


def test_response_schema_rejects_per_property_required_flag():
    with pytest.raises(ValidationError):
        ResponseSchema.model_validate(
            {
                "reason": {"type": "string"},
                "keep": {"type": "boolean", "required": False},
            },
        )


def test_openai_schema_name_is_derived_from_schema_and_not_configurable():
    event = render_prompt(
        _match_event(),
        PromptTemplate(
            text="Review $compact_text",
            format="openai",
            output=Output(stdout=True),
            schema=ResponseSchema.model_validate({"reason": {"type": "string"}}),
        ),
    )
    response_format = event.response_format
    assert response_format is not None
    schema_json = response_format.json_schema.schema_.model_dump_json(by_alias=True)

    assert response_format.json_schema.name == (
        f"parcoblatta_{hashlib.sha256(schema_json.encode()).hexdigest()[:16]}"
    )

    with pytest.raises(ValidationError):
        OpenAIJsonSchema(
            name="custom",
            strict=True,
            schema=OpenAIObjectSchema(properties={}),
        )
