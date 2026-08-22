from __future__ import annotations

from typing import TYPE_CHECKING

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query, QueryCursor

from .models import Capture, MatchEvent
from .text_formatting import compact_text, full_text

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .config import CodeInput, TreesitterQuery


def match_events(code: CodeInput, query_config: TreesitterQuery) -> Iterator[MatchEvent]:
    """Run one Tree-sitter query configuration over code inputs.

    :param code: Code input configuration.
    :param query_config: Tree-sitter query configuration.
    :return: Match events produced by running the configured queries.
    """
    if query_config.language != "python":
        raise ValueError(f"unsupported language: {query_config.language}")

    tree_sitter_language = Language(tspython.language())
    parser = Parser(tree_sitter_language)
    queries = list(query_config.resolve_queries())

    for code_file in code.resolve_files():
        source = code_file.read_bytes()
        tree = parser.parse(source)

        for query_spec in queries:
            query = Query(tree_sitter_language, query_spec.source)
            cursor = QueryCursor(query)
            matches = cursor.matches(tree.root_node)

            for match_index, (pattern_index, captures) in enumerate(matches):
                nodes = [node for nodes in captures.values() for node in nodes]

                yield MatchEvent(
                    name=query_config.name,
                    file=code_file,
                    language=query_config.language,
                    query=query_spec.name,
                    match_index=match_index,
                    pattern_index=pattern_index,
                    full_text=full_text(source, nodes),
                    compact_text=compact_text(source, nodes),
                    captures=[
                        Capture.from_node(str(capture_name), node, source)
                        for capture_name, nodes in captures.items()
                        for node in nodes
                    ],
                )
