"""Fixed-width working/ready/PR-status indicator for Kitty's tab titles."""

import re
from time import monotonic
from weakref import WeakKeyDictionary

from kitty.fast_data_types import add_timer, get_boss
from kitty.progress import ProgressState

# A pie that fills clockwise, then empties clockwise. Filling: Material Design
# circle slices 1-8, Nerd Font icons as large as the git logo, which Braille
# dots cannot be. Emptying: their mirror images, seven to one eighths left,
# from fonts/KittyTabPie.ttf (see symbol_map in kitty.conf).
FRAMES = "".join(map(chr, [*range(0xF0A9E, 0xF0AA6), *range(0x100006, 0xFFFFF, -1)]))
# Codex's native title refreshes its spinner while the TUI is working.
CODEX_WORKING = re.compile(r"^codex [⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏] Working(?: \||$)")
# Values: working, unread completion, or expiry time for an active completion.
STATES = WeakKeyDictionary()
# Pinote's `pinote_pr` user variable, most urgent first. One Nerd Font icon
# (Material Design git logo); its colour tells the states apart.
PR_ICON = "\U000f02a2"
# Material Design bold check, as large as the git logo, which ✓ cannot be.
DONE_ICON = "\U000f0e1e"
PR_COLORS = {
    "failing": "_e06c75",
    "pending": "_e5c07b",
    "passing": "_98c379",
    "merged": "_c678dd",
    # No current status (not checked yet, outdated or unavailable), or closed.
    "unknown": "_5c6370",
    "closed": "_5c6370",
}


def draw_title(data):
    tab = get_boss().tab_for_id(data["tab_id"])
    if tab is None:
        return "  "
    manager = tab.tab_manager_ref()
    active = manager is not None and manager.active_tab is tab
    busy = any(window.progress.state is ProgressState.indeterminate
               or CODEX_WORKING.match(window.title) for window in tab)
    previous = STATES.get(tab)
    now = monotonic()
    if busy:
        STATES[tab] = "working"
        symbol = FRAMES[int(now * 8) % len(FRAMES)]
        color = "_e5c07b"
    else:
        if previous == "working":
            if active:
                STATES[tab] = now + 2
                tab_id = data["tab_id"]

                def expire(_timer_id):
                    current = get_boss().tab_for_id(tab_id)
                    if current is not None:
                        current.mark_tab_bar_dirty()

                add_timer(expire, 2.05, False)
            else:
                STATES[tab] = "unread"
        elif previous == "unread" and active:
            STATES.pop(tab, None)
        state = STATES.get(tab)
        if isinstance(state, (int, float)) and now >= state:
            STATES.pop(tab, None)
            state = None
        # Idle: the most urgent PR status of any pane outranks the completion check.
        prs = {window.user_vars.get("pinote_pr") for window in tab}
        status = next((name for name in PR_COLORS if name in prs), None)
        if status is not None:
            symbol, color = PR_ICON, PR_COLORS[status]
        elif state is None:
            return "  "
        else:
            symbol = DONE_ICON
            color = "_98c379"
    fg = data["fmt"].fg
    return f"{getattr(fg, color)}{symbol}{fg.tab} "


def on_set_user_var(boss, window, data):
    """Global watcher: Kitty does not redraw the tab bar when a user variable changes."""
    if data.get("key") == "pinote_pr":
        tab = window.tabref()
        if tab is not None:
            tab.mark_tab_bar_dirty()
