# A few ideas (ie, the WHY section)

I'm not here to tell you what to do with this, or why.
I built it because I was tired of having X-Y adapter tools
for every combination of every tool. Its combinatorial and its not manageable.
So I decided that a common interface in the middle: X-Kafka-Y would allow me to
easily make changes if I needed to.

This is the X-Kafka part, where X=Treesitter, the thing I needed at the moment I wrote this.
I leave Y and everything downstream to you,
its not my business to guess at what you're trying to do.

Below is a nonexhaustive list of things I suspect this could be used for:

## Automated, single-scope agentic tasks

Feed functions/classes/blocks into an LLM with prompts like:
- "Optimize this block: %s"
- "add type hints and constrain loose typing on these parameters"
- "is this code nessessary and bespoke? suggest a library to replace it (if applicable)"

code quality checks, refactoring, test coverage, SMT solving, etc.

## Loop Engineering?

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


## Fan out

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

