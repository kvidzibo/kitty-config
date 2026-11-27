"""Observe X11 wheel events without grabbing or redirecting mouse input."""

import fcntl
import hashlib
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import tempfile


KITTEN = Path(__file__).resolve().parents[1] / "kitty/scroll-tabs.py"


def output(*command):
    return subprocess.check_output(
        command, text=True, stderr=subprocess.DEVNULL, timeout=1,
    ).strip()


def fields(value):
    return dict(line.split("=", 1) for line in value.splitlines())


def scroll(button):
    try:
        mouse = fields(output("xdotool", "getmouselocation", "--shell"))
        xid = str(int(mouse["WINDOW"]))
        pid = int(output("xdotool", "getwindowpid", xid))
        if Path(f"/proc/{pid}/exe").resolve(strict=True).name != "kitty":
            return
        # xdotool's geometry can double-count offsets in reparenting WMs (i3).
        geometry = output("xwininfo", "-id", xid, "-stats")
        left, top = map(int, re.findall(r"Absolute upper-left [XY]:\s+(-?\d+)", geometry))
        x = int(mouse["X"]) - left
        y = int(mouse["Y"]) - top
        output(
            "kitten", "@", "--to", f"unix:@mykitty-{pid}", "kitten",
            str(KITTEN), xid, str(x), str(y), "-1" if button == 4 else "1",
        )
    except (OSError, subprocess.SubprocessError, ValueError, KeyError):
        # Windows can disappear, or belong to a Kitty without remote control.
        pass


def main():
    display = os.environ.get("DISPLAY", "")
    if not display or os.environ.get("XDG_SESSION_TYPE") == "wayland":
        raise SystemExit("Kitty tab scrolling requires an X11 session.")
    for command in ("xinput", "stdbuf", "xdotool", "xwininfo", "kitten"):
        if shutil.which(command) is None:
            raise SystemExit(f"Missing required command: {command}")

    # One observer per user/display, including across i3 restarts.
    display_id = hashlib.sha256(display.removesuffix(".0").encode()).hexdigest()[:12]
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", tempfile.gettempdir()))
    with (runtime / f"kitty-tab-scroll-{os.getuid()}-{display_id}.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return

        def stop(_signum, _frame):
            raise SystemExit(0)

        signal.signal(signal.SIGTERM, stop)
        # Select the master pointer only: all devices would count each notch twice.
        listener = subprocess.Popen(
            ["stdbuf", "-oL", "xinput", "test-xi2", "--root", "Virtual core pointer"],
            stdout=subprocess.PIPE, text=True,
        )
        try:
            pressed = False
            for line in listener.stdout:
                line = line.strip()
                if line.startswith("EVENT type"):
                    pressed = "(RawButtonPress)" in line
                elif pressed and line.startswith("detail:"):
                    pressed = False
                    button = int(line.split(":", 1)[1])
                    if button in (4, 5):
                        scroll(button)
            raise SystemExit(listener.wait())
        finally:
            listener.terminate()
            listener.wait()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
