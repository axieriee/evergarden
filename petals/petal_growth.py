#!/usr/bin/env python3
"""
🌸 Petal's Growth Engine — Recursive Branching
Petal grows procedurally like cbonsai, but she's alive.
Her shape is unique every run. Her stage changes her rules.

Run with: python3 petal_grow.py
Press any key to regrow. Press 'q' to quit.
"""

import curses
import random
import time
import math
from dataclasses import dataclass, field
from typing import Optional

# ─────────────────────────────────────────────
# COLOR SETUP — same Evergarden palette 🌿
# ─────────────────────────────────────────────

def init_colors():
    curses.start_color()
    curses.use_default_colors()

    def c(r, g, b):
        return int(r * 3.9), int(g * 3.9), int(b * 3.9)

    curses.init_color(curses.COLOR_RED,     *c(252, 180, 190))  # rosewater
    curses.init_color(curses.COLOR_GREEN,   *c(150, 210, 160))  # mint
    curses.init_color(curses.COLOR_BLUE,    *c(160, 150, 210))  # lilac blue
    curses.init_color(curses.COLOR_YELLOW,  *c(255, 213, 128))  # gold
    curses.init_color(curses.COLOR_CYAN,    *c(207, 232, 213))  # teal mint
    curses.init_color(curses.COLOR_MAGENTA, *c(214, 201, 241))  # lilac
    curses.init_color(curses.COLOR_WHITE,   *c(250, 243, 224))  # vanilla

    curses.init_pair(1, curses.COLOR_RED,     -1)  # ROSE
    curses.init_pair(2, curses.COLOR_GREEN,   -1)  # MINT
    curses.init_pair(3, curses.COLOR_MAGENTA, -1)  # LILAC
    curses.init_pair(4, curses.COLOR_YELLOW,  -1)  # GOLD
    curses.init_pair(5, curses.COLOR_BLUE,    -1)  # MIST
    curses.init_pair(6, curses.COLOR_WHITE,   -1)  # CREAM
    curses.init_pair(7, curses.COLOR_CYAN,    -1)  # TEAL

ROSE  = lambda: curses.color_pair(1)
MINT  = lambda: curses.color_pair(2)
LILAC = lambda: curses.color_pair(3)
GOLD  = lambda: curses.color_pair(4)
MIST  = lambda: curses.color_pair(5)
CREAM = lambda: curses.color_pair(6)
TEAL  = lambda: curses.color_pair(7)
DIM   = lambda: curses.color_pair(5) | curses.A_DIM
BOLD  = lambda f: f() | curses.A_BOLD

# ─────────────────────────────────────────────
# THE CORE CONCEPT — recursive branching
# ─────────────────────────────────────────────
#
# Think of growth like this:
#
#   grow(row, col, direction, energy, branch_type)
#     → place a character at (row, col)
#     → reduce energy by 1
#     → if energy > 0:
#         → maybe split into two directions
#         → or continue in same direction with slight drift
#         → call grow() again with new position + less energy
#
# "energy" is how much life a branch has left.
# When energy hits 0 → place a leaf/flower and stop.
# This creates natural looking tapering because
# branches get thinner the further from the trunk 💕

# ─────────────────────────────────────────────
# BRANCH TYPES — what characters to use
# ─────────────────────────────────────────────
# Each type has characters for different growth directions
# and a color function

@dataclass
class BranchType:
    name:     str
    # characters indexed by direction (see DIR constants below)
    chars:    dict
    color_fn: object   # callable returning curses attr
    leaf_chars: list   # what to draw when energy runs out

# direction constants — these are (row_delta, col_delta) tuples
#
#   UP_LEFT   UP    UP_RIGHT
#       \      |      /
#        ·     ·     ·
#        ·     ·     ·
#   LEFT ←     ·     → RIGHT
#
UP        = (-1,  0)
UP_LEFT   = (-1, -1)
UP_RIGHT  = (-1,  1)
LEFT      = ( 0, -1)
RIGHT     = ( 0,  1)
UP_LEFT2  = (-1, -2)   # wider spread for bloom stage
UP_RIGHT2 = (-1,  2)

