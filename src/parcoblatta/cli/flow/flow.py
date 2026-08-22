from __future__ import annotations

from parcoblatta.cli.flow.config import (
    CodeInput,
    Flow,
    KafkaConfig,
    Output,
    PromptTemplate,
    QuerySpec,
    Rule,
    TreesitterQuery,
)

__all__ = [
    "CodeInput",
    "Flow",
    "KafkaConfig",
    "Output",
    "PromptTemplate",
    "QuerySpec",
    "Rule",
    "TreesitterQuery",
]


if __name__ == "__main__":
    from sys import argv

    try:
        from rich import print
    except ImportError:
        pass

    x = Flow.from_yaml(argv[1])
    print(x)
