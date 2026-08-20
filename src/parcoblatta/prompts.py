from __future__ import annotations

import json
from string import Template
from typing import TYPE_CHECKING

from .models import PromptEvent

if TYPE_CHECKING:
    from .flow import PromptTemplate
    from .models import MatchEvent


def render_prompt(match: MatchEvent, template_config: PromptTemplate) -> PromptEvent:
    template_text = template_config.resolve_template()
    prompt = Template(template_text).safe_substitute(prompt_context(match))
    return PromptEvent(
        match=match,
        prompt=prompt,
        template=str(template_config.file) if template_config.file else "inline",
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
