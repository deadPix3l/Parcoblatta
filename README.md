# Parcoblatta

![Parcoblatta Logo](./doc/images/logo.png)

- (n) A Pennsylvania Wood Cockroach
- (n) A not so obvious and definitely over-reaching pun (tree(sitter) + roach (kafka's "the metamorphosis"))
- (this) a code analysis pipeline

Given a code base, run a series of user provided treesitter queries, and publish the matches to JSONL files or Kafka topics.

A few queries have been provided to get you started, but the real power begins with writing your own queries.
If you were hoping for non-python-centric queries, sorry, ask an LLM I guess?
Or better yet, learn treesitters scheme-like syntax, its not hard, an it's so worth it!


## Usage

Run a config file:

```bash
uv run parcoblatta run examples/flows/functions_and_classes.yml
```

A config has shared code input and one or more rules. Each rule has a Tree-sitter query and an output.

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

Parcoblatta can also render prompt events from match events. It does not call an LLM; it just prepares the next event for whatever worker consumes it.

```bash
uv run parcoblatta run examples/flows/review_functions.yml
```

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
  output:
    file: matches.jsonl
  prompt:
    text: |
      Review this $language match from $file.

      $compact_text
    output:
      file: prompts.jsonl
```

### Kafka output

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


## I've published the capture groups to a kafka topic, now what?

This is where parcoblatta ends. This is not a batteries-included, swiss-army-knife, does-a-million-things tool.
Kafka is a powerhouse with a thriving community, enterprise support, tons of great libraries, etc.
You have the beginning of a pipeline.
Its up to you to build the next steps however you see fit (AI can help a lot!).

I recommend redpanda connect (formerly benthos, bento is the OSS fork if thats your thing) or faststream,
but thats just my personal preference.


## Kafka is a bit heavy, no? Thats way more power than I need for <simple task>.

Fair point. JSONL is also provided.
I could see SQLite or Spark or Parquet also being useful, but that sounds like swiss-army-knife stuff.
You can find a JSONL-Y thing if you need it. I believe in you.

## What can it do?

see: [Uses.md]
