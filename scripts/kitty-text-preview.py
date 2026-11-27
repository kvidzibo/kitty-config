"""Keep the complete source path above less, including after terminal resize."""
import os
from pathlib import Path
import signal
import re
import subprocess
import tempfile

from kitty_preview_header import path_lines


def wrapped_lines(lines, columns):
    from kitty.fast_data_types import Screen, truncate_point_for_length, wcswidth

    style = Screen(None, 1, 2)
    colors = link = ""
    for line in lines:
        # Split complete escape sequences before measuring: Kitty's truncation
        # helper handles SGR, but not zero-width OSC 8 hyperlinks.
        tokens = re.split(r"(\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x1b\x07]*(?:\x07|\x1b\\)|\t)",
                          line.rstrip("\r\n"))
        row = colors + link
        width = source_width = 0
        for token in tokens:
            if token.startswith("\x1b"):
                row += token
                if token.startswith("\x1b[") and token.endswith("m"):
                    style.apply_sgr(token[2:-1])
                    style.cursor_position(1, 1)
                    style.draw("x")
                    colors = style.line(0).as_ansi()[:-1]
                elif token.startswith("\x1b]8;"):
                    link = token
                continue
            if token == "\t":
                token = " " * (8 - source_width % 8)
            while token:
                end = truncate_point_for_length(token, columns - width)
                if end:
                    row += token[:end]
                    cells = wcswidth(token[:end])
                    width += cells
                    source_width += cells
                    token = token[end:]
                if token:
                    if not width:
                        # A wide character cannot fit in a one-column terminal.
                        row += "?"
                        source_width += wcswidth(token[0])
                        token = token[1:]
                    yield row + "\033[0m\033]8;;\033\\"
                    row, width = colors + link, 0
        yield row + "\033[0m\033]8;;\033\\"


def main(args):
    markdown = len(args) == 3 and args[1] == "--markdown"
    if len(args) != (3 if markdown else 2):
        raise SystemExit("Usage: kitty-text-preview.sh [--markdown] FILE")
    path = os.path.abspath(args[-1])
    pager = None
    resized = False

    def resize(_signal, _frame):
        nonlocal resized
        resized = True
        if pager is not None and pager.poll() is None:
            pager.terminate()

    previous = signal.signal(signal.SIGWINCH, resize)
    try:
        with tempfile.TemporaryDirectory(prefix="kitty-text-preview-") as directory:
            preview = Path(directory) / "preview"
            while True:
                resized = False
                size = os.get_terminal_size()
                header = path_lines(path, max(1, size.columns - 1))
                if len(header) >= size.lines - 2:
                    raise SystemExit("Terminal too short to show the full path; enlarge it and reopen.")
                with preview.open("wb") as output:
                    output.write(("\n".join(header) + "\n").encode())
                    source_path = path
                    if markdown:
                        source_path = str(Path(directory) / "markdown")
                        with open(source_path, "wb") as rendered:
                            subprocess.run(["glow", "--style", "dark", "--width", str(size.columns - 1), path],
                                           stdout=rendered, check=True)
                    with open(source_path, encoding="utf-8", errors="replace") as source:
                        for wrapped in wrapped_lines(source, max(1, size.columns - 1)):
                            output.write((wrapped + "\n").encode())
                pager = subprocess.Popen([
                    "less", "-R", "-c", "-+F", f"--header={len(header)},{size.columns}",
                    "--no-number-headers", "--no-search-header-lines",
                    "-P" + "PREVIEW | q to close | arrows to scroll", "--", str(preview),
                ], env={**os.environ, "LESSHISTFILE": "-"})
                if resized:
                    pager.terminate()
                code = pager.wait()
                pager = None
                if not resized:
                    raise SystemExit(code)
    finally:
        signal.signal(signal.SIGWINCH, previous)
        if pager is not None and pager.poll() is None:
            pager.terminate()
            pager.wait()
