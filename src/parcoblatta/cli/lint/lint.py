from collections import Counter
from pathlib import Path
from sys import stderr

from parcoblatta.cli.lint.violation import Violation
from parcoblatta.scanner.input.code import CodeInput
from parcoblatta.scanner.query.treesitter import TreesitterQuery
from parcoblatta.scanner.scanner import match_events

DEFAULT_QUERY_DIR = Path("queries/lint")


def lint(
    code_dir: Path | str = "src/",
    query: Path | list[Path] | None = None,
    quiet: bool = False,
    limit: int | None = None,
    no_color: bool = False,
    stats: bool = False,
    jsonl: bool = False,
) -> int:
    """Scan Python files for lint violations."""
    code_path = Path(code_dir)
    if code_path.is_file() and code_path.suffix != ".py":
        print(f"Warning: {code_path} is not a .py file", file=stderr)
        return 0

    query_inputs = [query] if isinstance(query, Path) else query or [DEFAULT_QUERY_DIR]

    counts: Counter[str] = Counter()
    events = match_events(
        CodeInput(file=[code_path]),
        TreesitterQuery(file=query_inputs),
    )

    for event in events:
        violation = Violation.from_event(event, color=not no_color)
        counts.update([violation.rule])
        if not quiet:
            print(violation.to_jsonl() if jsonl else violation)

        if limit is not None and counts.total() >= limit:
            if not quiet and not jsonl:
                print(f"\nReached limit of {limit} violations, stopping scan.")
            break

    if counts and not jsonl:
        print(f"Found {counts.total()} errors.")

        if stats:
            print("\nViolations by rule:")
            for rule, count in counts.most_common():
                print(f"  {rule}: {count}")

    return counts.total()
