#!/usr/bin/env python3
"""
🌸 Procedural Flower Bed — Proof of Concept
A living flower bed that grows based on Petal's stats.
Run with: python3 flowerbed.py

Press any key to regenerate. Press 'q' to quit.
"""

import curses
import random
import time
import math

# ─────────────────────────────────────────────
# THE CONCEPT — how curses works
# ─────────────────────────────────────────────
# Your terminal is a GRID. Every character has a position:
#
#   col →  0  1  2  3  4  5  6
# row 0:   .  .  .  .  .  .  .
# row 1:   .  .  .  *  .  .  .   ← stdscr.addch(1, 3, '*')
# row 2:   .  .  /  |  \  .  .
#
# curses.addch(row, col, character) — place ONE character
# curses.addstr(row, col, "text")  — place a STRING
# curses.refresh()                 — actually DRAW it all
#
# Nothing appears until you call refresh() — it's like a canvas
# you paint on privately, then reveal all at once 💕

# ─────────────────────────────────────────────
# COLOR PAIRS
# ─────────────────────────────────────────────
# curses uses "color pairs" — you define pair(id, fg, bg)
# then reference that pair id when drawing characters
#
# COLOR_PAIR(1) = rosewater pink
# COLOR_PAIR(2) = mint green
# COLOR_PAIR(3) = lilac purple
# COLOR_PAIR(4) = soft gold
# COLOR_PAIR(5) = dim mist
# COLOR_PAIR(6) = soil brown
# COLOR_PAIR(7) = sky blue
# COLOR_PAIR(8) = white

def init_colors():
    """Set up all our Evergarden color pairs."""
    curses.start_color()
    curses.use_default_colors()  # -1 means "use terminal's default background"

    # curses only has 8 built-in colors but we can redefine them
    # using curses.init_color(id, r, g, b) where values are 0-1000 (not 0-255!!)
    # so we convert: 0-255 → 0-1000 by multiplying by ~3.9

    def c(r, g, b):
        """Convert 0-255 RGB to 0-1000 curses scale."""
        return int(r * 3.9), int(g * 3.9), int(b * 3.9)

    # redefine curses color slots with our Evergarden palette
    curses.init_color(curses.COLOR_RED,     *c(252, 180, 180))  # soft red/rose
    curses.init_color(curses.COLOR_GREEN,   *c(150, 210, 160))  # soft green
    curses.init_color(curses.COLOR_BLUE,    *c(180, 180, 220))  # lilac blue
    curses.init_color(curses.COLOR_YELLOW,  *c(255, 213, 128))  # soft gold
    curses.init_color(curses.COLOR_CYAN,    *c(207, 232, 213))  # mint
    curses.init_color(curses.COLOR_MAGENTA, *c(214, 201, 241))  # lilac
    curses.init_color(curses.COLOR_WHITE,   *c(250, 243, 224))  # vanilla cream

    # now pair each color with a background (-1 = terminal default)
    curses.init_pair(1, curses.COLOR_RED,     -1)  # rose
    curses.init_pair(2, curses.COLOR_GREEN,   -1)  # mint
    curses.init_pair(3, curses.COLOR_MAGENTA, -1)  # lilac
    curses.init_pair(4, curses.COLOR_YELLOW,  -1)  # gold
    curses.init_pair(5, curses.COLOR_BLUE,    -1)  # mist
    curses.init_pair(6, curses.COLOR_WHITE,   -1)  # vanilla
    curses.init_pair(7, curses.COLOR_CYAN,    -1)  # mint bright

# shorthand accessors — these return the attribute to pass to addch/addstr
ROSE   = lambda: curses.color_pair(1)
MINT   = lambda: curses.color_pair(2)
LILAC  = lambda: curses.color_pair(3)
GOLD   = lambda: curses.color_pair(4)
MIST   = lambda: curses.color_pair(5)
CREAM  = lambda: curses.color_pair(6)
TEAL   = lambda: curses.color_pair(7)
DIM    = lambda: curses.color_pair(5) | curses.A_DIM
BOLD   = lambda pair: pair() | curses.A_BOLD

# ─────────────────────────────────────────────
# FLOWER TYPES
# ─────────────────────────────────────────────
# Each flower is a dict describing how to draw it.
# "layers" is a list of (row_offset, col_offset, char, color_fn)
# row_offset 0 = the bloom, positive = going DOWN (stem)