# character lookup by (row_delta, col_delta) direction
TRUNK_CHARS = {
    UP:        "|",
    UP_LEFT:   "/",
    UP_RIGHT:  "\\",
    LEFT:      "~",
    RIGHT:     "~",
    UP_LEFT2:  "/",
    UP_RIGHT2: "\\",
}

BRANCH_CHARS = {
    UP:        "|",
    UP_LEFT:   "/",
    UP_RIGHT:  "\\",
    LEFT:      "~",
    RIGHT:     "~",
    UP_LEFT2:  "/",
    UP_RIGHT2: "\\",
}

TWIG_CHARS = {
    UP:        ":",
    UP_LEFT:   "/",
    UP_RIGHT:  "\\",
    LEFT:      ".",
    RIGHT:     ".",
    UP_LEFT2:  "~",
    UP_RIGHT2: "~",
}

# branch type definitions for each stage
TRUNK_TYPE = BranchType(
    name="trunk",
    chars=TRUNK_CHARS,
    color_fn=MINT,
    leaf_chars=["&", "*", "✦"],
)

BRANCH_TYPE = BranchType(
    name="branch",
    chars=BRANCH_CHARS,
    color_fn=TEAL,
    leaf_chars=["✿", "꩜", "&", "∗"],
)

BLOOM_TYPE = BranchType(
    name="bloom",
    chars=BRANCH_CHARS,
    color_fn=ROSE,
    leaf_chars=["🌸", "✿", "꩜", "꩜", "✦"],
)

STAR_TYPE = BranchType(
    name="star",
    chars=TWIG_CHARS,
    color_fn=GOLD,
    leaf_chars=["✦", "∗", "·", "✦"],
)

LILAC_TYPE = BranchType(
    name="lilac",
    chars=BRANCH_CHARS,
    color_fn=LILAC,
    leaf_chars=["꩜", "✦", "∗", "꩜"],
)

# ─────────────────────────────────────────────
# GROWTH RULES PER STAGE
# ─────────────────────────────────────────────
# Each stage has different rules that shape how Petal grows.
# More energy = taller/wider. More split_chance = bushier.
# The stage rules are what make her feel like she's EVOLVING 🌱

STAGE_RULES = [
    # Stage 0 — Seed: tiny, single shoot, barely there
    {
        "name":          "Seed",
        "trunk_energy":  4,       # how tall the trunk grows
        "branch_energy": 2,       # how long branches grow
        "split_chance":  0.15,    # probability of splitting into two directions
        "drift_chance":  0.3,     # probability of drifting left or right
        "trunk_type":    TRUNK_TYPE,
        "branch_type":   BRANCH_TYPE,
        "twig_type":     STAR_TYPE,
        "wide_split":    False,   # whether branches can go wide (UP_LEFT2)
        "bloom_chance":  0.0,     # chance of a bloom branch appearing
    },
    # Stage 1 — Sprout: starting to branch, gentle
    {
        "name":          "Sprout",
        "trunk_energy":  7,
        "branch_energy": 4,
        "split_chance":  0.25,
        "drift_chance":  0.35,
        "trunk_type":    TRUNK_TYPE,
        "branch_type":   BRANCH_TYPE,
        "twig_type":     STAR_TYPE,
        "wide_split":    False,
        "bloom_chance":  0.0,
    },
    # Stage 2 — Bloom: fuller, flowers appearing, wider spread
    {
        "name":          "Bloom",
        "trunk_energy":  10,
        "branch_energy": 6,
        "split_chance":  0.35,
        "drift_chance":  0.4,
        "trunk_type":    TRUNK_TYPE,
        "branch_type":   BLOOM_TYPE,
        "twig_type":     BLOOM_TYPE,
        "wide_split":    True,
        "bloom_chance":  0.3,
    },
    # Stage 3 — Tree: full and lush, spreading wide
    {
        "name":          "Tree",
        "trunk_energy":  14,
        "branch_energy": 8,
        "split_chance":  0.45,
        "drift_chance":  0.45,
        "trunk_type":    TRUNK_TYPE,
        "branch_type":   LILAC_TYPE,
        "twig_type":     BLOOM_TYPE,
        "wide_split":    True,
        "bloom_chance":  0.5,
    },
    # Stage 4 — Starlight: otherworldly, gold and lilac
    {
        "name":          "Starlight",
        "trunk_energy":  16,
        "branch_energy": 10,
        "split_chance":  0.55,
        "drift_chance":  0.5,
        "trunk_type":    STAR_TYPE,
        "branch_type":   STAR_TYPE,
        "twig_type":     BLOOM_TYPE,
        "wide_split":    True,
        "bloom_chance":  0.7,
    },
]

