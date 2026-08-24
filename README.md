# Parcoblatta

![Parcoblatta Logo](./doc/images/logo.png)

- (n) A Pennsylvania Wood Cockroach
- (n) A not so obvious and definitely over-reaching pun (tree(sitter) + roach (Kafka's "The Metamorphosis"))
- (this) a structural code search tool for kicking off focused pipelines

Given a codebase, Parcoblatta runs user-provided Tree-sitter queries and publishes the matches to JSONL files, stdout, or Kafka topics.

That sounds boring. Good.

The point is to use deterministic structural queries to find the exact code you care about, then hand that bounded slice to whatever comes next: a linter, a script, a GNU tool, a queue, a dashboard, or an agent that badly needs less room to wander.

For the longer rant, see [WHY.md](./WHY.md).
For concrete examples, see [USES.md](./USES.md).

## What it is for

Parcoblatta turns this:

```text
read the repo, find all the places where this pattern happens, and then...
```

into this:

```text
Tree-sitter query
  -> match event
  -> JSONL / Kafka / prompt
  -> focused downstream work
```

It is especially useful when the downstream worker is an AI coding agent. Agents are much better when the task is already boxed in:

- review this function
- fix this capture
- explain this class
- reject this bad pattern
- generate a test for this one scope
- validate that this exact structural issue is gone

Tree-sitter chooses the scope. Parcoblatta packages it. The agent, script, or human gets a small thing to deal with.

## Usage

Run a flow config:

```bash
uv run parcoblatta run examples/flows/functions_and_classes.yml
```

A config has shared code input and one or more rules. Each rule has one or more Tree-sitter queries and outputs.

```yaml
code:
  file: src/parcoblatta

rules:
  - query:
      file: queries/functions.scm
    output:
      file: functions.jsonl

  - query:
      text: |
        (class_definition) @class
    output:
      file: classes.jsonl
```

Each JSONL line is a `MatchEvent`: one Tree-sitter query match with grouped captures, full contiguous source context, compact source context, and quickfix-style location metadata.

```json
{
  "file": "src/parcoblatta/scanner/scanner.py",
  "language": "python",
  "query": "functions",
  "match_index": 0,
  "pattern_index": 0,
  "full_text": "...",
  "compact_text": "...",
  "captures": []
}
```

## Prompt rendering

Parcoblatta can also render prompt events from match events. It does not call an LLM. It prepares the next event for whatever worker consumes it.

```bash
uv run parcoblatta run examples/flows/review_functions.yml
```

That example emits one prompt per matched function, with instructions to stay inside the captured scope.

Prompt templates use Python `string.Template` syntax. Available variables include:

- `$file`
- `$language`
- `$query`
- `$match_index`
- `$pattern_index`
- `$full_text`
- `$compact_text`
- `$quickfix`
- `$captures_json`
- `$event_json`

Example:

```yaml
rules:
  query:
    file: queries/functions.scm
  prompt:
    text: |
      You are reviewing one $language match from $file.
      Stay inside this scope.

      $compact_text
    output:
      file: prompts.jsonl
```

## Linting

Parcoblatta also includes a small Tree-sitter-query-based linter.

```bash
uv run parcoblatta lint examples/lint/demo_violations.py
```

Built-in example rules live in `queries/lint/`, including bare `except`, mutable defaults, `eval` / `exec`, debug `print`, and production `assert` patterns.

By default, linting skips common generated/vendor directories such as `.venv`, `venv`, `site-packages`, `node_modules`, `dist`, and cache directories. Add more ignores with `--exclude` or in `pyproject.toml`:

```toml
[tool.parcoblatta.lint]
code = ["."]
exclude = [".venv", "venv", "site-packages", "_scratch", "generated"]
```

## Kafka output

If you have Kafka or Redpanda listening on `localhost:9092`:

```bash
uv run parcoblatta run examples/flows/kafka.yml
```

Example output config:

```yaml
output:
  topic: parcoblatta.matches
  kafka:
    bootstrap_servers: localhost:9092
    client_id: parcoblatta-example
```

## Why Kafka? Why JSONL?

Kafka is for fan-out, replay, queues, and longer-running pipelines.
JSONL is for when that is obviously too much.

Both are just ways to keep Parcoblatta from becoming a giant swiss-army-knife tool. It finds structural matches and emits events. What happens after that is your business.

## Writing queries

A few Python queries are provided to get started. The real power begins when you write your own.

If you were hoping for non-Python-centric queries, sorry, ask an LLM I guess.
Or better yet, learn Tree-sitter's scheme-like query syntax. It's not hard, and it's worth it.