FLOWER_TYPES = [
    {
        # 🌸 Small daisy — happiness flower
        "name": "daisy",
        "stat": "happiness",
        "min_stat": 30,
        "layers": [
            # bloom
            (-2, 0, "✿", ROSE),
            # stem
            (-1, 0, "|", MINT),
            ( 0, 0, "|", MINT),
        ],
        "tall": 3,
    },
    {
        # 🌺 Full bloom — high happiness
        "name": "bloom",
        "stat": "happiness",
        "min_stat": 65,
        "layers": [
            (-3, -1, "꩜", ROSE),
            (-3,  0, "✿", GOLD),
            (-3,  1, "꩜", ROSE),
            (-2,  0, "|", MINT),
            (-1,  0, "|", MINT),
            ( 0,  0, "|", MINT),
        ],
        "tall": 4,
    },
    {
        # 🌿 Grass blade — always present (base)
        "name": "grass",
        "stat": None,
        "min_stat": 0,
        "layers": [
            (-1, 0, "╿", MINT),
            ( 0, 0, "╽", TEAL),
        ],
        "tall": 2,
    },
    {
        # 🌱 Sprout — discipline flower
        "name": "sprout",
        "stat": "discipline",
        "min_stat": 20,
        "layers": [
            (-2, 0, "⌒", TEAL),
            (-1, 0, "┃", MINT),
            ( 0, 0, "┃", MINT),
        ],
        "tall": 3,
    },
    {
        # ✦ Star flower — growth flower
        "name": "starflower",
        "stat": "growth",
        "min_stat": 40,
        "layers": [
            (-3,  0, "✦", GOLD),
            (-2, -1, "∗", LILAC),
            (-2,  1, "∗", LILAC),
            (-1,  0, "|", CREAM),
            ( 0,  0, "|", CREAM),
        ],
        "tall": 4,
    },
    {
        # 🌙 Moon flower — rare, appears when growth is high
        "name": "moonflower",
        "stat": "growth",
        "min_stat": 70,
        "layers": [
            (-4,  0, "꩜", LILAC),
            (-3, -1, "✦", MIST),
            (-3,  1, "✦", MIST),
            (-2,  0, "◈", LILAC),
            (-1,  0, "┃", MIST),
            ( 0,  0, "┃", MIST),
        ],
        "tall": 5,
    },
]

# ─────────────────────────────────────────────
# THE FLOWER BED GENERATOR
# ─────────────────────────────────────────────
# This is the "procedural" part — every call produces a
# slightly different bed based on stats + randomness 🌿

def generate_bed(stats: dict, width: int) -> list:
    """
    Generate a list of flower placements for the bed.

    Returns a list of:
        (col, flower_type_dict)

    The col is where on the x-axis the flower lives.
    We space them out so they don't overlap.
    """
    flowers = []

    # figure out which flower types are available given current stats
    available = []
    for ftype in FLOWER_TYPES:
        stat_name = ftype["stat"]
        if stat_name is None:
            # grass is always available
            available.append(ftype)
        elif stats.get(stat_name, 0) >= ftype["min_stat"]:
            available.append(ftype)

    # how many flowers fit? space them 3 cols apart minimum
    # leave 4 cols on each side as margin
    margin = 4
    usable_width = width - (margin * 2)
    spacing = 3
    max_flowers = usable_width // spacing

    # place flowers at slightly randomized positions
    positions = []
    col = margin
    while col < width - margin and len(positions) < max_flowers:
        # add a tiny random nudge so they don't look grid-like
        nudge = random.randint(-1, 1)
        positions.append(max(margin, min(width - margin, col + nudge)))
        col += spacing

    # assign a flower type to each position
    for col in positions:
        # weight selection — rarer flowers appear less often
        weights = []
        for f in available:
            if f["name"] == "grass":
                weights.append(3)       # grass is common
            elif f["name"] == "daisy":
                weights.append(2)
            elif f["name"] in ("bloom", "starflower"):
                weights.append(1.5)
            else:
                weights.append(0.8)    # rare flowers less common

        chosen = random.choices(available, weights=weights, k=1)[0]
        flowers.append((col, chosen))

    return flowers

# ─────────────────────────────────────────────
# DRAWING HELPERS
# ─────────────────────────────────────────────

def safe_addch(win, row, col, ch, attr=0):
    """
    curses raises an error if you try to draw outside the window bounds
    or on the very last cell (bottom-right corner quirk).
    This wrapper just silently ignores those cases 💕
    """
    max_row, max_col = win.getmaxyx()
    if 0 <= row < max_row and 0 <= col < max_col - 1:
        try:
            win.addch(row, col, ch, attr)
        except curses.error:
            pass

