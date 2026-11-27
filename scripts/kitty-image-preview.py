"""Zoomable image preview, run with Kitty's bundled Python/TUI."""

from contextlib import contextmanager
import math
import os
import subprocess
import tempfile

from kitty_preview_header import path_lines


@contextmanager
def preview_image(path):
    if not path.lower().endswith((".svg", ".svgz")):
        yield path
        return
    with tempfile.TemporaryDirectory(prefix="kitty-svg-") as directory:
        rendered = os.path.join(directory, "preview.png")
        try:
            subprocess.run(
                ["rsvg-convert", "--output", rendered, "--", path],
                check=True, timeout=30,
            )
        except FileNotFoundError:
            raise SystemExit("SVG previews require rsvg-convert (Debian: librsvg2-bin).") from None
        except subprocess.TimeoutExpired:
            raise SystemExit("SVG preview rendering timed out.") from None
        except subprocess.CalledProcessError:
            raise SystemExit("Could not render SVG preview.") from None
        yield rendered


def placement(image_size, terminal_size, zoom, center, header_rows=2):
    width, height = image_size
    cols, rows, cell_width, cell_height = terminal_size
    header = min(header_rows, max(0, rows - 1))
    view_width, view_height = cols * cell_width, (rows - header) * cell_height
    scale = min(1, view_width / width, view_height / height) * zoom
    crop_width = min(width, max(1, round(view_width / scale)))
    crop_height = min(height, max(1, round(view_height / scale)))
    x = max(0, min(width - crop_width, round(center[0] - crop_width / 2)))
    y = max(0, min(height - crop_height, round(center[1] - crop_height / 2)))
    dest_cols = min(cols, max(1, math.ceil(crop_width * scale / cell_width)))
    dest_rows = min(rows - header, max(1, math.ceil(crop_height * scale / cell_height)))
    return (
        (x, y, crop_width, crop_height),
        (dest_cols, dest_rows),
        ((cols - dest_cols) // 2, header + (rows - header - dest_rows) // 2),
    )


def drag_center(center, delta, source_size, display_size):
    return (
        center[0] - delta[0] * source_size[0] / display_size[0],
        center[1] - delta[1] * source_size[1] / display_size[1],
    )


def main(args):
    if len(args) != 2:
        raise SystemExit("Usage: kitty-image-overlay.sh IMAGE")
    source = os.path.abspath(args[1])
    with preview_image(source) as path:
        show_image(path, source)


def show_image(path, source):
    from kittens.tui.handler import Handler
    from kittens.tui.images import identify
    from kittens.tui.loop import EventType, Loop, MouseButton
    from kittens.tui.operations import MouseTracking, styled
    from kitty.fast_data_types import Color

    image = identify(path)

    class Preview(Handler):
        mouse_tracking = MouseTracking.buttons_and_drag
        drag_pos = None
        zoom = 1
        center = (image.width / 2, image.height / 2)

        def initialize(self):
            size = self.screen_size
            # Upload at native resolution once; zoom/pan only changes the placement.
            cols = max(size.cols, math.ceil(image.width / size.cell_width))
            rows = max(size.rows, math.ceil(image.height / size.cell_height))
            self.write(subprocess.check_output([
                "kitten", "icat", "--stdin=no", "--transfer-mode=stream",
                f"--use-window-size={size.cols},{size.rows},{size.width},{size.height}",
                "--image-id=2", "--align=left", f"--place={cols}x{rows}@0x0",
                "--", path,
            ]))
            self.cmd.set_cursor_visible(False)
            self.draw()

        @Handler.atomic_update
        def draw(self):
            size = self.screen_size
            headings = path_lines(source, max(1, size.cols - 1))
            hints = (
                "q/Esc/RMB close | +/-/wheel zoom",
                f"{self.zoom * 100:.0f}% | drag/arrows pan | 0 fit",
            )
            lines = headings + list(hints)
            previous_header_rows = getattr(self, "header_rows", 0)
            self.header_rows = min(len(lines), max(0, size.rows - 1))
            crop, dest, origin = placement(
                (image.width, image.height),
                (size.cols, size.rows, size.cell_width, size.cell_height),
                self.zoom, self.center, self.header_rows,
            )
            self.center = (crop[0] + crop[2] / 2, crop[1] + crop[3] / 2)
            self.crop = crop
            self.dest = dest
            # Clear placements, not the screen: ESC[2J also deletes image data.
            self.cmd.clear_images_on_screen()
            for row in range(min(size.rows, max(previous_header_rows, self.header_rows))):
                self.cmd.set_cursor_position(0, row)
                self.write("\033[K")
            for row, hint in enumerate(lines[:self.header_rows]):
                self.cmd.set_cursor_position(0, row)
                self.write(styled(hint[:size.cols], fg=Color(210, 185, 255), bold=True))
            self.cmd.set_cursor_position(*origin)
            self.cmd.gr_command({
                "a": "p", "i": 2, "q": 2, "C": 1,
                "x": crop[0], "y": crop[1], "w": crop[2], "h": crop[3],
                "c": dest[0], "r": dest[1],
            })

        def change_zoom(self, factor):
            self.zoom = max(0.25, min(16, self.zoom * factor))
            self.draw()

        def on_text(self, text, in_bracketed_paste=False):
            if in_bracketed_paste:
                return
            if text == "q":
                self.quit_loop(0)
            elif text in ("+", "="):
                self.change_zoom(1.25)
            elif text == "-":
                self.change_zoom(0.8)
            elif text == "0":
                self.zoom = 1
                self.center = (image.width / 2, image.height / 2)
                self.draw()

        def on_key(self, event):
            if event.matches("esc"):
                self.quit_loop(0)
                return
            for key, dx, dy in (("left", -1, 0), ("right", 1, 0), ("up", 0, -1), ("down", 0, 1)):
                if event.matches(key):
                    self.center = (
                        self.center[0] + dx * self.crop[2] / 8,
                        self.center[1] + dy * self.crop[3] / 8,
                    )
                    self.draw()
                    break

        def on_mouse_event(self, event):
            if event.type is EventType.RELEASE:
                self.drag_pos = None
                if event.buttons == MouseButton.RIGHT:
                    self.quit_loop(0)
            elif event.type is EventType.PRESS:
                if event.buttons == MouseButton.WHEEL_UP:
                    self.change_zoom(1.25)
                elif event.buttons == MouseButton.WHEEL_DOWN:
                    self.change_zoom(0.8)
                elif event.buttons == MouseButton.LEFT:
                    self.drag_pos = ((event.pixel_x, event.pixel_y)
                                     if event.cell_y >= self.header_rows else None)
            elif event.type is EventType.MOVE and event.buttons & MouseButton.LEFT and self.drag_pos is not None:
                size = self.screen_size
                position = (event.pixel_x, event.pixel_y)
                self.center = drag_center(
                    self.center,
                    (position[0] - self.drag_pos[0], position[1] - self.drag_pos[1]),
                    self.crop[2:],
                    (self.dest[0] * size.cell_width, self.dest[1] * size.cell_height),
                )
                self.drag_pos = position
                self.draw()

        def on_resize(self, size):
            super().on_resize(size)
            self.drag_pos = None
            self.draw()

        def finalize(self):
            self.cmd.clear_images_on_screen(delete_data=True)

        def on_interrupt(self):
            self.quit_loop(0)

    loop = Loop()
    loop.loop(Preview())
    raise SystemExit(loop.return_code)
