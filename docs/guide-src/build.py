"""Builds docs/how-raffle-cli-was-built.html from the real source files (snippets are pulled with ast)."""

from __future__ import annotations

import ast
import re
import subprocess
import sys
import textwrap
from html import escape
from pathlib import Path

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer, get_lexer_by_name

sys.path.insert(0, str(Path(__file__).parent))
import diagrams as D  # noqa: E402

REPO = Path(sys.argv[1])
OUT = Path(sys.argv[2])
SRC = REPO / "src" / "raffle_cli"
FMT = HtmlFormatter(nowrap=True, style="friendly")


# --------------------------------------------------------------------- helpers
def hl(code: str, lang: str = "python") -> str:
    lexer = PythonLexer() if lang == "python" else get_lexer_by_name(lang)
    return highlight(code, lexer, FMT)


def snip(code: str, lang: str = "python", caption: str = "") -> str:
    cap = f'<div class="cap">{escape(caption)}</div>' if caption else ""
    body = textwrap.dedent(code).strip(chr(10))
    long_cls = " long" if body.count(chr(10)) > 22 else ""
    return f'<div class="code{long_cls}">{cap}<pre>{hl(body, lang)}</pre></div>'


def code(file: str, qual: str, caption: str | None = None, strip_doc: bool = False) -> str:
    path = (REPO / file) if "/" in file else (SRC / file)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = tree
    for part in qual.split("."):
        node = next(n for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == part)
    start = min([node.lineno] + [d.lineno for d in node.decorator_list])
    lines = source.splitlines()[start - 1 : node.end_lineno]
    text = textwrap.dedent("\n".join(lines))
    return snip(text, "python", caption or f"{path.relative_to(REPO)} · {qual}")


def lines_of(file: str, a: str, b: str, lang="python", caption="") -> str:
    """Snippet between the first line containing `a` and the first following line containing `b` (inclusive)."""
    path = (REPO / file) if "/" in file else (SRC / file)
    ls = path.read_text(encoding="utf-8").splitlines()
    i = next(k for k, l in enumerate(ls) if a in l)
    j = next(k for k in range(i, len(ls)) if b in ls[k])
    return snip("\n".join(ls[i : j + 1]), lang, caption or f"{path.relative_to(REPO)}")


def callout(kind: str, title: str, body: str) -> str:
    return f'<div class="callout {kind}"><div class="ct">{title}</div>{body}</div>'


def decision(title: str, body: str) -> str:
    return callout("decision", f"Technical decision: {title}", body)


def tip(title: str, body: str) -> str:
    return callout("tip", title, body)


def warn(title: str, body: str) -> str:
    return callout("warn", title, body)


def chapter(num: int | str, title: str, anchor: str) -> str:
    return f'<h1 id="{anchor}"><span class="num">{num}</span>{title}</h1>'


# ---------------------------------------------------------------- derived data
def loc(name: str) -> int:
    return len((SRC / name).read_text().splitlines())


def reel_time(steps: int) -> float:
    return sum(0.04 + 0.28 * (p / steps) ** 3 for p in range(2, steps))


T1 = 0.18 + reel_time(18)
T2 = 0.18 + reel_time(30)
REVEAL = T2 + 0.5