def safe_addstr(win, row, col, text, attr=0):
    """Same safety wrapper for strings."""
    max_row, max_col = win.getmaxyx()
    if 0 <= row < max_row and 0 <= col < max_col - 1:
        try:
            # clip the string if it would go off screen
            space = max_col - col - 1
            win.addstr(row, col, text[:space], attr)
        except curses.error:
            pass

# ─────────────────────────────────────────────
# DRAW THE SOIL LINE
# ─────────────────────────────────────────────

def draw_soil(win, soil_row: int, width: int):
    """
    The soil is the baseline everything grows from.
    We draw a textured line using different characters
    to make it feel organic rather than just dashes.
    """
    soil_chars = ["▓", "▒", "░", "▓", "▒", "▓", "░", "▒"]

    for col in range(width - 1):
        # cycle through soil chars for a textured look
        ch = soil_chars[col % len(soil_chars)]
        safe_addch(win, soil_row, col, ch, GOLD() | curses.A_DIM)

# ─────────────────────────────────────────────
# DRAW ALL FLOWERS
# ─────────────────────────────────────────────

def draw_flowers(win, flowers: list, soil_row: int):
    """
    For each flower in our generated bed, draw its layers.

    Each layer has a row_offset — negative means ABOVE the soil.
    So a layer with row_offset -2 draws 2 rows above soil_row.

    col_offset shifts left/right from the flower's base position.
    """
    for base_col, ftype in flowers:
        for (row_off, col_off, char, color_fn) in ftype["layers"]:
            # calculate actual screen position
            draw_row = soil_row + row_off
            draw_col = base_col + col_off

            safe_addch(win, draw_row, draw_col, char, color_fn())

# ─────────────────────────────────────────────
# DRAW PETAL (placeholder sprite for now)
# ─────────────────────────────────────────────
# This is where her procedural body will go in the full version.
# For now she's a simple stage-based sprite in the center 🌸

PETAL_STAGES = [
    # stage 0 — Seed
    [
        "  ✦  ",
        " (·) ",
        "  |  ",
    ],
    # stage 1 — Sprout
    [
        "  𓆸  ",
        "(◠‿◠)",
        r" /|\ ",
        "  |  ",
    ],
    # stage 2 — Bloom
    [
        " ꩜𓆸꩜ ",
        "(◕‿◕✿)",
        r" /|\ ",
        "  |  ",
    ],
    # stage 3 — Tree
    [
        "꩜꩜𓆸꩜꩜",
        "(◠‿◠✿)",
        "ʕ/|\\ʔ ",
        "  |  ",
    ],
]

PETAL_COLORS = [CREAM, MINT, ROSE, GOLD]

def draw_petal(win, stage: int, mood: str, soil_row: int, center_col: int):
    """Draw Petal herself above the soil at the center of the screen."""
    sprite = PETAL_STAGES[min(stage, len(PETAL_STAGES) - 1)]
    color  = PETAL_COLORS[min(stage, len(PETAL_COLORS) - 1)]

    # draw from bottom up (sprite[0] is the top/head)
    start_row = soil_row - len(sprite)
    for i, line in enumerate(sprite):
        draw_row = start_row + i
        draw_col = center_col - len(line) // 2
        safe_addstr(win, draw_row, draw_col, line, BOLD(color))

# ─────────────────────────────────────────────
# DRAW THE STATS PANEL
# ─────────────────────────────────────────────

