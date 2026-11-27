"""Save shell-only sessions after layout changes and before Kitty's Quit action."""
import runpy
from pathlib import Path

from kitty.config import atomic_save
from kitty.constants import config_dir
from kitty.fast_data_types import add_timer
from kitty.utils import log_error

sanitize = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts/kitty-session-shells.py")
)["sanitize"]
SESSION_PATH = Path(config_dir) / "main.session"
_pending = False
_quitting = False


def _save(boss):
    if boss.shutting_down:
        return
    try:
        session = sanitize("\n".join(boss.serialize_state_as_session(str(SESSION_PATH))))
        # Preserve the last usable layout when the final pane/window is closed.
        if not any(line.split(maxsplit=1)[:1] == ["launch"] for line in session.splitlines()):
            return
        if SESSION_PATH.exists() and SESSION_PATH.read_text() == session:
            return
        atomic_save(session.encode(), str(SESSION_PATH))
    except Exception as error:
        log_error(f"Kitty session save failed: {error}")


def _schedule(boss, window, data):
    global _pending
    if _pending or _quitting or boss.shutting_down:
        return
    _pending = True

    def save_after_update(timer_id):
        global _pending
        _pending = False
        if not _quitting:
            _save(boss)

    # Coalesce bursts and let removals/moves finish updating the layout first.
    add_timer(save_after_update, 0.3, False)


on_resize = _schedule
on_close = _schedule
on_focus_change = _schedule
on_tab_bar_dirty = _schedule


def on_cmd_startstop(boss, window, data):
    if not data["is_start"]:
        _schedule(boss, window, data)


def on_quit(boss, window, data):
    global _quitting
    if data["confirmed"]:
        _save(boss)
        # Do not replace the complete snapshot with teardown's shrinking layout.
        _quitting = True
