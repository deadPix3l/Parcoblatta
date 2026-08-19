from __future__ import annotations

from dataclasses import dataclass

from tree_sitter import Language, Node, Parser, Query, QueryCursor, Tree
import tree_sitter_python as tspython

from .models import CaptureEvent, CaptureEventRange

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Generator
    from pathlib import Path

    from .flow import ParcoblattaFlow, TreesitterQuery


@dataclass(frozen=True)
class QuerySpec:
    name: str
    source: str
    language: str = "python"


def capture_events(flow: ParcoblattaFlow) -> Iterator[CaptureEvent]:
    """Run the Tree-sitter portion of a Parcoblatta flow.

    :param flow: Validated Parcoblatta flow.
    :return: Capture events produced by running the configured queries.
    """
    queries = list(load_queries(flow.query))
    for code_file in flow.code.resolve_files():
        yield from capture_file(code_file, queries=queries, language=flow.query.language)


def load_queries(query: TreesitterQuery) -> Generator[QuerySpec, None, None]:

    for index, text in enumerate(query.text):
        yield QuerySpec(name=f"inline:{index}", source=text, language=query.language)

    for path in query.file:
        if path.is_dir():
            query_files = sorted(path.rglob("*.scm") if query.recursive else path.glob("*.scm"))
        else:
            query_files = [path]

        for query_file in query_files:
            yield QuerySpec(
                name=query_file.stem,
                source=query_file.read_text(encoding="utf-8"),
                language=query.language,
            )


def capture_file(path: Path, *, queries: Iterable[QuerySpec], language: str) -> Iterator[CaptureEvent]:
    """Parse one source file and emit query captures.

    :param path: Source file to parse.
    :param queries: Loaded Tree-sitter queries.
    :param language: Source language.
    :return: Capture events from the file.
    """
    if language != "python":
        raise ValueError(f"unsupported language: {language}")

    tree_sitter_language = Language(tspython.language())
    parser = Parser(tree_sitter_language)

    source = path.read_bytes()
    tree = parser.parse(source)

    for query_spec in queries:
        query = Query(tree_sitter_language, query_spec.source)
        yield from run_query(
            path=path,
            source=source,
            tree=tree,
            query=query,
            query_name=query_spec.name,
            language=language,
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
            yield event_from_node(
                path=path,
                source=source,
                node=node,
                query_name=query_name,
                capture_name=str(capture_name),
                language=language,
            )


def event_from_node(
    *,
    path: Path,
    source: bytes,
    node: Node,
    query_name: str,
    capture_name: str,
    language: str,
) -> CaptureEvent:
    """Convert a Tree-sitter node capture into a CaptureEvent.

    :param path: Source file path.
    :param source: Source file bytes.
    :param node: Captured Tree-sitter node.
    :param query_name: Query name for emitted events.
    :param capture_name: Capture group name.
    :param language: Source language.
    :return: Capture event.
    """
    text = source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")

    return CaptureEvent(
        file=path,
        language=language,
        query=query_name,
        capture=capture_name,
        range=CaptureEventRange(
            start_line=node.start_point.row + 1,
            end_line=node.end_point.row + 1,
            start_column=node.start_point.column,
            end_column=node.end_point.column,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
        ),
        text=text,
        node_type=node.type,
    )