def draw_stats(win, stats: dict, start_row: int):
    """Simple stat bars below the scene."""
    labels = [
        ("Happiness",  "happiness",  ROSE),
        ("Discipline", "discipline", LILAC),
        ("Growth",     "growth",     MINT),
    ]

    safe_addstr(win, start_row, 2, "Petal", BOLD(ROSE))
    safe_addstr(win, start_row, 8,
                f"  Stage {stats.get('stage', 0)}  ·  Day {stats.get('age', 0)}",
                DIM())

    for i, (label, key, color_fn) in enumerate(labels):
        row = start_row + 2 + i
        val = stats.get(key, 0)
        bar_width = 16
        filled = round(val / 100 * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        safe_addstr(win, row, 2,  f"{label:<11}", MIST())
        safe_addstr(win, row, 13, bar,            color_fn())
        safe_addstr(win, row, 30, str(val),        DIM())

# ─────────────────────────────────────────────
# ANIMATION — flowers bloom in sequence
# ─────────────────────────────────────────────

def animate_bloom(win, flowers: list, soil_row: int):
    """
    Reveal flowers one layer at a time from soil upward.
    This gives a satisfying growing-from-ground feeling 🌱

    We loop from row 0 (top of tallest flower) up to soil,
    drawing only layers that exist at or below current reveal row.
    """
    # find the tallest flower
    max_height = max((f["tall"] for _, f in flowers), default=3)

    # animate from soil upward
    for reveal_height in range(1, max_height + 2):
        for base_col, ftype in flowers:
            for (row_off, col_off, char, color_fn) in ftype["layers"]:
                # only draw if this layer is within our current reveal height
                if abs(row_off) <= reveal_height:
                    draw_row = soil_row + row_off
                    draw_col = base_col + col_off
                    safe_addch(win, draw_row, draw_col, char, color_fn())

        win.refresh()
        time.sleep(0.04)   # 40ms between each reveal step — feels natural

# ─────────────────────────────────────────────
# MAIN SCENE COMPOSER
# ─────────────────────────────────────────────

def draw_scene(win, stats: dict):
    """
    Compose the full scene:
    1. Clear canvas
    2. Calculate layout based on terminal size
    3. Draw sky/background
    4. Draw Petal
    5. Draw soil
    6. Animate flowers blooming
    7. Draw stats panel
    8. Draw footer hint
    """
    win.clear()
    height, width = win.getmaxyx()

    # layout calculations
    # soil sits at 65% down the screen, leaving room for stats below
    soil_row   = int(height * 0.60)
    center_col = width // 2
    stats_row  = soil_row + 2

    # ── background atmosphere ──
    # scatter a few tiny stars in the upper portion
    # we use the stats to influence how many stars appear
    # more growth = more stars = more magical feeling ✦
    star_count = int(stats.get("growth", 20) / 5)
    for _ in range(star_count):
        star_row = random.randint(1, soil_row - 8)
        star_col = random.randint(1, width - 2)
        star_ch  = random.choice(["·", "✦", "∗", "·", "·"])
        safe_addch(win, star_row, star_col, star_ch, DIM())

    # ── title ──
    title = "✦ Petal's World"
    safe_addstr(win, 1, center_col - len(title) // 2, title,
                BOLD(ROSE))

    # ── Petal herself ──
    draw_petal(win, stats.get("stage", 0), stats.get("mood", "content"),
               soil_row, center_col)

    # ── soil ──
    draw_soil(win, soil_row, width)

    # ── generate and animate flower bed ──
    flowers = generate_bed(stats, width)
    animate_bloom(win, flowers, soil_row)

    # ── stats panel ──
    draw_stats(win, stats, stats_row)

    # ── footer ──
    hint = "press any key to regenerate  ·  q to quit"
    safe_addstr(win, height - 1, center_col - len(hint) // 2,
                hint, DIM())

    win.refresh()

# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

def main(stdscr):
    """
    curses.wrapper() calls this function with stdscr — the main window.
    stdscr is your full terminal canvas 🌸
    """
    # hide the blinking cursor — cleaner look
    curses.curs_set(0)

    # init our color palette
    init_colors()

    # test stats — in Phase 2 these come from your real data!
    # try changing these numbers to see how the bed changes 👀
    stats = {
        "happiness":  42,
        "discipline": 63,
        "growth":     2,
        "stage":      1,
        "age":        12,
        "mood":       "happy",
    }

    # main loop
    while True:
        draw_scene(stdscr, stats)

        # wait for a keypress
        # stdscr.getch() BLOCKS here — nothing happens until you press a key
        key = stdscr.getch()

        if key == ord('q'):
            break

        # nudge stats randomly on each regeneration so you can see variety
        # (remove this in the real version — stats will come from real data)
        stats["happiness"]  = max(0, min(100, stats["happiness"]  + random.randint(-10, 10)))
        stats["discipline"] = max(0, min(100, stats["discipline"] + random.randint(-8, 8)))
        stats["growth"]     = max(0, min(100, stats["growth"]     + random.randint(-5, 10)))


# curses.wrapper handles setup and teardown safely —
# if your code crashes it restores the terminal properly
# instead of leaving it in a broken state 💕
if __name__ == "__main__":
    curses.wrapper(main)