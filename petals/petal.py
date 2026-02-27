#!/usr/bin/env python3
"""
🌸 Petal — Phase 1
A soft, mysterious little creature who lives in your terminal.
Her world is yours. Her mood is real.

Usage:
    python3 petal.py
"""

import json
import os
import sys
import math
from datetime import datetime, date
from pathlib import Path

# ─────────────────────────────────────────────
# ANSI COLORS
# ─────────────────────────────────────────────
class C:
    RESET      = "\033[0m"
    BOLD       = "\033[1m"
    DIM        = "\033[2m"
    ITALIC     = "\033[3m"

    # foreground
    BLACK      = "\033[30m"
    RED        = "\033[31m"
    GREEN      = "\033[32m"
    YELLOW     = "\033[33m"
    BLUE       = "\033[34m"
    MAGENTA    = "\033[35m"
    CYAN       = "\033[36m"
    WHITE      = "\033[37m"

    # bright foreground
    BRED       = "\033[91m"
    BGREEN     = "\033[92m"
    BYELLOW    = "\033[93m"
    BBLUE      = "\033[94m"
    BMAGENTA   = "\033[95m"
    BCYAN      = "\033[96m"
    BWHITE     = "\033[97m"

    # background
    BG_BLACK   = "\033[40m"
    BG_MAGENTA = "\033[45m"
    BG_BLUE    = "\033[44m"

    @staticmethod
    def rgb(r, g, b, text):
        return f"\033[38;2;{r};{g};{b}m{text}{C.RESET}"

    @staticmethod
    def bg_rgb(r, g, b, text):
        return f"\033[48;2;{r};{g};{b}m{text}{C.RESET}"

# Evergarden palette 🌸
ROSEWATER  = lambda t: C.rgb(252, 225, 236, t)
MINT       = lambda t: C.rgb(207, 232, 213, t)
LILAC      = lambda t: C.rgb(214, 201, 241, t)
VANILLA    = lambda t: C.rgb(250, 243, 224, t)
SOFTGOLD   = lambda t: C.rgb(255, 213, 128, t)
MIST       = lambda t: C.rgb(180, 180, 200, t)
DIMTEXT    = lambda t: C.rgb(130, 120, 140, t)
SOFTGREEN  = lambda t: C.rgb(150, 210, 160, t)
SOFTRED    = lambda t: C.rgb(230, 150, 150, t)

# ─────────────────────────────────────────────
# SAVE FILE
# ─────────────────────────────────────────────
SAVE_PATH = Path(__file__).parent / ".petal_save.json"

DEFAULT_STATE = {
    "name": "Petal",
    "birthday": str(date.today()),
    "happiness":   60,
    "discipline":  40,
    "growth":      20,
    "stage":       0,        # 0=seed 1=sprout 2=bloom 3=tree 4=star
    "last_seen":   str(date.today()),
    "journal_streak": 0,
    "last_journaled":  "",
    "last_studied":    "",
    "total_actions":   0,
    "mood_history":    [],
}

def load_state() -> dict:
    if SAVE_PATH.exists():
        try:
            return json.loads(SAVE_PATH.read_text())
        except json.JSONDecodeError:
            pass
    return DEFAULT_STATE.copy()

def save_state(state: dict):
    SAVE_PATH.write_text(json.dumps(state, indent=2))

# ─────────────────────────────────────────────
# STAT HELPERS
# ─────────────────────────────────────────────
def clamp(val, lo=0, hi=100):
    return max(lo, min(hi, val))

