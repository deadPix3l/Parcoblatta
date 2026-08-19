from __future__ import annotations

from tree_sitter import Language, Parser, Query, QueryCursor, Tree
import tree_sitter_python as tspython

from .models import Capture, MatchEvent

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from .flow import ParcoblattaFlow


def match_events(flow: ParcoblattaFlow) -> Iterator[MatchEvent]:
    """Run the Tree-sitter portion of a Parcoblatta flow.

    :param flow: Validated Parcoblatta flow.
    :return: Match events produced by running the configured queries.
    """
    if flow.query.language != "python":
        raise ValueError(f"unsupported language: {flow.query.language}")

    tree_sitter_language = Language(tspython.language())
    parser = Parser(tree_sitter_language)
    queries = list(flow.query.resolve_queries())

    for code_file in flow.code.resolve_files():
        source = code_file.read_bytes()
        tree = parser.parse(source)

        for query_spec in queries:
            query = Query(tree_sitter_language, query_spec.source)
            cursor = QueryCursor(query)
            matches = cursor.matches(tree.root_node)

            for match_index, (pattern_index, captures) in enumerate(matches):
                nodes = [node for nodes in captures.values() for node in nodes]
                start_byte = min(node.start_byte for node in nodes)
                end_byte = max(node.end_byte for node in nodes)

                yield MatchEvent(
                    file=code_file,
                    language=flow.query.language,
                    query=query_spec.name,
                    match_index=match_index,
                    pattern_index=pattern_index,
                    full_text=source[start_byte:end_byte].decode("utf-8", errors="replace"),
                    captures=[
                        Capture.from_node(str(capture_name), node, source)
                        for capture_name, nodes in captures.items()
                        for node in nodes
                    ],
                )

