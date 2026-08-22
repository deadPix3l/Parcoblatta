# Uses

Parcoblatta finds structural matches in code and emits them as events.
What happens after that is up to you.

## Single-scope agent work

Feed functions, classes, call sites, or suspicious patterns into an agent one at a time.

Not:

```text
read the repo and improve it
```

More like:

```text
review this captured function only
```

or:

```text
this query found a mutable default argument; propose the smallest safe fix
```

That can mean review, refactoring, test generation, type-hint cleanup, security checks, doc cleanup, or whatever else you can make useful at one bounded scope.

## Deterministic checks before and after AI

Use one structural query to find the work.
Use another structural query to verify the shape of the result.

The model can still be wrong. Fine. Make it wrong in a small box, then check the box.

## Linting and structural policy checks

Parcoblatta includes a small Tree-sitter-query-based linter, but the same shape works for project-specific rules:

- no bare `except`
- no mutable defaults
- no production `assert`
- no `eval` / `exec`
- no local antipattern your team keeps seeing
- no generated-code shape you want to reject

These do not need to be AI tasks. Sometimes the right answer is a deterministic rule and a failing build.

## Fan-out

Take one match and send it to multiple workers:

- one reviews it
- one writes tests
- one looks for a stdlib or third-party replacement
- one checks for security issues
- one runs boring formatting or lint fixes

Then compare the results instead of trusting the first confident blob of generated code.

## Loops without one giant context

You can build agent loops on top of this without letting the loop eat the repo.

A match goes to `pending`.
A worker adds a prompt and publishes to `in_progress`.
A reviewer publishes back to `needs_work` or `done`.

Kafka is useful here because replay, fan-out, and failure handling are real things.
JSONL is useful when Kafka would be ridiculous.

The important part is that the loop is about a captured scope, not vibes over a whole codebase.

## Plain old scripts

The downstream consumer does not have to be an LLM.

A Parcoblatta event can feed:

- shell scripts
- GNU tools
- Python scripts
- dashboards
- review queues
- metrics jobs
- migration tooling
- anything that can read JSONL or Kafka

Tree-sitter finds the scope. Parcoblatta emits the event. Everything else can stay small.
