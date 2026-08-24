from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from jinja2 import Template

from parcoblatta.cli.lint.colors import ANSIColor, NoColor
from parcoblatta.scanner.models import MatchEvent

from parcoblatta import TEMPLATES_PATH

VIOLATION_TEMPLATE = Template(Path(TEMPLATES_PATH / "violation.jinja").read_text(encoding="utf-8"))


@dataclass(frozen=True)
class Violation:
    rule: str
    message: str
    file: Path
    line: int
    column: int
    text: str
    quickfix: str
    why: str | None = None
    help: str | None = None
    color: bool = True

    @classmethod
    def from_event(cls, event: MatchEvent, color: bool = True) -> Self:
        target = event.first_capture("target") or event.first_capture()

        return cls(
            rule=event.setting("name", event.query),
            message=event.setting(
                "message",
                event.setting("lint_message", "Untagged Lint Rule"),
            ),
            file=event.file,
            line=target.range.start_line,
            column=target.range.start_column + 1,
            text=event.compact_text,
            quickfix=event.quickfix,
            why=event.settings.get("why"),
            help=event.settings.get("help"),
            color=color,
        )

    def __str__(self) -> str:
        return self.render(color=self.color)

    def to_jsonl(self) -> str:
        """Convert violation to JSONL format (single line JSON)."""
        return json.dumps(
            {
                "rule": self.rule,
                "message": self.message,
                "file": str(self.file),
                "line": self.line,
                "column": self.column,
                "quickfix": self.quickfix,
                "why": self.why,
                "help": self.help,
                "text": self.text,
            },
            ensure_ascii=False,
        )

    def render(self, color: bool = True) -> str:
        c = ANSIColor if color else NoColor
        return str(VIOLATION_TEMPLATE.render(v=self, c=c))

    def is_pointer_line(self, line: str) -> bool:
        return bool(line.strip()) and set(line.strip()) == {"^"}
