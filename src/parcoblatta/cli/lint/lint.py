from collections import Counter
from pathlib import Path
from sys import stderr

from parcoblatta import QUERIES_PATH
from parcoblatta.cli.lint.violation import Violation
from parcoblatta.scanner.input.code import CodeInput
from parcoblatta.scanner.query.treesitter import TreesitterQuery
from parcoblatta.scanner.scanner import match_events

DEFAULT_QUERY_DIR = Path(QUERIES_PATH / "lint")


def lint(
    code: Path | list[Path] | None = None,
    query: Path | list[Path] | None = None,
    quiet: bool = False,
    limit: int | None = None,
    no_color: bool = False,
    stats: bool = False,
    jsonl: bool = False,
    select: list[str] | None = None,
    ignore: list[str] | None = None,
    exclude: list[str] | None = None,
) -> int:
    """Scan Python files for lint violations."""
    code_inputs = [code] if isinstance(code, Path) else code or [Path("src")]
    for code_path in code_inputs:
        if code_path.is_file() and code_path.suffix != ".py":
            print(f"Warning: {code_path} is not a .py file", file=stderr)
            return 0

    if isinstance(query, Path):
        query_inputs = [query]
    elif query is None:
        query_inputs = [DEFAULT_QUERY_DIR]
    else:
        query_inputs = query
    selected = set(select or [])
    ignored = set(ignore or [])

    counts: Counter[str] = Counter()
    events = match_events(
        CodeInput(file=code_inputs, exclude=exclude or []),
        TreesitterQuery(file=query_inputs),
    )

    for event in events:
        violation = Violation.from_event(event, color=not no_color)
        if selected and violation.rule not in selected:
            continue
        if violation.rule in ignored:
            continue

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
