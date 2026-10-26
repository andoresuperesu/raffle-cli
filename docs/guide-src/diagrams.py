"""Tiny SVG helpers + every diagram used in the guide."""

from __future__ import annotations

import math
from html import escape

DEFS = """<defs>
<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#4b5563"/></marker>
<marker id="ahb" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#2563eb"/></marker>
</defs>"""


def svg(w: int, h: int, body: str, label: str = "") -> str:
    return (
        f'<figure class="diagram"><svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="{escape(label)}" font-family="Inter, Helvetica, Arial, sans-serif">{DEFS}{body}</svg></figure>'
    )


def box(x, y, w, h, title, sub="", kind="plain", mono=False) -> str:
    out = [f'<rect class="bx {kind}" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>']
    lines = sub.split("\n") if sub else []
    ty = y + h / 2 - (len(lines) * 7) + (4 if not lines else 0)
    if lines:
        ty = y + h / 2 - (len(lines) * 6.5) - 1
    fam = ' font-family="DejaVu Sans Mono, monospace"' if mono else ""
    out.append(f'<text x="{x + w / 2}" y="{ty + 4}" text-anchor="middle" class="bt"{fam}>{escape(title)}</text>')
    for i, line in enumerate(lines):
        out.append(f'<text x="{x + w / 2}" y="{ty + 20 + i * 13}" text-anchor="middle" class="bs">{escape(line)}</text>')
    return "".join(out)


def arrow(pts, dashed=False, blue=False, label=None, lx=None, ly=None, both=False) -> str:
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    cls = "ar" + (" dash" if dashed else "") + (" blue" if blue else "")
    mk = "ahb" if blue else "ah"
    start = f' marker-start="url(#{mk})"' if both else ""
    out = f'<path class="{cls}" d="{d}" marker-end="url(#{mk})"{start}/>'
    if label:
        mx = lx if lx is not None else (pts[0][0] + pts[-1][0]) / 2
        my = ly if ly is not None else (pts[0][1] + pts[-1][1]) / 2 - 4
        out += f'<text x="{mx}" y="{my}" text-anchor="middle" class="lb">{escape(label)}</text>'
    return out


def text(x, y, s, cls="lb", anchor="middle") -> str:
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="{cls}">{escape(s)}</text>'


# ---------------------------------------------------------------------------
def architecture() -> str:
    b = []
    b.append(box(250, 12, 270, 54, "cli.py", "front door: options, wiring, error messages", "door"))
    b.append(box(20, 112, 160, 76, "Files on disk", "config.yaml\nparticipants.csv  prizes.csv\nwinners.csv", "disk"))
    b.append(box(250, 112, 125, 76, "config.py", "load + validate\nconfig.yaml, setup", "io"))
    b.append(box(395, 112, 125, 76, "files.py", "read / validate / write\nthe CSV files", "io"))
    b.append(box(250, 222, 270, 76, "raffle.py  (the brain)", "who wins what, in which order.\nNo printing, no files: pure logic.", "brain"))
    b.append(box(40, 350, 150, 70, "ui.py", "classic terminal\n(Rich, press Enter)", "face"))
    b.append(box(235, 350, 150, 70, "tui.py + slot.py", "full screen (Textual)\nslot machine + lever", "face"))
    b.append(box(430, 350, 150, 70, "fireworks.py", "particle simulation\nshared by both faces", "fx"))
    b.append(arrow([(312, 66), (312, 112)], label="1 read", lx=335, ly=92))
    b.append(arrow([(458, 66), (458, 112)]))
    b.append(arrow([(180, 150), (250, 150)], both=True))
    b.append(arrow([(312, 188), (312, 222)], label="2 data", lx=340, ly=208))
    b.append(arrow([(458, 188), (458, 222)]))
    b.append(arrow([(330, 298), (130, 350)], blue=True, label="3 draw()", lx=205, ly=318))
    b.append(arrow([(385, 298), (310, 350)], blue=True))
    b.append(arrow([(385, 385), (430, 385)], dashed=True))
    b.append(arrow([(115, 420), (115, 440), (505, 440), (505, 420)], dashed=True))
    b.append(arrow([(250, 40), (20, 40), (20, 300), (40, 380)], dashed=True))
    b.append(text(150, 30, "picks the interface", "lb", "middle"))
    b.append(arrow([(520, 40), (640, 40), (640, 385), (580, 385)], dashed=True, label="saves each winner", lx=618, ly=205))
    b.append(text(400, 462, "Solid arrows: data. Blue arrows: the draw. Dashed: control / callbacks.", "lb"))
    return svg(700, 474, "".join(b), "Architecture of raffle-cli")