# ─────────────────────────────────────────────
# THE CANVAS — we draw to this first, then render
# ─────────────────────────────────────────────
# Instead of drawing directly to curses one cell at a time
# during recursion, we collect all cells into a list first.
# Then we can animate them in order — growing from bottom up 🌱

@dataclass
class Cell:
    row:   int
    col:   int
    char:  str
    color: object   # curses attr
    order: int      # draw order for animation (lower = draw first)

# ─────────────────────────────────────────────
# THE RECURSIVE GROWTH FUNCTION
# ─────────────────────────────────────────────

def grow(
    cells:       list,         # we append Cell objects here
    row:         int,          # current position
    col:         int,
    direction:   tuple,        # current direction (row_delta, col_delta)
    energy:      int,          # life remaining in this branch
    branch_type: BranchType,   # what kind of branch this is
    rules:       dict,         # stage rules
    order:       int,          # draw order counter
    is_trunk:    bool = False,  # trunk behaves slightly differently
) -> int:
    """
    Recursively grow a branch from (row, col) in direction.
    Returns updated order counter.

    This is the heart of the whole system 💕
    """

    # BASE CASE — energy depleted, place a leaf and stop
    if energy <= 0:
        leaf = random.choice(branch_type.leaf_chars)
        cells.append(Cell(
            row=row, col=col,
            char=leaf,
            color=BOLD(branch_type.color_fn),
            order=order
        ))
        return order + 1

    # ── place current character ──
    char = branch_type.chars.get(direction, "|")
    cells.append(Cell(
        row=row, col=col,
        char=char,
        color=branch_type.color_fn(),
        order=order,
    ))
    order += 1

    # ── calculate next position ──
    next_row = row + direction[0]
    next_col = col + direction[1]
    next_energy = energy - 1

    # ── decide what to do next ──
    # this random decision tree is what makes each growth unique

    roll = random.random()

    # SPLIT — branch into two directions
    if roll < rules["split_chance"]:
        # choose two diverging directions
        if rules["wide_split"] and random.random() < 0.3:
            dirs = [UP_LEFT2, UP_RIGHT2]
        else:
            dirs = [UP_LEFT, UP_RIGHT]

        # the new branch type — sometimes switches to bloom
        if random.random() < rules["bloom_chance"]:
            new_type = rules["twig_type"]
        else:
            new_type = rules["branch_type"]

        for d in dirs:
            order = grow(
                cells, next_row, next_col + d[1],
                d, next_energy - 1,
                new_type, rules, order
            )

    # DRIFT — continue but shift slightly left or right
    elif roll < rules["split_chance"] + rules["drift_chance"]:
        drift = random.choice([UP_LEFT, UP_RIGHT, UP])
        order = grow(
            cells, next_row, next_col,
            drift, next_energy,
            branch_type, rules, order
        )

    # STRAIGHT — keep going in same direction
    else:
        order = grow(
            cells, next_row, next_col,
            direction, next_energy,
            branch_type, rules, order
        )

    return order