def apply_daily_decay(state: dict) -> dict:
    """Stats decay gently if Petal hasn't been visited today."""
    last = state.get("last_seen", str(date.today()))
    today = str(date.today())
    if last == today:
        return state

    try:
        delta = (date.today() - date.fromisoformat(last)).days
    except ValueError:
        delta = 0

    if delta > 0:
        decay = min(delta * 4, 30)
        state["happiness"]  = clamp(state["happiness"]  - decay)
        state["discipline"] = clamp(state["discipline"] - decay // 2)
        # growth never decays — it's earned forever 🌿

    state["last_seen"] = today
    return state

# ─────────────────────────────────────────────
# MOOD SYSTEM
# ─────────────────────────────────────────────
def get_mood(state: dict) -> str:
    h = state["happiness"]
    d = state["discipline"]
    g = state["growth"]

    if h >= 80 and d >= 70:
        return "radiant"
    elif h >= 65:
        return "happy"
    elif h >= 45 and d >= 50:
        return "content"
    elif d < 30 and h < 40:
        return "withdrawn"
    elif h < 35:
        return "sad"
    elif d < 35:
        return "restless"
    else:
        return "quiet"

# ─────────────────────────────────────────────
# ASCII ART — mood driven 🌸
# ─────────────────────────────────────────────
STAGE_NAMES = ["Seed", "Sprout", "Bloom", "Tree", "Starlight"]
STAGE_NEXT  = [30, 50, 120, 220, 999]   # growth needed to evolve

PETAL_ART = {
    "radiant": [
        "    ✦  ✦  ✦    ",
        "   (◠‿◠✿)      ",
        "   ʕ🌸ʔ づ      ",
        "    ∪∪           ",
    ],
    "happy": [
        "               ",
        "   (｡◕‿◕｡)    ",
        "   ʕ🌱ʔ づ     ",
        "    ∪∪          ",
    ],
    "content": [
        "               ",
        "   (｡•‿•｡)    ",
        "   ʕ🌿ʔ づ     ",
        "    ∪∪          ",
    ],
    "quiet": [
        "    ·  ·        ",
        "   (｀•ω•´)    ",
        "   ʕ🌙ʔ づ     ",
        "    ∪∪          ",
    ],
    "restless": [
        "    ~ ~ ~       ",
        "   (•̀ω•́)ง     ",
        "   ʕ🍂ʔ づ     ",
        "    ∪∪          ",
    ],
    "sad": [
        "    . . .       ",
        "   (╥_╥)        ",
        "   ʕ🥀ʔ づ     ",
        "    ∪∪          ",
    ],
    "withdrawn": [
        "               ",
        "   ( . . )     ",
        "   ʕ💤ʔ づ     ",
        "    ∪∪          ",
    ],
}

MOOD_COLORS = {
    "radiant":   ROSEWATER,
    "happy":     SOFTGOLD,
    "content":   MINT,
    "quiet":     LILAC,
    "restless":  VANILLA,
    "sad":       MIST,
    "withdrawn": DIMTEXT,
}

# ─────────────────────────────────────────────
# PETAL'S VOICE — she wears her heart on sleeve
# ─────────────────────────────────────────────
PETAL_DIALOGUE = {
    "radiant": [
        "Everything feels warm today... I'm glad you're here.",
        "Something is blooming. I can feel it.",
        "The world feels very gentle right now.",
    ],
    "happy": [
        "Oh, you came back! I was hoping you would.",
        "I feel light today. Like petals in wind.",
        "Today feels like a good day to grow.",
    ],
    "content": [
        "I'm here. Just watching the quiet.",
        "Not every day needs to be big. This is enough.",
        "I've been thinking about things. Nothing urgent.",
    ],
    "quiet": [
        "...",
        "I'm not sad. I just have a lot inside right now.",
        "Some days I go inward. Today is one of those.",
    ],
    "restless": [
        "I need something. I'm not sure what.",
        "Have you been consistent lately? I can feel when you're not.",
        "The stillness is getting loud.",
    ],
    "sad": [
        "I missed you. It's been a while.",
        "I don't want to complain... but I've been feeling low.",
        "Come back more often? Please?",
    ],
    "withdrawn": [
        "...",
        "I don't have much to say today.",
        "Maybe tomorrow will be different.",
    ],
}

import random
def get_dialogue(mood: str) -> str:
    return random.choice(PETAL_DIALOGUE.get(mood, ["..."]))

# ─────────────────────────────────────────────
# DISPLAY
# ─────────────────────────────────────────────
def clear():
    os.system("clear" if os.name == "posix" else "cls")

def bar(value: int, width: int = 20, fill="█", empty="░") -> str:
    filled = round(value / 100 * width)
    return fill * filled + empty * (width - filled)

def render(state: dict):
    clear()
    mood  = get_mood(state)
    color = MOOD_COLORS.get(mood, VANILLA)
    art   = PETAL_ART.get(mood, PETAL_ART["content"])
    stage = STAGE_NAMES[min(state["stage"], len(STAGE_NAMES)-1)]
    age   = (date.today() - date.fromisoformat(state["birthday"])).days

    # ── header ──
    print()
    print(ROSEWATER("  ✦ Petal's World") + DIMTEXT("  ·  ") + DIMTEXT(datetime.now().strftime("%b %d, %Y  %I:%M %p")))
    print(DIMTEXT("  " + "─" * 44))
    print()

    # ── art ──
    for line in art:
        print(color("  " + line))
    print()

    # ── name + stage ──
    print(f"  {C.BOLD}{color(state['name'])}{C.RESET}  {DIMTEXT(f'— {stage}  ·  Day {age}')}")
    print(f"  {DIMTEXT('feeling')} {C.ITALIC}{color(mood)}{C.RESET}")
    print()

    # ── dialogue ──
    quote = get_dialogue(mood)
    print(DIMTEXT("  ❝ ") + LILAC(C.ITALIC + quote + C.RESET))
    print()

    # ── stats ──
    print(DIMTEXT("  " + "─" * 44))
    h = state["happiness"]
    d = state["discipline"]
    g = state["growth"]

    # color bars based on value
    def stat_color(v):
        if v >= 70: return SOFTGREEN
        elif v >= 40: return SOFTGOLD
        else: return SOFTRED

    print(f"  {SOFTGOLD('Happiness')}  {C.BOLD}{stat_color(h)(bar(h))}{C.RESET}  {DIMTEXT(str(h))}")
    print(f"  {LILAC('Discipline')} {C.BOLD}{stat_color(d)(bar(d))}{C.RESET}  {DIMTEXT(str(d))}")
    print(f"  {MINT('Growth')}     {C.BOLD}{MINT(bar(g))}{C.RESET}  {DIMTEXT(str(g))}")

    # ── evolution hint ──
    next_threshold = STAGE_NEXT[min(state["stage"], len(STAGE_NEXT)-1)]
    needed = next_threshold - g
    if needed > 0:
        print()
        print(DIMTEXT(f"  ✦ {needed} growth until next stage..."))
    else:
        print()
        print(ROSEWATER("  ✦ Petal is ready to evolve... ") + DIMTEXT("(choose 'rest' to let it happen)"))

    # ── streak ──
    if state["journal_streak"] > 0:
        print(DIMTEXT(f"  🌿 Journal streak: {state['journal_streak']} days"))

    print()
    print(DIMTEXT("  " + "─" * 44))

# ─────────────────────────────────────────────
# ACTIONS
# ─────────────────────────────────────────────
def action_journal(state: dict) -> dict:
    today = str(date.today())
    already = state.get("last_journaled") == today

    if already:
        msg = LILAC("You already journaled today. Petal smiles softly... ") + DIMTEXT("(+2 happiness)")
        state["happiness"] = clamp(state["happiness"] + 2)
    else:
        state["happiness"]  = clamp(state["happiness"]  + 12)
        state["discipline"] = clamp(state["discipline"] + 10)
        state["growth"]     = clamp(state["growth"]     + 8)

        # streak
        yesterday = str(date.fromordinal(date.today().toordinal() - 1))
        if state.get("last_journaled") == yesterday:
            state["journal_streak"] = state.get("journal_streak", 0) + 1
        else:
            state["journal_streak"] = 1

        state["last_journaled"] = today
        msg = MINT("Petal glows warmly. ") + DIMTEXT("Happiness +12  Discipline +10  Growth +8")

    state["total_actions"] = state.get("total_actions", 0) + 1
    print(); print(" " + msg); print()
    return state

def action_study(state: dict) -> dict:
    today = str(date.today())
    already = state.get("last_studied") == today

    if already:
        msg = LILAC("You've already studied today. Petal nods gently... ") + DIMTEXT("(+3 discipline)")
        state["discipline"] = clamp(state["discipline"] + 3)
    else:
        state["discipline"] = clamp(state["discipline"] + 15)
        state["growth"]     = clamp(state["growth"]     + 10)
        state["happiness"]  = clamp(state["happiness"]  + 5)
        state["last_studied"] = today
        msg = SOFTGOLD("Petal stands a little taller. ") + DIMTEXT("Discipline +15  Growth +10  Happiness +5")

    state["total_actions"] = state.get("total_actions", 0) + 1
    print(); print(" " + msg); print()
    return state

def action_rest(state: dict) -> dict:
    state["happiness"] = clamp(state["happiness"] + 8)

    # check evolution
    g     = state["growth"]
    stage = state["stage"]
    if stage < len(STAGE_NEXT) and g >= STAGE_NEXT[stage]:
        state["stage"] += 1
        new_stage = STAGE_NAMES[state["stage"]]
        print()
        print(ROSEWATER(f"  ✦ ✦ ✦  Petal evolved into {C.BOLD}{new_stage}{C.RESET}{ROSEWATER('  ✦ ✦ ✦')}"))
        print(LILAC("  Something shifted. Something opened. She feels new."))
        print()
        input(DIMTEXT("  press enter to continue..."))
    else:
        msg = MIST("Petal curls up quietly. ") + DIMTEXT("Happiness +8")
        print(); print(" " + msg); print()

    state["total_actions"] = state.get("total_actions", 0) + 1
    return state

def action_check(state: dict):
    """Show detailed stats screen."""
    clear()
    print()
    print(ROSEWATER("  ✦ Petal's Full Status"))
    print(DIMTEXT("  " + "─" * 44))
    print()

    age = (date.today() - date.fromisoformat(state["birthday"])).days
    stage = STAGE_NAMES[min(state["stage"], len(STAGE_NAMES)-1)]

    print(f"  {LILAC('Name')}      {state['name']}")
    print(f"  {LILAC('Stage')}     {stage}")
    print(f"  {LILAC('Age')}       Day {age}")
    print(f"  {LILAC('Streak')}    {state.get('journal_streak', 0)} days journaling")
    print(f"  {LILAC('Actions')}   {state.get('total_actions', 0)} total interactions")
    print()

    next_threshold = STAGE_NEXT[min(state["stage"], len(STAGE_NEXT)-1)]
    needed = max(0, next_threshold - state["growth"])
    print(f"  {MINT('Growth to next stage:')}  {needed} points needed")
    print()
    print(DIMTEXT("  Last journaled:  ") + VANILLA(state.get("last_journaled", "never")))
    print(DIMTEXT("  Last studied:    ") + VANILLA(state.get("last_studied",   "never")))
    print()
    print(DIMTEXT("  " + "─" * 44))
    input(DIMTEXT("\n  press enter to go back..."))

# ─────────────────────────────────────────────
# MENU
# ─────────────────────────────────────────────
def show_menu():
    print(f"  {LILAC('1')}  {VANILLA('Write in journal')}        {DIMTEXT('happiness + discipline + growth')}")
    print(f"  {LILAC('2')}  {VANILLA('Do replay / study')}       {DIMTEXT('discipline + growth + happiness')}")
    print(f"  {LILAC('3')}  {VANILLA('Rest together')}           {DIMTEXT('happiness  ·  check evolution')}")
    print(f"  {LILAC('4')}  {VANILLA('Check full status')}")
    print(f"  {LILAC('5')}  {VANILLA('Leave for now')}")
    print()

# ─────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────
def main():
    state = load_state()
    state = apply_daily_decay(state)

    while True:
        render(state)
        show_menu()

        choice = input(DIMTEXT("  > ") + VANILLA("")).strip()

        if choice == "1":
            state = action_journal(state)
            save_state(state)
            input(DIMTEXT("  press enter to continue..."))

        elif choice == "2":
            state = action_study(state)
            save_state(state)
            input(DIMTEXT("  press enter to continue..."))

        elif choice == "3":
            state = action_rest(state)
            save_state(state)
            if state["stage"] < 4:
                input(DIMTEXT("  press enter to continue..."))

        elif choice == "4":
            action_check(state)

        elif choice == "5":
            clear()
            print()
            mood = get_mood(state)
            color = MOOD_COLORS.get(mood, VANILLA)
            print(color("  Petal watches you go..."))
            print(DIMTEXT("  She'll be here when you return."))
            print()
            save_state(state)
            sys.exit(0)

        else:
            pass  # just re-render on invalid input

if __name__ == "__main__":
    main()