def entrypoint() -> str:
    b = []
    xs = [10, 128, 246, 364, 482, 600]
    names = [
        ("You type", "raffle-cli --tui", "plain"),
        ("Launcher", "created by uv/pip from\n[project.scripts]", "io"),
        ("main_cli()", "in __init__.py\ncalls app()", "door"),
        ("Typer parses", "options, picks the\ncommand to run", "door"),
        ("main() callback", "validates, builds the\nRaffle", "brain"),
        ("A face runs", "ui.run() or\nRaffleApp.run()", "face"),
    ]
    for x, (t, s, k) in zip(xs, names):
        b.append(box(x, 20, 108, 78, t, s, k))
    for a, c in zip(xs, xs[1:]):
        b.append(arrow([(a + 108, 59), (c, 59)]))
    b.append(text(355, 128, 'pyproject.toml:   [project.scripts]   raffle-cli = "raffle_cli:main_cli"', "lb"))
    return svg(720, 140, "".join(b), "What happens when you type raffle-cli")


def draw_flow() -> str:
    b = []
    b.append(box(190, 10, 240, 44, "units = [\"Mug\",\"Mug\",\"Pen\", ...]", "one entry per prize still to give away", "plain"))
    b.append(box(190, 84, 240, 44, "item = units.pop(0)", "take the next prize", "io"))
    b.append(box(190, 158, 240, 56, "key = (wins, already_holds_item)", "for every participant", "brain"))
    b.append(box(190, 244, 240, 44, "pool = people with the smallest key", "fewest prizes first, and no duplicates", "brain"))
    b.append(box(190, 318, 240, 44, "winner = rng.choice(pool)", "the only random step", "fx"))
    b.append(box(190, 392, 240, 44, "record it", "wins += 1, remember the item", "io"))
    b.append(box(190, 466, 240, 44, "append to winners.csv", "saved the moment it is revealed", "door"))
    for y_from, y_to in ((54, 84), (128, 158), (214, 244), (288, 318), (362, 392), (436, 466)):
        b.append(arrow([(310, y_from), (310, y_to)]))
    b.append(arrow([(430, 488), (500, 488), (500, 106), (430, 106)], dashed=True))
    b.append(text(508, 300, "more prizes?", "lb", "start"))
    b.append(text(130, 106, "repeat until", "lb"))
    b.append(text(130, 120, "units is empty", "lb"))
    return svg(620, 520, "".join(b), "How one winner is drawn")


def resume_flow() -> str:
    b = []
    b.append(box(220, 8, 200, 40, "recreate_from_winners ?", "", "brain"))
    b.append(box(20, 100, 220, 56, "true  (default)", "read winners.csv\nrebuild the state", "io"))
    b.append(box(400, 100, 220, 56, "false", "copy winners.csv to\nwinners.csv.bak, start empty", "io"))
    b.append(box(20, 200, 220, 56, "Raffle(previous_winners=...)", "removes those prizes from the pile\nand counts the wins", "brain"))
    b.append(box(400, 200, 220, 56, "Raffle(previous_winners=[])", "everything is up for grabs", "brain"))
    b.append(box(120, 300, 400, 56, "Nothing left?  say so and explain how to start over", "otherwise carry on exactly where it stopped", "door"))
    b.append(arrow([(260, 48), (130, 100)], label="true", lx=180, ly=70))
    b.append(arrow([(380, 48), (510, 100)], label="false", lx=470, ly=70))
    b.append(arrow([(130, 156), (130, 200)]))
    b.append(arrow([(510, 156), (510, 200)]))
    b.append(arrow([(130, 256), (200, 300)]))
    b.append(arrow([(510, 256), (440, 300)]))
    return svg(640, 370, "".join(b), "Resuming from winners.csv")


