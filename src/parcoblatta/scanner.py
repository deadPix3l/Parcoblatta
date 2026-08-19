from __future__ import annotations

from tree_sitter import Language, Parser, Query, QueryCursor, Tree
import tree_sitter_python as tspython

from .models import CaptureEvent, CaptureEventRange

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from .flow import ParcoblattaFlow


def capture_events(flow: ParcoblattaFlow) -> Iterator[CaptureEvent]:
    """Run the Tree-sitter portion of a Parcoblatta flow.

    :param flow: Validated Parcoblatta flow.
    :return: Capture events produced by running the configured queries.
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
            yield from run_query(
                path=code_file,
                source=source,
                tree=tree,
                query=query,
                query_name=query_spec.name,
                language=flow.query.language,
            )


def run_query(
    *,
    path: Path,
    source: bytes,
    tree: Tree,
    query: Query,
    query_name: str,
    language: str,
) -> Iterator[CaptureEvent]:
    """Run a compiled query and yield normalized capture events.

    :param path: Source file path.
    :param source: Source file bytes.
    :param tree: Parsed Tree-sitter tree.
    :param query: Compiled Tree-sitter query.
    :param query_name: Query name for emitted events.
    :param language: Source language.
    :return: Capture events.
    """
    cursor = QueryCursor(query)
    captures = cursor.captures(tree.root_node)

    for capture_name, nodes in captures.items():
        for node in nodes:
            text = source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
            yield CaptureEvent(
                file=path,
                language=language,
                query=query_name,
                capture=str(capture_name),
                range=CaptureEventRange.from_node(node),
                text=text,
                node_type=node.type,
            )