# ─────────────────────────────────────────────
# GROW PETAL — builds the full cell list
# ─────────────────────────────────────────────

def grow_petal(base_row: int, base_col: int, stage: int) -> list:
    """
    Grow Petal from base_row/col upward.
    Returns a list of Cell objects sorted by draw order.
    """
    rules = STAGE_RULES[min(stage, len(STAGE_RULES) - 1)]
    cells = []
    order = 0

    # ── grow the trunk straight up first ──
    # trunk always starts going straight UP
    order = grow(
        cells,
        row=base_row,
        col=base_col,
        direction=UP,
        energy=rules["trunk_energy"],
        branch_type=rules["trunk_type"],
        rules=rules,
        order=order,
        is_trunk=True,
    )

    # ── add a face near the top of the trunk ──
    # find the topmost cell (lowest row number)
    if cells:
        top = min(cells, key=lambda c: c.row)
        face = get_face_for_stage(stage)
        face_row = top.row - 1
        face_col = base_col - len(face) // 2

        for i, ch in enumerate(face):
            color = BOLD(ROSE) if ch not in ("|", " ") else MINT()
            cells.append(Cell(
                row=face_row,
                col=face_col + i,
                char=ch,
                color=color,
                order=order + i,
            ))

    # sort by draw order so animation flows naturally
    cells.sort(key=lambda c: c.order)
    return cells

# ─────────────────────────────────────────────
# PETAL'S FACE — changes with stage 🌸
# ─────────────────────────────────────────────

def get_face_for_stage(stage: int) -> str:
    faces = [
        "(·)",        # seed — tiny dot
        "(◠‿◠)",      # sprout — gentle smile
        "(◕‿◕✿)",     # bloom — flowers in eyes
        "(◠‿◠✿)",     # tree — full bloom
        "(✦‿✦)",      # starlight — star eyes
    ]
    return faces[min(stage, len(faces) - 1)]

# ─────────────────────────────────────────────
# SAFE DRAW HELPER
# ─────────────────────────────────────────────

def safe_addch(win, row, col, ch, attr=0):
    max_row, max_col = win.getmaxyx()
    if 0 <= row < max_row - 1 and 0 <= col < max_col - 1:
        try:
            win.addch(row, col, ch, attr)
        except curses.error:
            pass

def safe_addstr(win, row, col, text, attr=0):
    max_row, max_col = win.getmaxyx()
    if 0 <= row < max_row - 1 and 0 <= col < max_col - 1:
        try:
            space = max_col - col - 1
            win.addstr(row, col, text[:space], attr)
        except curses.error:
            pass

# ─────────────────────────────────────────────
# SOIL + ATMOSPHERE
# ─────────────────────────────────────────────

def draw_soil(win, soil_row: int, width: int):
    soil_chars = ["▓", "▒", "░", "▓", "▒", "▓", "░", "▒"]
    for col in range(width - 1):
        ch = soil_chars[col % len(soil_chars)]
        safe_addch(win, soil_row, col, ch, GOLD() | curses.A_DIM)

