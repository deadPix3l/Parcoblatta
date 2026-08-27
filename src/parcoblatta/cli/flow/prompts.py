from __future__ import annotations

import json
from string import Template
from typing import TYPE_CHECKING

from parcoblatta.scanner.models import PromptEvent, PromptEventOpenAI

if TYPE_CHECKING:
    from parcoblatta.cli.flow.config import PromptTemplate
    from parcoblatta.scanner.models import MatchEvent


def render_prompt(
    match: MatchEvent,
    template_config: PromptTemplate,
) -> PromptEvent | PromptEventOpenAI:
    template_text = template_config.resolve_template()
    prompt = Template(template_text).substitute(prompt_context(match))
    if template_config.format == "openai":
        return PromptEventOpenAI(
            prompt=prompt,
            model=template_config.model,
            quickfix=match.quickfix,
        )
    return PromptEvent(
        prompt=prompt,
        quickfix=match.quickfix,
    )


def prompt_context(match: MatchEvent) -> dict[str, str]:
    return {
        "file": str(match.file),
        "language": match.language,
        "query": match.query,
        "match_index": str(match.match_index),
        "pattern_index": str(match.pattern_index),
        "full_text": match.full_text,
        "compact_text": match.compact_text,
        "quickfix": match.quickfix,
        "captures_json": json.dumps(
            [capture.model_dump(mode="json") for capture in match.captures],
            ensure_ascii=False,
        ),
        "event_json": match.model_dump_json(),
    }
