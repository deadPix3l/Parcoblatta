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


def compact_text(source: bytes, captures) -> str:
    """Build compact match text from source lines touched by captures.

    If a capture is named ``target``, include a caret pointer line under the first
    line of each target capture. Queries do not need a target capture; without
    one this renders plain compact context.
    """
    source_lines = source.decode("utf-8", errors="replace").splitlines()
    nodes = [node for capture_nodes in captures.values() for node in capture_nodes]
    target_nodes = captures.get("target", [])
    merged = merge_line_ranges(captured_line_range(node) for node in nodes)

    chunks: list[str] = []
    for start_line, end_line in merged:
        lines: list[str] = []
        for line_index in range(start_line, end_line + 1):
            lines.append(source_lines[line_index])
            if pointer := target_pointer(line_index, target_nodes):
                lines.append(pointer)
        chunks.append("\n".join(lines))

    return "\n...\n".join(chunks)


def merge_line_ranges(line_ranges) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start_line, end_line in sorted(line_ranges):
        if not merged or start_line > merged[-1][1] + 1:
            merged.append((start_line, end_line))
            continue
        merged[-1] = (merged[-1][0], max(merged[-1][1], end_line))
    return merged


def target_pointer(line_index: int, target_nodes) -> str:
    pointers = []
    for node in target_nodes:
        if node.start_point.row != line_index:
            continue

        text = node.text.decode("utf-8", errors="replace") if node.text else ""
        first_line = text.split("\n", maxsplit=1)[0]
        pointers.append((node.start_point.column, max(1, len(first_line))))

    if not pointers:
        return ""

    width = max(column + length for column, length in pointers)
    line = [" "] * width
    for column, length in pointers:
        line[column : column + length] = ["^"] * length
    return "".join(line)


def captured_line_range(node) -> tuple[int, int]:
    start_line = node.start_point.row
    end_line = node.end_point.row
    if node.end_point.column == 0:
        end_line -= 1
    return start_line, max(start_line, end_line)
