def full_text(source: bytes, nodes) -> str:
    """Build contiguous match text from full source lines touched by captures.

    :param source: Source file bytes.
    :param nodes: Captured Tree-sitter nodes for one match.
    :return: Full source lines from the first touched line through the last touched line.
    """
    source_lines = source.decode("utf-8", errors="replace").splitlines()
    line_ranges = [captured_line_range(node) for node in nodes]
    start_line = min(start_line for start_line, _ in line_ranges)
    end_line = max(end_line for _, end_line in line_ranges)
    return "\n".join(source_lines[start_line : end_line + 1])


def compact_text(source: bytes, nodes) -> str:
    """Build compact match text from source lines touched by captures.

    :param source: Source file bytes.
    :param nodes: Captured Tree-sitter nodes for one match.
    :return: Full source lines touched by captures, with omitted lines represented by ``...``.
    """
    source_lines = source.decode("utf-8", errors="replace").splitlines()
    line_ranges = sorted(captured_line_range(node) for node in nodes)
    merged: list[tuple[int, int]] = []

    for start_line, end_line in line_ranges:
        if not merged or start_line > merged[-1][1] + 1:
            merged.append((start_line, end_line))
            continue
        merged[-1] = (merged[-1][0], max(merged[-1][1], end_line))

    return "\n...\n".join(
        "\n".join(source_lines[start_line : end_line + 1]) for start_line, end_line in merged
    )


def captured_line_range(node) -> tuple[int, int]:
    start_line = node.start_point.row
    end_line = node.end_point.row
    if node.end_point.column == 0:
        end_line -= 1
    return start_line, max(start_line, end_line)
