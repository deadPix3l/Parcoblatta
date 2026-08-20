# Parcoblatta

![Parcoblatta Logo](./images/logo.png)

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
uv run parcoblatta run example_configs/functions_and_classes.yml
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

Each JSONL line is a `MatchEvent`: one Tree-sitter query match with grouped captures, full contiguous source context, and compact source context.

```json
{
  "file": "src/parcoblatta/flow.py",
  "language": "python",
  "query": "functions",
  "match_index": 0,
  "pattern_index": 0,
  "full_text": "...",
  "compact_text": "...",
  "captures": []
}
```

### Prompt rendering

Parcoblatta can also render prompt events from match events. It does not call an LLM; it just prepares the next event for whatever worker consumes it.

```bash
uv run parcoblatta run example_configs/prompts.yml
uv run parcoblatta run example_configs/double_prompts.yml
```

Prompt templates use Python `string.Template` syntax. Available variables include:

- `$file`
- `$language`
- `$query`
- `$match_index`
- `$pattern_index`
- `$full_text`
- `$compact_text`
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
uv run parcoblatta run example_configs/kafka.yml
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


## A few ideas (ie, the WHY section)

I'm not here to tell you what to do with this, or why.
I built it because I was tired of having X-Y adapter tools
for every combination of every tool. Its combinatorial and its not manageable.
So I decided that a common interface in the middle: X-Kafka-Y would allow me to
easily make changes if I needed to.

This is the X-Kafka part, where X=Treesitter, the thing I needed at the moment I wrote this.
I leave Y and everything downstream to you,
its not my business to guess at what you're trying to do.

Below is a nonexhaustive list of things I suspect this could be used for:

### Automated, single-scope agentic tasks

Feed functions/classes/blocks into an LLM with prompts like:
- "Optimize this block: %s"
- "add type hints and constrain loose typing on these parameters"
- "is this code nessessary and bespoke? suggest a library to replace it (if applicable)"

code quality checks, refactoring, test coverage, SMT solving, etc.

### Loop Engineering?

This is a bonus idea. It has not been tested. It's based on one of the newer buzzwords.

take a match (file, function, variable, anything), feed it into a topic `pending`.
Another consumer subscribes to that topic, adds a prompt, and publishes to `in_progress`:
```text
You are a <something> specialist. You are tasked with <blank>
<context that needs to be carried forward in every run>

Objective: <something an agent can achieve>.
Termination Condition: print DONE if done (or STUCK if needing human assistance)

<context from last run if applicable>

The original block of code:
<capture here>
```

Keep publishing the result of this agent into `in_progress` until DONE/STUCK is reached.
This is essentially a kafka based ralph loop.

YOu can also have a mutual ping-pong between the `acheive_task` and `reviewer` topics.
I suspect this will yield better results because LLMs are too sycophantic to be critical of
the work produced in their own context. THis also creates a boundary to switch models.


### Fan out

Write a basic sketch of a function. It's not very good, but it gets the point accross.
Maybe you didn't even write it, your agent did. It's probably slop. Doesn't matter.

push it to a topic.
Multiple consumers, all doing something different.
- write tests
- refactors for clarity.
- adds a docstring if missing.
- runs `ruff check --fix`
- suggests a library that does the same thing better
- scan for bugs

Then come back together and produce an updated version.