def draw_atmosphere(win, height: int, width: int, growth: int):
    """Scatter stars — more growth = more stars ✦"""
    count = int(growth / 4)
    for _ in range(count):
        r = random.randint(1, height // 2)
        c = random.randint(1, width - 2)
        ch = random.choice(["·", "∗", "✦", "·", "·", "·"])
        safe_addch(win, r, c, ch, DIM())

# ─────────────────────────────────────────────
# STAT BARS
# ─────────────────────────────────────────────

def draw_stats(win, stats: dict, row: int, width: int):
    rules = STAGE_RULES[min(stats["stage"], len(STAGE_RULES) - 1)]

    safe_addstr(win, row, 2,
        f"Petal  —  {rules['name']}  ·  Day {stats.get('age', 0)}",
        BOLD(ROSE))

    pairs = [
        ("Happiness",  "happiness",  ROSE),
        ("Discipline", "discipline", LILAC),
        ("Growth",     "growth",     MINT),
    ]
    for i, (label, key, color_fn) in enumerate(pairs):
        val = stats.get(key, 0)
        bw  = 14
        bar = "█" * round(val / 100 * bw) + "░" * (bw - round(val / 100 * bw))
        safe_addstr(win, row + 2 + i, 2,  f"{label:<11}", MIST())
        safe_addstr(win, row + 2 + i, 13, bar,            color_fn())
        safe_addstr(win, row + 2 + i, 28, str(val),        DIM())

# ─────────────────────────────────────────────
# ANIMATE GROWTH
# ─────────────────────────────────────────────

def animate_growth(win, cells: list, delay: float = 0.018):
    """
    Draw cells one at a time in order.
    Bottom-up because we sorted by draw order which
    naturally goes trunk → branches → tips → leaves 🌱
    """
    for cell in cells:
        safe_addch(win, cell.row, cell.col, cell.char, cell.color)

        # only refresh every few cells for speed
        # refreshing every single character would be too slow
        if cell.order % 3 == 0:
            win.refresh()
            time.sleep(delay)

    win.refresh()

# ─────────────────────────────────────────────
# FULL SCENE
# ─────────────────────────────────────────────

def draw_scene(win, stats: dict):
    win.clear()
    height, width = win.getmaxyx()

    soil_row   = int(height * 0.68)
    center_col = width // 2
    stats_row  = soil_row + 2

    # atmosphere first — stars in background
    draw_atmosphere(win, height, width, stats.get("growth", 20))

    # title
    title = "✦ Petal's World"
    safe_addstr(win, 1, center_col - len(title) // 2, title, BOLD(ROSE))

    # mood line
    mood_text = f"feeling {get_mood_label(stats)}"
    safe_addstr(win, 2, center_col - len(mood_text) // 2, mood_text,
                MIST() | curses.A_ITALIC)

    # soil
    draw_soil(win, soil_row, width)

    # grow Petal from soil upward
    cells = grow_petal(
        base_row=soil_row - 1,
        base_col=center_col,
        stage=stats["stage"],
    )

    # animate her growing
    animate_growth(win, cells)

    # stats panel
    draw_stats(win, stats, stats_row, width)

    # footer
    hint = "any key — regrow  ·  s — next stage  ·  q — quit"
    safe_addstr(win, height - 2, center_col - len(hint) // 2, hint, DIM())

    win.refresh()

# ─────────────────────────────────────────────
# MOOD
# ─────────────────────────────────────────────

def get_mood_label(stats: dict) -> str:
    h = stats.get("happiness", 50)
    d = stats.get("discipline", 50)
    if h >= 80 and d >= 70: return "radiant ✦"
    elif h >= 65:            return "happy 🌸"
    elif h >= 45:            return "content"
    elif h < 35:             return "sad..."
    elif d < 30:             return "restless"
    else:                    return "quiet 🌙"

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main(stdscr):
    curses.curs_set(0)
    init_colors()

    # test stats — Phase 2 will load from petal_save.json 💕
    stats = {
        "happiness":  65,
        "discipline": 50,
        "growth":     35,
        "stage":      0,
        "age":        1,
    }

    while True:
        draw_scene(stdscr, stats)

        key = stdscr.getch()

        if key == ord('q'):
            break

        # s cycles through stages so you can preview all of them!
        elif key == ord('s'):
            stats["stage"] = (stats["stage"] + 1) % len(STAGE_RULES)
            stats["growth"] = STAGE_RULES[stats["stage"]]["trunk_energy"] * 4

        # any other key — just regrow with slight stat nudge
        else:
            stats["happiness"]  = max(0, min(100, stats["happiness"]  + random.randint(-5, 8)))
            stats["discipline"] = max(0, min(100, stats["discipline"] + random.randint(-5, 8)))
            stats["growth"]     = max(0, min(100, stats["growth"]     + random.randint(0, 5)))


if __name__ == "__main__":
    curses.wrapper(main)