def two_rngs() -> str:
    b = []
    b.append(box(20, 20, 250, 70, "raffle.rng = Random(seed)", "decides every winner\nsame seed + same files = same result", "brain"))
    b.append(box(350, 20, 250, 70, "SlotMachine.rng = Random()", "only picks the names that blur by\nwhile the reels spin", "fx"))
    b.append(box(20, 150, 250, 50, "winners (saved, reproducible)", "", "door"))
    b.append(box(350, 150, 250, 50, "pixels on the screen (cosmetic)", "", "plain"))
    b.append(arrow([(145, 90), (145, 150)]))
    b.append(arrow([(475, 90), (475, 150)]))
    b.append(f'<path d="M310,15 L310,205" stroke="#dc2626" stroke-width="2.5" stroke-dasharray="6 5"/>')
    b.append(text(310, 228, "never shared: animation can't change who wins", "lb"))
    return svg(620, 240, "".join(b), "Two random generators")


def fireworks_life() -> str:
    b = []
    b.append('<line x1="20" y1="268" x2="420" y2="268" stroke="#9ca3af"/>')
    b.append(text(220, 285, "bottom of the terminal (y = height - 1)", "lb"))
    b.append('<line x1="110" y1="268" x2="110" y2="110" stroke="#f59e0b" stroke-width="3" stroke-dasharray="3 4"/>')
    b.append('<rect x="106" y="108" width="8" height="18" fill="#374151"/>')
    b.append(text(110, 96, "Rocket", "bt"))
    b.append(text(110, 66, "explodes at its apex", "lb"))
    b.append(text(60, 200, "moves up:", "lb"))
    b.append(text(60, 214, "vy = -0.9 .. -1.4", "lb"))
    b.append(text(60, 228, "short trail behind", "lb"))
    cx, cy, r = 310, 105, 55
    for i in range(16):
        a_ = 2 * math.pi * i / 16
        x2, y2 = cx + math.cos(a_) * r * 1.4, cy + math.sin(a_) * r * 0.9
        b.append(f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#2563eb" stroke-width="1" opacity="0.35"/>')
        b.append(f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="3" fill="#ef4444"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="5" fill="#f59e0b"/>')
    b.append(text(310, 24, "Sparks fly out in a circle", "bt"))
    b.append(text(310, 40, "vx = cos(angle) * speed * 2", "lb"))
    b.append(text(310, 54, "vy = sin(angle) * speed", "lb"))
    b.append(arrow([(118, 112), (236, 108)], dashed=True, blue=True))
    b.append(arrow([(310, 182), (310, 228)], blue=True))
    b.append(text(322, 210, "gravity pulls them down", "lb", "start"))
    b.append(text(310, 244, "every tick:   vx = vx * 0.9", "lb"))
    b.append(text(310, 258, "vy = vy * 0.9 + 0.035", "lb"))
    b.append(text(540, 100, "A spark's life", "bt"))
    for i, (ch, lab) in enumerate([("*", "bright, just born"), ("+", "medium"), (".", "dim, about to vanish")]):
        b.append(text(490, 130 + i * 28, ch, "bt", "middle"))
        b.append(text(510, 134 + i * 28, lab, "lb", "start"))
    b.append(text(540, 232, "life counts down each tick;", "lb"))
    b.append(text(540, 246, "at 0 the spark is removed", "lb"))
    return svg(660, 300, "".join(b), "Life of a firework")


def layouts() -> str:
    b = []
    b.append(text(210, 18, "Wide terminal (120+ columns)", "bt"))
    b.append('<rect class="bx plain" x="20" y="28" width="380" height="230" rx="6"/>')
    b.append(box(30, 36, 360, 22, "Header", "", "io"))
    b.append(box(30, 64, 215, 54, "stage text", "what is happening now", "door"))
    b.append(box(30, 124, 105, 100, "Prizes left", "table", "plain"))
    b.append(box(140, 124, 105, 100, "Winners", "table", "plain"))
    b.append(box(252, 64, 138, 160, "Slot machine", "on the right\nclick to pull", "fx"))
    b.append(box(30, 230, 360, 20, "Footer (key hints)", "", "io"))
    b.append(text(580, 18, "Narrow terminal", "bt"))
    b.append('<rect class="bx plain" x="470" y="28" width="220" height="230" rx="6"/>')
    b.append(box(478, 36, 204, 20, "Header", "", "io"))
    b.append(box(478, 62, 204, 66, "Slot machine", "on top, centered", "fx"))
    b.append(box(478, 134, 204, 36, "stage text", "", "door"))
    b.append(box(478, 176, 100, 50, "Prizes", "", "plain"))
    b.append(box(582, 176, 100, 50, "Winners", "", "plain"))
    b.append(box(478, 232, 204, 20, "Footer", "", "io"))
    b.append(text(380, 285, "One CSS class on #main (\"wide\") flips between the two layouts when the window resizes.", "lb"))
    return svg(720, 300, "".join(b), "Responsive layout")


def machine_anatomy() -> str:
    b = []
    b.append('<rect x="60" y="20" width="250" height="150" rx="10" fill="#fef3c7" stroke="#d97706" stroke-width="3"/>')
    b.append(text(185, 46, "★  RAFFLE-CLI  ★", "bt"))
    for i, (x, t) in enumerate([(75, "Reel 1: name"), (190, "Reel 2: lastname")]):
        b.append(f'<rect x="{x}" y="62" width="105" height="92" rx="4" fill="#fff" stroke="#6b7280"/>')
        b.append(text(x + 52, 82, "Margaret", "lbd"))
        b.append(f'<rect x="{x + 2}" y="92" width="101" height="24" fill="#374151"/>')
        b.append(text(x + 52, 109, "▶  Linus  ◀" if i == 0 else "▶ Torvalds ◀", "lbw"))
        b.append(text(x + 52, 140, "Ada", "lbd"))
        b.append(text(x + 52, 176 + 14, t, "lb"))
    # lever
    b.append('<line x1="340" y1="150" x2="340" y2="50" stroke="#6b7280" stroke-width="5"/>')
    b.append('<circle cx="340" cy="46" r="11" fill="#dc2626"/>')
    b.append('<rect x="326" y="146" width="28" height="10" rx="3" fill="#6b7280"/>')
    b.append(text(340, 30, "lever", "bt"))
    b.append(arrow([(340, 72), (340, 118)], blue=True, label="pull", lx=372, ly=100))
    b.append(text(450, 70, "window = 3 rows:", "lb", "start"))
    b.append(text(450, 86, "  above (dim)", "lb", "start"))
    b.append(text(450, 102, "  middle (bright, ▶ ◀)", "lb", "start"))
    b.append(text(450, 118, "  below (dim)", "lb", "start"))
    b.append(text(450, 146, "strip = list of names; the", "lb", "start"))
    b.append(text(450, 160, "reel just moves a pointer", "lb", "start"))
    b.append(text(450, 174, "(pos) down that list.", "lb", "start"))
    return svg(640, 215, "".join(b), "Anatomy of the slot machine")


def delay_curve(steps_list) -> str:
    W, H, L, B = 560, 260, 60, 40
    ymax = 0.34
    b = []
    b.append(f'<line x1="{L}" y1="{H - B}" x2="{W - 10}" y2="{H - B}" stroke="#6b7280"/><line x1="{L}" y1="10" x2="{L}" y2="{H - B}" stroke="#6b7280"/>')
    for yv in (0.1, 0.2, 0.3):
        y = H - B - yv / ymax * (H - B - 10)
        b.append(f'<line x1="{L}" y1="{y:.1f}" x2="{W - 10}" y2="{y:.1f}" stroke="#e5e7eb"/>')
        b.append(text(L - 8, y + 4, f"{yv:.1f}s", "lb", "end"))
    b.append(text((L + W) / 2, H - 8, "progress through the spin  (0% = start, 100% = landing)", "lb"))
    steps = steps_list[0]
    pts = []
    for p in range(2, steps):
        x = L + (p / steps) * (W - L - 20)
        y = H - B - (0.04 + 0.28 * (p / steps) ** 3) / ymax * (H - B - 10)
        pts.append(f"{x:.1f},{y:.1f}")
    b.append(f'<polyline fill="none" stroke="#2563eb" stroke-width="2.4" points="{" ".join(pts)}"/>')
    b.append(text(L + 12, 30, "pause between two rows", "lb", "start"))
    b.append(text(L + 12, 60, "both reels follow this same curve;", "lb", "start"))
    b.append(text(L + 12, 74, "the lastname reel just has more rows to go through", "lb", "start"))
    return svg(W, H, "".join(b), "Deceleration curve")


def timeline(t1, t2, reveal) -> str:
    W, L = 640, 110
    total = reveal + 0.2
    sx = lambda t: L + t / total * (W - L - 20)
    b = []
    rows = [("lever", 0.0, 0.36, "#f59e0b"), ("reel 1 (name)", 0.18, t1, "#2563eb"), ("reel 2 (lastname)", 0.18, t2, "#dc2626"), ("pause", t2, reveal, "#9ca3af")]
    for i, (name, a, c, col) in enumerate(rows):
        y = 20 + i * 36
        b.append(text(L - 8, y + 16, name, "lb", "end"))
        b.append(f'<rect x="{sx(a):.1f}" y="{y}" width="{sx(c) - sx(a):.1f}" height="22" rx="4" fill="{col}" opacity="0.85"/>')
    y0 = 20 + 4 * 36
    b.append(f'<line x1="{L}" y1="{y0}" x2="{W - 10}" y2="{y0}" stroke="#6b7280"/>')
    for t in range(0, int(total) + 1):
        b.append(f'<line x1="{sx(t):.1f}" y1="{y0}" x2="{sx(t):.1f}" y2="{y0 + 5}" stroke="#6b7280"/>' + text(sx(t), y0 + 18, f"{t}s", "lb"))
    b.append(f'<line x1="{sx(reveal):.1f}" y1="10" x2="{sx(reveal):.1f}" y2="{y0}" stroke="#16a34a" stroke-width="2" stroke-dasharray="5 4"/>')
    b.append(text(sx(reveal) - 4, 14, "reveal: save winner, update tables", "lb", "end"))
    b.append(text(sx(0.18) + 2, y0 - 6, "reels start when the lever is down (0.18s)", "lb", "start"))
    return svg(W, y0 + 30, "".join(b), "Timeline of one pull")


def message_flow() -> str:
    b = []
    lanes = [("User", 20), ("SlotMachine", 170), ("RaffleApp", 330), ("Raffle + disk", 490)]
    for name, x in lanes:
        b.append(box(x, 8, 130, 30, name, "", "io"))
        b.append(f'<line x1="{x + 65}" y1="38" x2="{x + 65}" y2="330" stroke="#d1d5db" stroke-dasharray="4 4"/>')
    steps = [
        (85, 235, 66, "1  click (or Enter)"),
        (235, 395, 102, "2  Pulled message"),
        (395, 555, 138, "3  raffle.draw()  (winner decided)"),
        (395, 235, 174, "4  machine.pull(winner, reveal)"),
        (235, 235, 210, ""),
        (235, 395, 246, "5  timers finish: reveal()"),
        (395, 555, 282, "6  append_winner() to CSV"),
    ]
    for x1, x2, y, lab in steps:
        if x1 == x2:
            b.append(f'<path d="M235,{y - 14} C285,{y - 14} 285,{y + 4} 240,{y + 4}" class="ar" fill="none" marker-end="url(#ah)"/>')
            b.append(text(300, y - 4, "lever, reels, timers", "lb", "start"))
            continue
        b.append(arrow([(x1, y), (x2, y)], blue=(x2 > x1)))
        b.append(text((x1 + x2) / 2, y - 6, lab, "lb"))
    return svg(640, 345, "".join(b), "Click to winner")


def test_layers() -> str:
    b = []
    layers = [
        ("TUI tests (Textual Pilot, headless)", "click the machine, resize, full draw", 140, "fx", 10),
        ("CLI tests (Typer CliRunner)", "whole commands, files in a temp folder", 110, "door", 80),
        ("File + config tests", "validation messages, setup, resume", 80, "io", 150),
        ("Pure logic tests", "fairness, rounds, seeds, resuming", 50, "brain", 220),
    ]
    # widths grow downward: trapezoid-ish stacked boxes
    for i, (t, s, _, k, _) in enumerate(layers):
        w = 300 + i * 90
        x = 20 + (480 - w) / 2 + 80
        b.append(box(x, 12 + i * 66, w, 56, t, s, k))
    b.append(arrow([(655, 220), (655, 30)], blue=True))
    b.append(text(667, 125, "slower,", "lb", "start"))
    b.append(text(667, 139, "more", "lb", "start"))
    b.append(text(667, 153, "fragile", "lb", "start"))
    b.append(text(60, 282, "bottom: fast and many", "lb", "start"))
    return svg(720, 295, "".join(b), "Test layers")
