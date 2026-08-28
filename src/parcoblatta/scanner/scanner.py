from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query, QueryCursor

from parcoblatta.scanner.models import Capture, MatchEvent
from parcoblatta.utils.text_formatting import compact_text, full_text

if TYPE_CHECKING:
    from collections.abc import Iterator

    from parcoblatta.scanner.input.code import CodeInput
    from parcoblatta.scanner.query.treesitter import TreesitterQuery


def match_events_from_source(
    source: bytes | str,
    *,
    file: Path | str,
    query_config: TreesitterQuery,
) -> Iterator[MatchEvent]:
    """Run one Tree-sitter query configuration over a single source payload.

    This lower-level API is useful for integrations where code arrives from a
    stream/message instead of Parcoblatta resolving files itself.

    :param source: Source code as bytes or text.
    :param file: File/path-like identifier to include in emitted events.
    :param query_config: Tree-sitter query configuration.
    :return: Match events produced by running the configured queries.
    """
    if query_config.language != "python":
        raise ValueError(f"unsupported language: {query_config.language}")

    source_bytes = source.encode("utf-8") if isinstance(source, str) else source
    tree_sitter_language = Language(tspython.language())
    parser = Parser(tree_sitter_language)
    tree = parser.parse(source_bytes)

    for query_spec in query_config.resolve_queries():
        query = Query(tree_sitter_language, query_spec.source)
        cursor = QueryCursor(query)
        matches = cursor.matches(tree.root_node)

        for match_index, (pattern_index, captures) in enumerate(matches):
            nodes = [node for nodes in captures.values() for node in nodes]

            yield MatchEvent(
                name=query_config.name,
                file=Path(file),
                language=query_config.language,
                query=query_spec.name,
                match_index=match_index,
                pattern_index=pattern_index,
                full_text=full_text(source_bytes, nodes),
                compact_text=compact_text(source_bytes, captures),
                captures=[
                    Capture.from_node(str(capture_name), node, source_bytes)
                    for capture_name, nodes in captures.items()
                    for node in nodes
                ],
                settings={
                    str(key): str(value)
                    for key, value in query.pattern_settings(pattern_index).items()
                },
            )


def match_events(code: CodeInput, query_config: TreesitterQuery) -> Iterator[MatchEvent]:
    """Run one Tree-sitter query configuration over code inputs.

    :param code: Code input configuration.
    :param query_config: Tree-sitter query configuration.
    :return: Match events produced by running the configured queries.
    """
    for code_file in code.resolve_files():
        yield from match_events_from_source(
            code_file.read_bytes(),
            file=code_file,
            query_config=query_config,
        )