collected = subprocess.run(
    [sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=REPO, capture_output=True, text=True
).stdout
counts: dict[str, int] = {}
for line in collected.splitlines():
    m = re.match(r"tests/(\w+)\.py::", line)
    if m:
        counts[m.group(1)] = counts.get(m.group(1), 0) + 1
TOTAL = sum(counts.values())

# ---------------------------------------------------------------------- content
P: list[str] = []
add = P.append

TOC = [
    ("1", "What we built", "c1"), ("2", "The big picture", "c2"), ("3", "Where we started: the review", "c3"),
    ("4", "Python foundations you meet in this code", "c4"), ("5", "The raffle engine", "c5"),
    ("6", "Files, validation and resuming", "c6"), ("7", "Randomness, fairness and --seed", "c7"),
    ("8", "The classic terminal interface", "c8"), ("9", "The fireworks", "c9"), ("10", "The Textual interface", "c10"),
    ("11", "The slot machine", "c11"), ("12", "Testing", "c12"), ("13", "Technical decisions, in one table", "c13"),
    ("14", "Things that went wrong (and what they taught)", "c14"), ("15", "Exercises", "c15"),
    ("16", "Glossary and how to run everything", "c16"),
]

add(f"""
<section class="cover">
  <div class="kicker">pybaq · meetup tooling</div>
  <h1 class="title">How <code>raffle-cli</code> was built</h1>
  <p class="subtitle">A beginner's guide to the code, the diagrams and the technical decisions behind it</p>
  <div class="coverbox">
    <p><b>Version covered:</b> 0.2.0 &nbsp;·&nbsp; <b>Python:</b> 3.10+ &nbsp;·&nbsp; <b>Code:</b> {sum(loc(f.name) for f in SRC.glob('*.py'))} lines in {len(list(SRC.glob('*.py')))} modules, {TOTAL} tests</p>
    <p><b>Honest note:</b> the first prototype was written by Andoresu; this version (restructure, fixes, persistence,
    fireworks, Textual slot machine, tests, docs) was written together with Claude, an AI assistant. Reading this guide is how the
    learning gets back to you: every important line is explained, every decision has a reason, and the exercises at the end
    ask you to change the program yourself.</p>
  </div>
  <p class="how"><b>How to use this guide.</b> Read a chapter, then open the file it talks about and find the code. Run the
  program. Change a number, break something on purpose, read the error. Typing code yourself teaches far more than reading it.</p>
</section>
<section class="toc"><h2>Contents</h2><ol>{''.join(f'<li><a href="#{a}"><span>{n}</span> {t}</a></li>' for n, t, a in TOC)}</ol></section>
""")

# 1 -------------------------------------------------------------------------
add(chapter(1, "What we built", "c1"))
add("""
<p><code>raffle-cli</code> runs a raffle in the terminal for meetup giveaways: it is meant to be <em>watchable</em>, so everybody
can see the draw is fair. You give it three files (people, prizes, and a config) and it draws the winners one prize at a time.</p>
<table class="t"><tr><th>You can…</th><th>With</th></tr>
<tr><td>Create the starter files</td><td><code>raffle-cli setup</code></td></tr>
<tr><td>Run the classic raffle (press Enter to reveal each winner)</td><td><code>raffle-cli</code></td></tr>
<tr><td>Run it as a full-screen slot machine, with mouse support</td><td><code>raffle-cli --tui</code></td></tr>
<tr><td>Watch the fireworks finale on its own</td><td><code>raffle-cli fireworks</code></td></tr>
<tr><td>Make a draw reproducible and auditable</td><td><code>--seed 7</code> (a seed is always shown in the results)</td></tr>
<tr><td>Pick the prize order, skip delays, run unattended</td><td><code>--order</code>, <code>--fast</code>, <code>--yes</code></td></tr>
<tr><td>Recover after a crash</td><td>winners are saved the moment they are revealed; run again and it resumes</td></tr>
</table>
<h3>The three files</h3>
""")
add(snip("""participants_file: participants.csv
prizes_file: prizes.csv
winners_file: winners.csv
recreate_from_winners: true""", "yaml", "config.yaml"))
add(snip("""name,lastname
Ada,Lovelace
Grace,Hopper""", "text", "participants.csv"))
add(snip("""item,qty
Mechanical keyboard,1
Python mug,2""", "text", "prizes.csv"))
add("<p>The program writes a fourth file, <code>winners.csv</code>, with columns <code>name,lastname,item</code>.</p>")

# 2 -------------------------------------------------------------------------
add(chapter(2, "The big picture", "c2"))
add("""<p>The original project was one file with everything mixed together: reading files, drawing winners, and printing. The most
important change was to <b>pull those jobs apart</b>. Programmers call this <em>separation of concerns</em>: each piece does one
thing, and you can change or test one piece without touching the others.</p>""")
add(D.architecture())
add(f"""
<table class="t"><tr><th>File</th><th>Job</th><th>Lines</th><th>Python ideas you will meet</th></tr>
<tr><td><code>raffle.py</code></td><td>The brain: who wins what. No printing, no files.</td><td>{loc('raffle.py')}</td><td>dataclasses, type hints, tuples as sort keys, <code>random.Random</code></td></tr>
<tr><td><code>files.py</code></td><td>Read, validate and write the CSV files</td><td>{loc('files.py')}</td><td><code>csv</code>, <code>pathlib</code>, custom exceptions, encodings</td></tr>
<tr><td><code>config.py</code></td><td>Load <code>config.yaml</code>, create starter files</td><td>{loc('config.py')}</td><td>Pydantic models, YAML, closures</td></tr>
<tr><td><code>cli.py</code></td><td>Front door: options, wiring, friendly errors</td><td>{loc('cli.py')}</td><td>Typer, <code>Annotated</code>, callbacks, exit codes</td></tr>
<tr><td><code>ui.py</code></td><td>The classic interface</td><td>{loc('ui.py')}</td><td>Rich panels and tables, callbacks</td></tr>
<tr><td><code>fireworks.py</code></td><td>Particle simulation + renderer</td><td>{loc('fireworks.py')}</td><td>classes, simple physics, <code>rich.live.Live</code></td></tr>
<tr><td><code>tui.py</code></td><td>Full-screen Textual app</td><td>{loc('tui.py')}</td><td>widgets, CSS, key bindings, timers, messages</td></tr>
<tr><td><code>slot.py</code></td><td>The slot machine widget</td><td>{loc('slot.py')}</td><td>custom widget, animation by timers, mouse events</td></tr>
</table>
<h3>What happens when you type <code>raffle-cli</code></h3>
<p>A command like <code>raffle-cli</code> is not magic: the packaging tool created a tiny launcher script that imports your function and calls it.</p>
""")
add(D.entrypoint())
add(snip("""[project.scripts]
raffle-cli = "raffle_cli:main_cli"

[project.optional-dependencies]
tui = ["textual>=0.86"]""", "toml", "pyproject.toml (excerpt)"))

# 3 -------------------------------------------------------------------------
add(chapter(3, "Where we started: the review", "c3"))
add("""<p>The first step was <em>not</em> writing code: it was reading the prototype and actually running it to confirm each suspicion.
Bugs you only suspect are opinions; bugs you reproduce are facts. These are the real problems found, and where each is solved.</p>
<table class="t"><tr><th>Problem found (reproduced by running it)</th><th>Fix</th><th>Chapter</th></tr>
<tr><td><code>raffle-cli setup</code> ran a whole raffle first (the main callback runs before subcommands)</td><td><code>ctx.invoked_subcommand</code> check</td><td>4</td></tr>
<tr><td>Winners were never saved; <code>recreate_from_winners</code> did nothing</td><td>append each winner; real resume logic</td><td>6</td></tr>
<tr><td>Infinite loop when prizes outnumber participants</td><td>draw in rounds: everyone wins once before anyone wins twice</td><td>5</td></tr>
<tr><td><code>UnboundLocalError</code> on a bad config</td><td>validation raises clear errors, exits with code 1</td><td>6</td></tr>
<tr><td>Empty or header-only CSVs were accepted, then crashed</td><td>validation reports every problem with line numbers</td><td>6</td></tr>
<tr><td><code>eval()</code> used to pick constants; names with <code>[</code> broke the output</td><td>no <code>eval</code>; <code>rich.markup.escape</code></td><td>4, 8</td></tr>
<tr><td><code>keyboard</code> dependency never used (needs root on Linux); <code>rich</code> used but not declared</td><td>fixed <code>pyproject.toml</code></td><td>4</td></tr>
<tr><td>One 485-line module, no tests, no CI, no LICENSE, README out of date</td><td>modules, tests, CI, docs</td><td>2, 12</td></tr>
</table>
""")
add(tip("Habit worth stealing", "Before changing code, write down what is wrong and prove it. Half of the “bugs” you suspect turn out to be fine, and the other half are usually worse than you thought."))

# 4 -------------------------------------------------------------------------
add(chapter(4, "Python foundations you meet in this code", "c4"))
add("<h2>4.1 Packaging: from a folder to a command</h2>")
add("""<p>The code lives in <code>src/raffle_cli/</code>. This is the “src layout”: because the package is not at the top level, your
tests can only import it after it is installed. That catches a classic mistake (code that works on your laptop only because you
happen to be standing in the right folder).</p>
<p><b>uv</b> is the tool that creates a virtual environment (a private set of installed packages for one project), installs what
<code>pyproject.toml</code> asks for, and records the exact versions in <code>uv.lock</code> so everybody gets the same ones.
<code>uv run pytest</code> runs a command inside that environment.</p>""")
add(decision("the Textual interface is an optional extra", """<p><b>Alternatives:</b> make Textual a normal dependency.
<b>Why not:</b> most people only want the classic interface, and Textual is a big dependency. With an extra
(<code>raffle-cli[tui]</code>) it is installed only on request. The code imports it lazily, inside the <code>if tui:</code> branch,
and prints a helpful message if it is missing. <b>Trade-off:</b> one more thing for users to remember (<code>uvx --with textual</code>).</p>"""))

add("<h2>4.2 Type hints and dataclasses</h2>")
add("""<p>A <b>dataclass</b> is a class whose main job is to hold data. Python writes <code>__init__</code>, <code>__repr__</code>
and <code>__eq__</code> for you. <code>frozen=True</code> makes instances read-only, which also makes them comparable and usable as
dictionary keys. The text after the colon (<code>str</code>, <code>int</code>) is a <em>type hint</em>: Python does not enforce it, but your editor and
readers do use it.</p>""")
add(code("raffle.py", "Participant"))
add(code("raffle.py", "Prize"))
add(code("raffle.py", "Winner"))
add(decision("small frozen dataclasses instead of dictionaries", """<p>The prototype passed <code>{"name": ..., "lastname": ...}</code>
dictionaries around. A typo like <code>row["lasname"]</code> only fails when that line runs. With a dataclass,
<code>p.lasname</code> is flagged by your editor immediately, tests can compare whole objects with <code>==</code>, and
<code>frozen</code> guarantees nobody modifies a prize by accident. <b>Alternative:</b> Pydantic models (more features, more weight; we use Pydantic only where it
earns its keep: validating <code>config.yaml</code>).</p>"""))
add("<p>The line <code>from __future__ import annotations</code> at the top of each module makes type hints lazy strings, so newer syntax like <code>list[str] | None</code> is safe on Python 3.10.</p>")

add("<h2>4.3 pathlib, csv and encodings</h2>")
add("""<p><code>pathlib.Path</code> treats file paths as objects: <code>base / "winners.csv"</code> joins paths correctly on Windows and Linux.
The <code>csv</code> module handles quoting for you (a prize called <code>Mug, large</code> stays one cell). One real-world detail:
Excel saves CSVs with an invisible <em>byte order mark</em> at the start. We open files with <code>encoding="utf-8-sig"</code>, which silently removes it,
otherwise the first column would be called <code>\\ufeffname</code> and validation would fail for a mysterious reason.</p>""")

add("<h2>4.4 Exceptions that carry information</h2>")
add(code("files.py", "DataFileError"))
add("""<p>An exception is just a class. This one stores <em>all</em> the problems found in a file, not only the first. A person fixing a
spreadsheet wants to see every wrong row at once. The command line catches it and prints a bullet list, so users never see a
traceback for their own typos.</p>""")

add("<h2>4.5 Pydantic for the config file</h2>")
add(code("config.py", "RaffleConfig"))
add("""<p>Pydantic checks the shape of data using the type hints. If someone writes <code>recreate_from_winners: maybe</code>, Pydantic
raises <code>ValidationError</code>, which <code>load_config</code> turns into one readable message. The paths are
resolved relative to the config file's folder (<code>resolved()</code>), so <code>raffle-cli -c event/config.yaml</code> works from anywhere.</p>""")

add("<h2>4.6 Typer: turning functions into commands</h2>")
add("""<p><b>Typer</b> reads a function's parameters and builds the command line from them. <code>@app.command()</code> adds a subcommand
(<code>setup</code>, <code>fireworks</code>); <code>@app.callback(invoke_without_command=True)</code> defines code that runs for
<code>raffle-cli</code> itself and holds the global options.</p>""")
add(lines_of("cli.py", "@app.callback", "ctx.obj = {", caption="src/raffle_cli/cli.py · the main callback (start)"))
add(lines_of("cli.py", "    if ctx.invoked_subcommand is not None:", "build_raffle(config or", caption="… and what it does next"))
add(decision("a guard in the callback instead of a separate “run” command", """<p>The prototype's callback ran the raffle <em>always</em>, even
for <code>raffle-cli setup</code>. The fix is two lines: if Typer says a subcommand was requested
(<code>ctx.invoked_subcommand</code>), return immediately. <b>Alternative:</b> a dedicated <code>raffle-cli run</code>; cleaner in theory but it would
break the simple, memorable <code>raffle-cli</code> from the original README. <b>Trade-off:</b> options like <code>--seed</code> live on the callback, so they go
<em>before</em> a subcommand name.</p>"""))
add("""<p><code>Annotated[bool, typer.Option("--fast", help="…")] = False</code> reads as: “a bool, shown as the option <code>--fast</code> with this help
text, default False”. Errors go through one helper, <code>fail()</code>, which prints in red and returns <code>typer.Exit(1)</code>; the non-zero exit
code lets scripts detect failure.</p>""")

add("<h2>4.7 Rich: colour without the pain</h2>")
add("""<p><b>Rich</b> prints styled text with a tiny markup language: <code>[bold green]hi[/]</code>. The catch: user data can contain square brackets.
A participant called <code>[bold]Eve</code> would be interpreted as markup. Every place that prints names uses <code>rich.markup.escape()</code>.</p>""")

# 5 -------------------------------------------------------------------------
add(chapter(5, "The raffle engine", "c5"))
add("""<p><code>raffle.py</code> is the heart. It imports no UI library, prints nothing and touches no files. That is why it is
easy to test and why <em>two</em> different interfaces (classic and Textual) can share it without duplicating a line of draw logic.</p>
<h2>5.1 The data model: a pile of prize units</h2>""")
add(code("raffle.py", "Raffle.__init__"))
add("""<p>Instead of tracking “Mug: 2 left”, the constructor expands every prize into <em>one entry per physical item</em>:
<code>["Mug", "Mug", "Pen", ...]</code>. Giving a prize away is just <code>pop(0)</code>. Counting remaining prizes is counting the list.
Fewer special cases means fewer bugs.</p>""")
add(code("raffle.py", "order_prizes"))
add(decision("never modify the caller's data", """<p>The prototype decremented <code>prize["qty"]</code> in place, so the same list could not be reused
(for a second run, a test, or a re-render). <code>order_prizes</code> returns a <em>new</em> list; <code>Prize</code> is frozen; the engine keeps its own
<code>_units</code>. A test (<code>test_prizes_are_not_mutated</code>) pins this down.</p>"""))
add("<h2>5.2 How a winner is chosen</h2>")
add(D.draw_flow())
add(code("raffle.py", "Raffle.draw"))
add("""<p>The core idea is one line: <code>keys = [(wins, holds_item) ...]</code>. Python compares tuples element by element, so <code>(0, False)</code> sorts before
<code>(1, False)</code>, which sorts before <code>(1, True)</code>. <code>min(keys)</code> gives the “most deserving” key; <code>pool</code> is everyone sharing it;
<code>rng.choice(pool)</code> is the single random step. The rules fall out of the tuple:</p>
<ul><li><b>Nobody wins twice before everybody has won once</b> (first element: fewest wins).</li>
<li><b>In later rounds, avoid giving someone an item they already hold</b> (second element), unless there is no alternative.</li></ul>""")
add("<h3>A worked example</h3><p>Three people (Ana, Ben, Cy), prizes Mug×2, Pen×2, Sticker×1. <code>high-low</code> ordering (stable) gives <code>units = [Mug, Mug, Pen, Pen, Sticker]</code>. One possible run:</p>")
add("""<table class="t"><tr><th>#</th><th>Prize</th><th>Pool (smallest key)</th><th>Winner</th><th>Wins after (Ana, Ben, Cy)</th></tr>
<tr><td>1</td><td>Mug</td><td>Ana, Ben, Cy: all (0, no)</td><td>Ben</td><td>0, 1, 0</td></tr>
<tr><td>2</td><td>Mug</td><td>Ana, Cy: still at 0 wins</td><td>Cy</td><td>0, 1, 1</td></tr>
<tr><td>3</td><td>Pen</td><td>Ana: the only one with 0 wins</td><td>Ana</td><td>1, 1, 1</td></tr>
<tr><td>4</td><td>Pen</td><td>Ben, Cy: Ana is (1, <b>holds Pen</b>) so she is behind them</td><td>Cy</td><td>1, 1, 2</td></tr>
<tr><td>5</td><td>Sticker</td><td>Ana, Ben: fewest wins (1)</td><td>Ben</td><td>1, 2, 2</td></tr></table>
<p>Five prizes, three people: nobody got a second prize until draw 4, because only then had everyone won once. That is exactly the rule “if there are more prizes than participants, people get more than one”.</p>""")
add(decision("rounds instead of “pick anyone, then swap”", """<p>The prototype picked a random person with replacement; if they already had a prize it asked “swap?”. That
made the raffle interactive in a confusing way, and it looped forever when prizes outnumbered people, because swapping never reduced the pile.
<b>Our rule:</b> draw from the people with the fewest wins. It is simple to explain to an audience, can never loop forever, and is provably fair (the tests assert that with
10 prizes and 5 people everybody gets exactly two). <b>Trade-off:</b> we dropped the swap prompt. It could come back as an option.</p>"""))
add(decision("participants are identified by position, not by name", """<p>Two people can share a name. If winners were looked up by <code>(name, lastname)</code>, they would be merged into one.
The engine keeps <code>_wins</code> and <code>_held</code> as lists indexed by participant position, so duplicates are two separate chances.
The CSV reader only prints a <em>warning</em> for duplicates.</p>"""))
add("<h2>5.3 Rebuilding state: resuming</h2>")
add(code("raffle.py", "Raffle._restore"))
add("""<p>When resuming, each saved winner is replayed: remove that prize from the pile and count the win. If the saved file contradicts the prizes file
(an item that no longer exists, a person who is gone) we raise a clear <code>ValueError</code> instead of guessing.</p>""")

# 6 -------------------------------------------------------------------------
add(chapter(6, "Files, validation and resuming", "c6"))
add("<h2>6.1 Reading a CSV defensively</h2>")
add("""<p>The rule for anything a human types: <b>assume it is wrong and explain exactly how</b>. All three readers share one helper that checks the header
and returns the rows with their line numbers.</p>""")
add(code("files.py", "_read_rows"))
add(code("files.py", "read_prizes"))
add(decision("collect every problem, and never “repair” the user's files", """<p>Two choices here.</p>
<p><b>1. Report all problems at once.</b> Failing on the first bad row means ten edit-run cycles for ten typos. The reader gathers a list and raises once.</p>
<p><b>2. No automatic fixing.</b> The prototype offered “want to set the default content?”, which would overwrite a real participant list if you pressed
<code>y</code> by reflex. Now a broken file produces an error message and is left untouched; <code>setup</code> only writes files that do not exist (or when you pass <code>--force</code>).</p>
<p>Smaller details: headers are lower-cased and stripped, cells are stripped, blank lines are ignored, and <code>qty</code> must be a whole number ≥ 1.</p>"""))
add("<h2>6.2 Saving every winner immediately</h2>")
add(code("files.py", "append_winner"))
add("""<p>If the laptop dies in the middle of a meetup, you should not lose the winners already announced. So a winner is appended to <code>winners.csv</code> at the moment they are revealed,
not at the end. Appending one row is also cheap and safe.</p>""")
add("<h2>6.3 Starting fresh or resuming</h2>")
add(D.resume_flow())
add(decision("a draw is decided first, saved when revealed", """<p><code>raffle.draw()</code> picks the winner <em>before</em> the suspense, then the interface plays the animation, and only when the name is revealed do we call
the <code>on_winner</code> callback that writes the CSV. <b>Why:</b> the UI can show anything it likes while the result is already fixed (the slot machine reels simply land on it), and the file never contains a winner the audience has not seen yet.
<b>Trade-off:</b> if you quit during a spin, that prize is not recorded and will be drawn again on resume (possibly someone else): this is the right behaviour for a live event.</p>"""))
add(decision("old results are backed up, not erased", """<p>With <code>recreate_from_winners: false</code> the program starts empty, but first copies a non-empty <code>winners.csv</code> to
<code>winners.csv.bak</code> (see <code>reset_winners</code>). Deleting results silently is the kind of mistake you only make once, in front of an audience.</p>"""))

# 7 -------------------------------------------------------------------------
add(chapter(7, "Randomness, fairness and --seed", "c7"))
add("""<p>Computers do not produce truly random numbers; <code>random.Random(seed)</code> is a <em>pseudo-random generator</em>: give it the same
seed and it produces the same sequence forever. That sounds like a flaw, but for a transparent raffle it is a feature.</p>
<ul><li>If no seed is given, one is generated with <code>secrets.randbits(32)</code> and <b>printed in the results</b>.</li>
<li>Anyone with the same files and the same <code>--seed</code> can reproduce the exact same winners.</li></ul>""")
add(decision("show the seed instead of hiding randomness", """<p><b>Alternative:</b> <code>random.SystemRandom()</code>, which draws from the operating system's entropy: unpredictable, but nobody can ever verify a result.
For giving away stickers, <em>auditability</em> beats secrecy. A 32-bit seed is not cryptographically strong and that is fine: it is a receipt, not a secret.
(If prizes had real money value you would want to commit to the seed publicly before the draw.)</p>"""))
add("<h2>7.1 A bug we found by thinking about it</h2>")
add("""<p>The first Textual version made the “blurring names” effect by calling <code>raffle.rng.choice(...)</code>. Every call consumes a number from
the generator, so the spinning animation changed <em>who won the next prize</em>: the same seed would give different winners in the classic interface and in the
Textual one, and with <code>--fast</code> (fewer animation steps) vs normal speed. The fix: the slot machine owns a separate generator.</p>""")
add(D.two_rngs())
add(tip("Rule of thumb", "Anything that must be reproducible gets its own random generator, and nothing cosmetic is allowed to touch it. A test (<code>test_tui_animation_leaves_the_seeded_draw_untouched</code>) now guards this."))

# 8 -------------------------------------------------------------------------
add(chapter(8, "The classic terminal interface", "c8"))
add("""<p><code>ui.py</code> is the first “face”. It receives a ready <code>Raffle</code> and a <code>on_winner</code> function and does presentation only.</p>""")
add(code("ui.py", "run"))
add("""<p>Notice what it does <em>not</em> know: how winners are chosen (<code>raffle.draw()</code>) or where they are saved (<code>on_winner</code>). Passing a function as an argument
like this is called a <b>callback</b>; it keeps the interface and the storage independent.</p>
<ul><li><code>delayed()</code> prints word by word with <code>time.sleep</code> for suspense; <code>--fast</code> sets the delay to zero.</li>
<li><code>pause()</code> waits for Enter, but catches <code>EOFError</code> so the program does not crash when input is piped (for example <code>echo | raffle-cli</code> in a script).</li>
<li>The same <code>Raffle</code> object is shown in tables via <code>raffle.remaining</code> and <code>raffle.winners</code>.</li></ul>""")
add(code("ui.py", "pause"))

# 9 -------------------------------------------------------------------------
add(chapter(9, "The fireworks", "c9"))
add("""<p>Fireworks are a classic first <em>simulation</em>: keep a list of moving things, update each one a little per “tick”, draw them all, repeat 20 times a second.
There are two kinds of things: <b>rockets</b> (go up, then explode) and <b>sparks</b> (fly out, slow down, fall, fade).</p>""")
add(D.fireworks_life())
add(code("fireworks.py", "Fireworks.step"))
add(code("fireworks.py", "Fireworks._explode"))
add("""<p>Three small bits of maths do the work:</p>
<ul><li><b>Angle:</b> <code>2π · i / count</code> spreads the sparks evenly around a circle. “ring” bursts all use the same speed; “burst” bursts use random speeds.</li>
<li><b>Aspect ratio:</b> terminal cells are about twice as tall as wide, so horizontal speed is multiplied by <code>ASPECT = 2</code>. Without it, circles look like tall ovals.</li>
<li><b>Drag and gravity:</b> each tick the speed is multiplied by 0.9 (air resistance) and gravity adds 0.035 to the downward speed. A spark with speed 0.75 travels about
<code>0.75 / (1 − 0.9) ≈ 7.5</code> rows before stopping, which is just right for a terminal.</li></ul>""")
add("<h2>9.1 Drawing a frame</h2>")
add("""<p><code>render()</code> makes an empty grid of characters, “plots” every rocket and spark into it (the character depends on how much life is left: <code>*</code>, <code>+</code>, <code>.</code>),
overlays the title and the winner caption, and returns one <code>rich.text.Text</code>. Note that <code>Fireworks</code> never prints anything itself.</p>""")
add(code("fireworks.py", "play"))
add(decision("one simulation, two renderers", """<p><code>Fireworks</code> only produces a <code>Text</code>. <code>play()</code> shows it with Rich's <code>Live(screen=True)</code> (the terminal's “alternate screen”, restored
afterwards, like <code>vim</code> or <code>less</code>), and the Textual interface shows the same object inside a <code>Static</code> widget refreshed by a timer.
<b>Alternatives:</b> a curses program (not portable to Windows) or a fireworks library (a dependency for 200 lines of code). <b>Trade-off:</b> we implement the physics ourselves, which is also
more fun to learn from. It does nothing when not attached to a terminal (<code>console.is_terminal</code>), so scripts and tests do not hang.</p>"""))

# 10 ------------------------------------------------------------------------
add(chapter(10, "The Textual interface", "c10"))
add("""<p><b>Textual</b> is a framework for full-screen terminal apps with ideas borrowed from web pages: <em>widgets</em> (tables, labels, your own), layout described with <em>CSS</em>,
<em>events</em> (key, mouse, resize), <em>timers</em>, and <em>messages</em> that widgets send to each other.</p>
<h2>10.1 Layout that adapts to the window</h2>""")
add(D.layouts())
add(lines_of("tui.py", "WIDE_AT", "BINDINGS = [", caption="src/raffle_cli/tui.py · constants and CSS"))
add(code("tui.py", "RaffleApp._layout"))
add("""<p>The slot machine sits in a container (<code>#machine-box</code>) that is, by default, a full-width row at the top. When the window is at least 120 columns wide, Python adds the CSS class
<code>wide</code> to <code>#main</code>, and the rule <code>#main.wide #machine-box { dock: right; ... }</code> moves it to the right edge. Python decides <em>when</em>; CSS decides <em>how it looks</em>.
Resizing is handled by <code>on_resize</code> calling <code>_layout</code> again.</p>""")
add("<h2>10.2 Key bindings and a surprising bug</h2>")
add(code("tui.py", "RaffleApp.action_draw"))
add("""<p><code>BINDINGS</code> maps keys to <em>actions</em> (methods named <code>action_...</code>). Our first version did nothing when you pressed Enter, because the focused
<code>DataTable</code> widget handles Enter itself (“select this row”) before the app sees it. The fix is <code>priority=True</code> on the binding, which lets the app win.
The test suite caught this: it presses Enter and checks that a prize was drawn.</p>""")
add(decision("the app tells widgets what to do; widgets send messages back", """<p>Notice <code>action_draw</code> calls <code>machine.pull(winner, reveal)</code> (the app commands the widget), while the widget tells the app “I was clicked” by <em>posting a message</em>
(<code>Pulled</code>). The app never reaches into the widget's internals and the widget knows nothing about raffles beyond a winner to land on. This is the same callback idea as in chapter 8.</p>"""))

# 11 ------------------------------------------------------------------------
add(chapter(11, "The slot machine", "c11"))
add("""<p>The slot machine is a <b>custom widget</b>: a class that inherits from Textual's <code>Widget</code> and implements <code>render()</code>, returning what to draw. Everything you see is text:
box-drawing characters, a few colours, and the lever made of <code>●</code>, <code>┃</code> and <code>┻</code>.</p>""")
add(D.machine_anatomy())
add("""<p>A <b>reel</b> is just a list of names (the strip) and a number (<code>pos</code>) saying which one is in the middle row. “Spinning” means increasing <code>pos</code> and re-drawing. To make the reel land on the winner,
the strip is built <em>backwards</em>: random names, with the winner placed at index <code>steps</code>, and the reel stops when <code>pos</code> reaches it. The names directly above and below the winner are
re-rolled so you never see the winner's name twice.</p>""")
add(code("slot.py", "SlotMachine._start_reels"))
add("<h2>11.1 Animation without a loop: timers</h2>")
add("""<p>You might expect a <code>while</code> loop with <code>sleep</code> inside. That would freeze the whole app, because Textual needs to keep handling keys, the mouse and drawing. Instead,
each step does a little work and then asks Textual, “call me again in N seconds” with <code>set_timer</code>. Between calls, Textual is free to do other things.</p>""")
add(code("slot.py", "SlotMachine._advance"))
add("""<p>The delay grows with the cube of the progress: <code>0.04 + 0.28 · (pos/steps)³</code>. Early on, rows fly by every 40 ms; near the end the gaps stretch to about 0.3 s, exactly like a
real machine slowing down. A cube keeps it fast for a long time and then brakes hard. The right reel has 12 more rows to travel, so it lands later: the classic “left reel stops, then the right one” suspense.</p>""")
add(D.delay_curve([18, 30]))
add(D.timeline(T1, T2, REVEAL))
add(f"""<p>Total time from pull to reveal is about <b>{REVEAL:.1f} seconds</b> (computed from the same formula the code uses). With <code>--fast</code> the delays shrink to 20 ms and the reels have 3 and 5 rows,
which makes automated tests quick.</p>""")
add("<h2>11.2 The lever and the mouse</h2>")
add(code("slot.py", "SlotMachine.pull"))
add("""<p>The lever has three states (up, halfway, pulled), each just a different row for the red ball. <code>pull()</code> schedules them one after another, then starts the reels at the bottom of the pull.
Clicking works because Textual calls a widget's <code>on_click</code> method for mouse clicks; we post a <code>Pulled</code> message, and the app (<code>on_slot_machine_pulled</code>) draws.
<b>Keyboard and mouse run exactly the same code path</b>, so there is nothing extra to test or maintain.</p>""")
add(D.message_flow())
add(decision("draw the machine as one text widget instead of many small widgets", """<p><b>Alternative:</b> build the machine from Textual containers and labels (one label per row, one container per reel). It would be easier to
style individually, but harder to animate in sync and to keep the lever aligned. Returning one <code>Text</code> from <code>render()</code> keeps every frame consistent and the whole machine is ~150 lines.
<b>Trade-off:</b> character-art needs care with widths: that is why every line is padded to the same length and the cell width is clamped to 8–12 characters (long names are cut with “…”).</p>"""))

# 12 ------------------------------------------------------------------------
add(chapter(12, "Testing", "c12"))
add(f"""<p>There are <b>{TOTAL} automated tests</b>: {counts.get('test_raffle', 0)} for the engine, {counts.get('test_files_config', 0)} for files and config, {counts.get('test_cli', 0)} for commands, fireworks and the Textual app.
Run them with <code>uv run pytest</code>. A test is a function that sets up a situation, runs the code, and <code>assert</code>s what must be true. If any assertion is false, the test fails and tells you which.</p>""")
add(D.test_layers())
add("""<p>The pyramid explains the structure: lots of fast tests at the bottom for pure logic (milliseconds, no files, no screen), fewer higher-level tests on top that exercise everything together.
Because we split the engine from the interfaces in chapter 2, the most important rules can be tested with no screen at all.</p>""")
add(lines_of("tests/test_raffle.py", "def test_more_prizes_than_participants", "== {2}", caption="tests/test_raffle.py · your rule “more prizes than people”"))
add(lines_of("tests/test_raffle.py", "def test_same_seed_same_result", "assert a == b", caption="tests/test_raffle.py · reproducibility"))
add(code("tests/test_cli.py", "test_tui_lever_click_draws_and_layout_is_responsive", "tests/test_cli.py · driving the real Textual app headlessly"))
add(decision("pytest + Textual's Pilot, without pytest-asyncio", """<p>Textual provides <code>app.run_test()</code>, which runs the app without a real terminal and gives you a <b>Pilot</b>
to press keys, click widgets and resize the “terminal”. The test body is <code>async</code>, so we wrap it with <code>asyncio.run(go())</code> inside a normal test function. <b>Alternative:</b> the
<code>pytest-asyncio</code> plugin, which is one more dependency to explain. <b>Trade-off:</b> a few <code>pause()</code> calls to wait for timers; <code>--fast</code> keeps them short.</p>"""))
add(tip("What tests cannot tell you", "All of these tests pass without anybody looking at the screen. The fonts, how the lever looks in your terminal, and whether the fireworks <em>feel</em> good still need your own eyes. Run the program for real before an event."))

# 13 ------------------------------------------------------------------------
add(chapter(13, "Technical decisions, in one table", "c13"))
add("""<p>The same decisions explained in the chapters, as a quick reference. <em>Trade-off</em> is what you give up.</p>
<table class="t dec"><tr><th>Decision</th><th>Alternative</th><th>Why</th><th>Trade-off</th></tr>
<tr><td>Engine in a pure module (<code>raffle.py</code>)</td><td>logic inside the UI code</td><td>testable, shared by both interfaces</td><td>one more file to learn</td></tr>
<tr><td>Frozen dataclasses</td><td>dicts / Pydantic</td><td>typo-proof, comparable, immutable</td><td>no automatic parsing</td></tr>
<tr><td>Prizes as a list of units</td><td>counters per prize</td><td>fewer special cases</td><td>list grows with total prizes (tiny)</td></tr>
<tr><td>Draw by minimal <code>(wins, holds_item)</code></td><td>random with swap prompt</td><td>fair, explainable, never loops</td><td>swap feature dropped</td></tr>
<tr><td>People identified by index</td><td>by name</td><td>duplicate names allowed</td><td>needs a duplicate warning</td></tr>
<tr><td>Seed shown, <code>Random(seed)</code></td><td><code>SystemRandom</code></td><td>auditable, reproducible</td><td>not secret (fine for swag)</td></tr>
<tr><td>Separate cosmetic RNG</td><td>reuse the raffle's RNG</td><td>animation can't change winners</td><td>two generators to remember</td></tr>
<tr><td>Decide first, save on reveal</td><td>save at draw time</td><td>file never spoils the reveal</td><td>quitting mid-spin redraws</td></tr>
<tr><td>Append winners one by one</td><td>write all at the end</td><td>crash-safe</td><td>many small writes (tiny)</td></tr>
<tr><td>Validate with all problems listed</td><td>fail on first error</td><td>fix everything in one go</td><td>slightly more code</td></tr>
<tr><td>Never auto-repair user files</td><td>offer defaults on error</td><td>cannot overwrite real data</td><td>user fixes by hand</td></tr>
<tr><td>Paths relative to config file</td><td>relative to the shell's folder</td><td>works from anywhere</td><td>slightly surprising for some</td></tr>
<tr><td>Pydantic only for config</td><td>manual dict checks</td><td>clear errors for little code</td><td>a dependency</td></tr>
<tr><td>Typer callback with <code>invoke_without_command</code></td><td>explicit <code>run</code> subcommand</td><td>keeps plain <code>raffle-cli</code></td><td>options precede subcommands</td></tr>
<tr><td>Textual as optional extra, lazy import</td><td>always installed</td><td>light default install</td><td>extra install step</td></tr>
<tr><td>Own fireworks simulation</td><td>curses / library</td><td>portable, tiny, educational</td><td>we maintain the physics</td></tr>
<tr><td>One simulation, two renderers</td><td>two implementations</td><td>no duplicate logic</td><td>renderer returns <code>Text</code> only</td></tr>
<tr><td>Rich <code>Live(screen=True)</code></td><td>print frames and clear</td><td>flicker-free, terminal restored</td><td>needs a real terminal</td></tr>
<tr><td>Priority binding for Enter</td><td>make tables unfocusable</td><td>one line, key always works</td><td>shadows widget Enter</td></tr>
<tr><td>CSS class flips layout at 120 columns</td><td>two separate screens</td><td>one layout, tiny code</td><td>fixed breakpoint</td></tr>
<tr><td>Slot machine = one custom widget</td><td>many small widgets</td><td>frames stay consistent</td><td>care with text widths</td></tr>
<tr><td>Plain text names, no ASCII-art font</td><td>big figlet letters</td><td>long names and accents break art</td><td>smaller names</td></tr>
<tr><td>Timers instead of <code>sleep</code> loops</td><td>blocking animation</td><td>UI stays responsive</td><td>callbacks are harder to read</td></tr>
<tr><td><code>asyncio.run</code> in tests</td><td>pytest-asyncio</td><td>no extra plugin</td><td>a little boilerplate</td></tr>
<tr><td>Python ≥ 3.10, uv + lockfile</td><td>newer only / pip freeze</td><td>wide support, reproducible installs</td><td>older syntax limits</td></tr>
</table>""")

# 14 ------------------------------------------------------------------------
add(chapter(14, "Things that went wrong (and what they taught)", "c14"))
add("""<p>Real projects do not go in a straight line. These are the actual detours, because debugging stories teach more than polished code.</p>
<table class="t"><tr><th>What happened</th><th>Cause</th><th>Lesson</th></tr>
<tr><td>Pressing Enter in the Textual app did nothing</td><td>The focused table handled Enter first</td><td>Events go to the focused widget first; use <code>priority=True</code>. Tests that simulate keys find this in seconds.</td></tr>
<tr><td>The “install the tui extra” message was cut to <code>pip install 'raffle-cli'</code></td><td>Rich read <code>[tui]</code> as markup and swallowed it</td><td>Escape anything user-visible that might contain brackets (<code>rich.markup.escape</code>).</td></tr>
<tr><td><code>uvx ... --tui</code> failed on a fresh machine</td><td><code>uvx</code> does not install optional extras unless asked</td><td>Document the exact command (<code>--with textual</code>) and make the error say it.</td></tr>
<tr><td>Same seed, different winners in the two interfaces</td><td>Animation consumed numbers from the raffle's generator</td><td>Separate randomness that must be reproducible from randomness that is decoration.</td></tr>
<tr><td>Big ASCII-art names looked impressive then were dropped</td><td>Long names, accents and non-Latin letters either overflow or render blank</td><td>Features that need width handling for every possible input are expensive. Simpler plain text wins in a terminal.</td></tr>
<tr><td>The first idea for the spin showed one name at a time</td><td>We wanted “a literal spin”</td><td>Moving to reels (a list and a pointer) made the effect more convincing <em>and</em> simpler than the old code.</td></tr>
</table>""")

# 15 ------------------------------------------------------------------------
add(chapter(15, "Exercises", "c15"))
add("""<p>This is where you take the code back. They are ordered from easiest to hardest. For each, write a test first (or at least run the program and look).</p>
<table class="t"><tr><th>#</th><th>Exercise</th><th>Where to look</th><th>Hint</th></tr>
<tr><td>1</td><td>Change the fireworks colours and make them last longer</td><td><code>fireworks.py</code> <code>PALETTE</code>, <code>ui.py</code> seconds</td><td>Run <code>raffle-cli fireworks --seconds 20</code> as you tweak.</td></tr>
<tr><td>2</td><td>Add a new <code>--order</code> value, <code>alpha</code> (prizes A to Z)</td><td><code>raffle.py</code> <code>ORDERS</code>, <code>order_prizes</code></td><td>One <code>elif</code> and a test. <code>sort(key=lambda p: p.item.lower())</code>.</td></tr>
<tr><td>3</td><td>Print a sentence at the end: “N winners, M prizes”</td><td><code>ui.show_results</code></td><td>You have <code>raffle.winners</code> and <code>raffle.remaining</code>.</td></tr>
<tr><td>4</td><td>Add an optional <code>email</code> column to participants that is ignored by the draw</td><td><code>files.py</code>, <code>raffle.py</code></td><td>The header check is strict: decide how to allow extra columns and test both cases.</td></tr>
<tr><td>5</td><td>Add a <code>--exclude "Name Lastname"</code> option for people who are present but not eligible (organisers)</td><td><code>cli.py</code> <code>build_raffle</code></td><td>Filter the participant list before creating the <code>Raffle</code>.</td></tr>
<tr><td>6</td><td>Export a Markdown results file next to <code>winners.csv</code></td><td>new function in <code>files.py</code></td><td>Call it after the last prize in <code>main</code>.</td></tr>
<tr><td>7</td><td>Add a third reel that shows the prize in the slot machine</td><td><code>slot.py</code></td><td>The reel list is built for 2; generalise it. Careful with total width and the CSS dock width (52).</td></tr>
<tr><td>8</td><td>Add a <code>weight</code> column so some people get more chances</td><td><code>raffle.py</code> <code>draw</code></td><td>Think about fairness first: how does it interact with “everyone wins once before anyone wins twice”? Write that rule down before coding.</td></tr>
</table>""")

# 16 ------------------------------------------------------------------------
add(chapter(16, "Glossary and how to run everything", "c16"))
add("""<h2>Run it</h2>
<p><b>Without installing (macOS / Linux):</b></p>""")
add(snip("""R="git+https://github.com/andoresuperesu/raffle-cli"
uvx --from $R raffle-cli setup
uvx --from $R --with textual raffle-cli --tui""", "bash", "bash / zsh"))
add("<p><b>PowerShell:</b></p>")
add(snip("""$R = "git+https://github.com/andoresuperesu/raffle-cli"
uvx --from $R raffle-cli setup
uvx --from $R --with textual raffle-cli --tui""", "powershell", "PowerShell"))
add("<p><b>From a clone, for development:</b></p>")
add(snip("""git clone https://github.com/andoresuperesu/raffle-cli
cd raffle-cli
uv sync
uv run pytest
uv run raffle-cli --config examples/config.yaml --tui""", "bash", "any shell"))
add("""<h2>Known limits</h2>
<ul><li>Developed and tested on Linux. On Windows use Windows Terminal; the box-drawing characters and mouse input are unverified there.</li>
<li>The tests prove behaviour, not looks: check the slot machine and fireworks visually before an event.</li>
<li>The 32-bit seed makes draws reproducible, not secret (see chapter 7).</li></ul>
<h2>Glossary</h2>
<table class="t gloss">
<tr><td><b>Callback</b></td><td>A function you hand to other code so it can call you back later (<code>on_winner</code>, <code>reveal</code>).</td></tr>
<tr><td><b>CLI</b></td><td>Command-line interface: a program you control by typing a command.</td></tr>
<tr><td><b>Dataclass</b></td><td>A class meant to hold data; Python generates the boring methods.</td></tr>
<tr><td><b>Entry point</b></td><td>The function a command like <code>raffle-cli</code> calls; declared in <code>pyproject.toml</code>.</td></tr>
<tr><td><b>Extra</b></td><td>Optional dependencies installed with <code>pkg[name]</code>.</td></tr>
<tr><td><b>Frozen</b></td><td>An object that cannot be modified after creation.</td></tr>
<tr><td><b>Pilot</b></td><td>Textual's test driver that presses keys and clicks in a headless app.</td></tr>
<tr><td><b>Pseudo-random</b></td><td>Looks random but is computed from a seed, so it can be repeated.</td></tr>
<tr><td><b>Pure function / module</b></td><td>Only computes from its inputs: no printing, no files, no clock.</td></tr>
<tr><td><b>Seed</b></td><td>The starting number of a pseudo-random generator.</td></tr>
<tr><td><b>Separation of concerns</b></td><td>Splitting a program so each part has a single job.</td></tr>
<tr><td><b>Tick</b></td><td>One step of a simulation or animation.</td></tr>
<tr><td><b>TUI</b></td><td>Text user interface: a full-screen app drawn with characters.</td></tr>
<tr><td><b>Virtual environment</b></td><td>A private folder of installed packages for one project (<code>.venv</code>).</td></tr>
<tr><td><b>Widget</b></td><td>A reusable piece of a user interface (a table, a label, the slot machine).</td></tr>
</table>
<h2>Where to read more</h2>
<ul><li>Typer: typer.tiangolo.com &nbsp;·&nbsp; Rich: rich.readthedocs.io &nbsp;·&nbsp; Textual: textual.textualize.io</li>
<li>Pydantic: docs.pydantic.dev &nbsp;·&nbsp; pytest: docs.pytest.org &nbsp;·&nbsp; uv: docs.astral.sh/uv</li>
<li>The Python tutorial on classes, exceptions and modules: docs.python.org/3/tutorial</li></ul>
""")

CSS = (
    HtmlFormatter(style="friendly").get_style_defs(".code pre")
    + """
@page { size: A4; margin: 18mm 16mm 20mm 16mm; }
* { box-sizing: border-box; }
body { font-family: Inter, Helvetica, Arial, sans-serif; font-size: 10.4pt; line-height: 1.5; color: #1f2937; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 0.88em; background: #f3f4f6; padding: 0.5px 4px; border-radius: 3px; color: #111827; }
h1 { font-size: 21pt; margin: 0 0 10px; padding-top: 4px; border-bottom: 3px solid #2563eb; padding-bottom: 6px; page-break-before: always; line-height: 1.2; }
h1 .num { display: inline-block; background: #2563eb; color: #fff; border-radius: 6px; padding: 0 10px; margin-right: 10px; font-size: 18pt; }
h2 { font-size: 14pt; margin: 20px 0 6px; color: #1e3a8a; break-after: avoid; }
h3 { font-size: 11.5pt; margin: 14px 0 4px; color: #374151; break-after: avoid; }
p { margin: 6px 0; } ul, ol { margin: 6px 0 6px 20px; padding: 0; } li { margin: 3px 0; }
.cover { height: 235mm; padding-top: 28mm; page-break-after: always; }
.cover .kicker { color: #2563eb; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; font-size: 10pt; }
.cover h1.title { border: 0; font-size: 36pt; page-break-before: avoid; margin: 8px 0 8px; line-height: 1.1; }
.cover .subtitle { font-size: 15pt; color: #4b5563; margin: 0 0 24px; }
.coverbox { background: #eff6ff; border-left: 5px solid #2563eb; padding: 10px 16px; margin: 18px 0; border-radius: 4px; font-size: 10.5pt; }
.how { font-size: 11pt; }
.toc { page-break-after: always; } .toc h2 { margin-top: 0; font-size: 18pt; }
.toc ol { list-style: none; margin: 0; } .toc li { padding: 5px 0; border-bottom: 1px solid #e5e7eb; font-size: 11.5pt; }
.toc a { color: #1f2937; text-decoration: none; } .toc span { display: inline-block; width: 28px; color: #2563eb; font-weight: 700; }
table.t { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9.2pt; }
table.t th { background: #1e3a8a; color: #fff; text-align: left; padding: 5px 8px; }
table.t td { border-bottom: 1px solid #e5e7eb; padding: 5px 8px; vertical-align: top; }
table.t tr:nth-child(even) td { background: #f9fafb; } table.t tr { break-inside: avoid; }
table.dec { font-size: 7.8pt; } table.dec td, table.dec th { padding: 3px 6px; } table.dec td:first-child { font-weight: 600; }
table.gloss td:first-child { width: 28%; white-space: nowrap; }
.code { margin: 10px 0; border: 1px solid #d1d5db; border-radius: 6px; overflow: hidden; break-inside: avoid; }
.code.long { break-inside: auto; }
.code .cap { background: #e5e7eb; font-family: "DejaVu Sans Mono", monospace; font-size: 8pt; padding: 3px 10px; color: #374151; }
.code pre { margin: 0; padding: 8px 10px; background: #fbfbfb; font-family: "DejaVu Sans Mono", monospace; font-size: 7.6pt; line-height: 1.38; white-space: pre-wrap; word-break: break-word; }
.callout { margin: 12px 0; padding: 8px 14px; border-radius: 6px; border-left: 5px solid; break-inside: avoid; font-size: 9.8pt; }
.callout .ct { font-weight: 700; margin-bottom: 2px; }
.callout.decision { background: #eef2ff; border-color: #4f46e5; } .callout.decision .ct { color: #3730a3; }
.callout.tip { background: #ecfdf5; border-color: #10b981; } .callout.tip .ct { color: #047857; }
.callout.warn { background: #fffbeb; border-color: #f59e0b; } .callout.warn .ct { color: #b45309; }
figure.diagram { margin: 12px 0; text-align: center; break-inside: avoid; }
figure.diagram svg { width: 100%; height: auto; max-height: 215mm; }
.bx { stroke-width: 1.6; } .bx.plain { fill: #f9fafb; stroke: #9ca3af; } .bx.io { fill: #eef2ff; stroke: #6366f1; }
.bx.door { fill: #fff7ed; stroke: #f97316; } .bx.brain { fill: #e0f2fe; stroke: #0284c7; stroke-width: 2.6; }
.bx.face { fill: #ecfdf5; stroke: #10b981; } .bx.fx { fill: #fdf2f8; stroke: #ec4899; } .bx.disk { fill: #f3f4f6; stroke: #6b7280; stroke-dasharray: 5 3; }
.bt { font-size: 13px; font-weight: 700; fill: #111827; } .bs { font-size: 10.5px; fill: #374151; }
.lb { font-size: 11px; fill: #374151; } .lbd { font-size: 11px; fill: #6b7280; } .lbw { font-size: 12px; fill: #fff; font-weight: 700; }
.ar { fill: none; stroke: #4b5563; stroke-width: 2; } .ar.dash { stroke-dasharray: 6 5; } .ar.blue { stroke: #2563eb; }
"""
)

html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>How raffle-cli was built</title><style>{CSS}</style></head>
<body>{''.join(P)}</body></html>"""
OUT.write_text(html, encoding="utf-8")
print("wrote", OUT, len(html) // 1024, "KB; timings", round(T1, 2), round(T2, 2), round(REVEAL, 2))
