"""Wrap a preview's source path without hiding characters or terminal controls."""
import unicodedata


def path_lines(path, columns):
    lines = [""]
    width = 0
    for character in path:
        # Filenames must not be able to emit terminal control sequences.
        display = ascii(character)[1:-1] if unicodedata.category(character).startswith("C") else character
        for char in display:
            cells = 0 if unicodedata.combining(char) else (2 if unicodedata.east_asian_width(char) in "WF" else 1)
            if width + cells > columns and lines[-1]:
                lines.append("")
                width = 0
            lines[-1] += char
            width += cells
    return lines
