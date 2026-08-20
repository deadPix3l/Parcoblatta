from __future__ import annotations

from parcoblatta.config import (
    CodeInput,
    KafkaConfig,
    ParcoblattaFlow,
    ParcoblattaOutput,
    ParcoblattaRule,
    PromptTemplate,
    QuerySpec,
    TreesitterQuery,
)

__all__ = [
    "CodeInput",
    "KafkaConfig",
    "ParcoblattaFlow",
    "ParcoblattaOutput",
    "ParcoblattaRule",
    "PromptTemplate",
    "QuerySpec",
    "TreesitterQuery",
]


if __name__ == "__main__":
    from sys import argv

    try:
        from rich import print
    except ImportError:
        pass

    x = ParcoblattaFlow.from_yaml(argv[1])
    print(x)
