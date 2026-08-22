# Why Parcoblatta Exists

Agents suck.
Every day I use them, and every day I'm reminded of this.

Not always, not at everything, but enough to be incredibly frustrating.
You should not hand one a whole repo and say "make it better"
(I do it frequently, and I regret it every single time.)

They over-engineer.
The manner in which they were trained means they understand the patterns and decisions
a senior engineer would choose, but they've undoubtedly read much more junior-level code.
(And as model collapse sets in, probably more AI-generated code than anything.)
What you get is a junior pretending to be a senior, pumping out slop confidently.

They reach for patterns that show up too much in their training data. They invent abstractions because they have seen a thousand blog posts that look like that. They make simple code clever. They make local changes global. They wander. And then they tell you how one function whose entire job is to call another function (and so on, until the actual logic is 4 levels of indirection away) is best practices.

They fail to understand that comments and docstrings that just restate the function signature add no value.
They invent the wheel everywhere rather than reaching for third-party or even stdlib alternatives, until
eventually you have 100k lines of unreadable slop that doesn't even really work yet!

That is how you get broad, confident, unnecessary change,
along with a mini-manifesto about how that slop is actually
game changing, revolutionary, clean code.
You are a prophet, and your ideas are so good!
Other self-serving bullshit here.
And behind the curtain is garbage code the industry has agreed isn't worth
reading anymore.

Enough is enough!
Parcoblatta is a way to push back on that.

It's not just for AI. It can be used on its own, it includes a linter, it can be used to call deterministic,
40+ year old GNU tools or hand-written scripts. This will always be important, and will always be supported.

But one of its main focuses is AI. It's one of the main reasons I wrote it.
I'm tired of saying "read through the codebase, find all instances of this pattern and then..."

Not only is it annoying, it's context bloat.
I want to define a structural search with a deterministic query,
find exactly the issue I want fixed,
pull it out,
feed it to the model in a new context,
make a decision,
and maybe even push that decision into a full pipeline where a ton of work can be done.

I want to have more structural queries that can confirm that work.

Maybe I'm alone.
Maybe the industry has moved on from reading the code.
They've all decided that fixing the code isn't worth it; just regenerate it.
Why write in a structured, parsable, consistent, testable syntax,
when you can write in the nuanced, contradictory, unclear language that is English?
Dijkstra is no doubt rolling in his grave.

"Just prompt better"
Tried it.
It does kinda work.
I wrote metaprompts, and ralph-loops, and skills, and pi extensions.
It's better, I'll admit.

But I still have to deal with everyone else's shitty vibe-code.
I have to read projects even the "authors" didn't read.

This is my attempt at fixing garbage code, rejecting bad changes,
stripping unnecessary context to the bare minimum needed,
and kicking off agent coding pipelines in a way that doesn't lead to an abyss of despair.

I hope it brings you value.
It's changed my workflow in ways I couldn't have imagined when I started.
I hope it does the same for you.
