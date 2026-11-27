import gzip
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "image_preview", Path(__file__).resolve().parents[1] / "scripts/kitty-image-preview.py")
preview = importlib.util.module_from_spec(spec)
with patch.object(sys, "path", [str(Path(__file__).resolve().parents[1] / "scripts"), *sys.path]):
    spec.loader.exec_module(preview)


class ImagePreviewTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("rsvg-convert") and shutil.which("magick"), "SVG preview tools required")
    def test_svg_styles_and_symbols_render_and_cleanup_on_close(self):
        svg = b'''<svg xmlns="http://www.w3.org/2000/svg" width="20" height="10">
          <style>.paper { fill: white; } .art { fill: #287860; }</style>
          <defs><symbol id="art" viewBox="0 0 10 10"><rect class="art" width="10" height="10"/></symbol></defs>
          <rect class="paper" width="20" height="10"/>
          <use href="#art" x="10" width="10" height="10"/>
        </svg>'''
        rendered_paths = []

        def show_rendered(path, source):
            self.assertEqual(source, str(svg_source))
            rendered_paths.append(Path(path))
            pixels = subprocess.check_output([
                "magick", path, "-format", "%[pixel:p{1,1}]|%[pixel:p{11,1}]", "info:",
            ], text=True)
            self.assertEqual(pixels, "srgb(255,255,255)|srgb(40,120,96)")
            raise SystemExit(0)

        with tempfile.TemporaryDirectory() as directory:
            for suffix in (".svg", ".SVGZ"):
                with self.subTest(suffix=suffix):
                    source = Path(directory) / ("a draft" + suffix)
                    svg_source = source
                    source.write_bytes(gzip.compress(svg) if suffix == ".SVGZ" else svg)
                    with patch.object(preview, "show_image", side_effect=show_rendered):
                        with self.assertRaises(SystemExit) as closed:
                            preview.main(["preview", str(source)])
                    self.assertEqual(closed.exception.code, 0)
                    self.assertFalse(rendered_paths[-1].parent.exists())
                    self.assertTrue(source.exists())
            with preview.preview_image(str(Path(directory) / "unchanged.png")) as path:
                self.assertEqual(path, str(Path(directory) / "unchanged.png"))

    def test_full_path_header_wraps_and_reserves_image_rows(self):
        path = "/tmp/a long directory/界/file name.svg"
        lines = preview.path_lines(path, 12)
        self.assertEqual("".join(lines), path)
        self.assertGreater(len(lines), 1)
        self.assertEqual(preview.path_lines("/tmp/a\x1b\n.png", 80), [r"/tmp/a\x1b\n.png"])
        _, _, origin = preview.placement((100, 100), (12, 20, 10, 20), 2, (50, 50), len(lines) + 2)
        self.assertGreaterEqual(origin[1], len(lines) + 2)
        # Exercise text wrapping with the actual runtime used by the pager.
        scripts = str(Path(__file__).resolve().parents[1] / "scripts")
        subprocess.run(["kitty", "+runpy", '''
import runpy, sys
from kitty.fast_data_types import wcswidth
sys.path.insert(0, sys.argv[1])
wrap_rows = runpy.run_path(sys.argv[1] + '/kitty-text-preview.py')['wrapped_lines']
wrap = lambda text, columns, wrap_rows=wrap_rows: wrap_rows(text.splitlines(True), columns)
lines = list(wrap('\\t\\x1b[31m0123456789\\x1b[0m\\n', 8))
assert all(wcswidth(line) <= 8 for line in lines), lines
assert lines[0].startswith('        '), lines
assert lines[-1].startswith('\\x1b[31m'), lines
opening = '\\x1b]8;;https://example.com\\x1b' + chr(92)
closing = '\\x1b]8;;\\x1b' + chr(92)
links = list(wrap(opening + '123456789' + closing, 8))
assert len(links) == 2 and all(opening in line for line in links), links
assert '12345678' in links[0] and '9' in links[1], links
assert list(wrap('12345678901\\tX', 10))[-1].startswith('1     X')
multi = list(wrap(opening + 'first\\n123456789' + closing, 8))
assert len(multi) == 3 and all(opening in line for line in multi), multi
colored = list(wrap('\\x1b[31mfirst\\n123456789\\x1b[0m', 8))
assert len(colored) == 3 and all(line.startswith('\\x1b[31m') for line in colored), colored
rows = list(wrap('\\x1b[31mx\\x1b[39m\\n' * 1000, 8))
assert len(rows) == 1000 and sum(map(len, rows)) < 50000
''', scripts], check=True)

    def test_drag_follows_pointer_at_zoom_scale(self):
        self.assertEqual(
            preview.drag_center((1000, 500), (120, -60), (500, 250), (1000, 500)),
            (940, 530),
        )

    def test_zoom_crop_panning_bounds_and_reserved_hint_rows(self):
        image = (2000, 1000)
        terminal = (100, 30, 10, 20)
        crop, dest, origin = preview.placement(image, terminal, 1, (1000, 500))
        self.assertEqual((crop, dest, origin), ((0, 0, 2000, 1000), (100, 25), (0, 3)))
        crop, dest, origin = preview.placement(image, terminal, 2, (1000, 500))
        self.assertEqual((crop, dest, origin), ((500, 220, 1000, 560), (100, 28), (0, 2)))
        crop, _, origin = preview.placement(image, terminal, 2, (9999, -9999))
        self.assertEqual(crop, (1000, 0, 1000, 560))
        self.assertGreaterEqual(origin[1], 2)


if __name__ == "__main__":
    unittest.main()
