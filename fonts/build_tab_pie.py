"""Build KittyTabPie.ttf: the tab bar's emptying pie frames.

Hack Nerd Font has pie slices that fill clockwise but none that empty
clockwise. Those are the same slices mirrored, placed at U+100000-U+100006
(one to seven eighths left). Metrics are copied so both fonts draw alike.

    uv run --with fonttools fonts/build_tab_pie.py [HackNerdFont-Regular.ttf]
"""

from pathlib import Path
import sys

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

SOURCE = Path.home() / ".local/share/fonts/Hack/HackNerdFont-Regular.ttf"
SLICES = range(0xF0A9E, 0xF0AA5)  # md-circle_slice_1 to 7
FIRST = 0x100000


def main():
    source = TTFont(sys.argv[1] if len(sys.argv) > 1 else SOURCE)
    cmap, glyphs = source.getBestCmap(), source.getGlyphSet()
    empty = TTGlyphPen(None).glyph()
    built, widths, codes = {".notdef": empty}, {".notdef": (0, 0)}, {}
    for index, code in enumerate(SLICES):
        name, original = f"pie_left_{index + 1}", glyphs[cmap[code]]
        bounds = BoundsPen(glyphs)
        original.draw(bounds)
        left, _, right, _ = bounds.bounds
        pen = TTGlyphPen(None)
        # Mirroring flips the winding direction; reverse it back.
        original.draw(TransformPen(ReverseContourPen(pen), (-1, 0, 0, 1, left + right, 0)))
        built[name] = pen.glyph()
        widths[name] = (original.width, round(left))
        codes[FIRST + index] = name
    hhea, os2 = source["hhea"], source["OS/2"]
    font = FontBuilder(source["head"].unitsPerEm, isTTF=True)
    font.setupGlyphOrder(list(built))
    font.setupCharacterMap(codes)
    font.setupGlyf(built)
    font.setupHorizontalMetrics(widths)
    font.setupHorizontalHeader(ascent=hhea.ascent, descent=hhea.descent, lineGap=hhea.lineGap)
    font.setupNameTable({
        "familyName": "Kitty Tab Pie",
        "styleName": "Regular",
        "copyright": "Mirrored circle-slice glyphs from Material Design Icons (Apache-2.0), via Nerd Fonts.",
    })
    font.setupOS2(sTypoAscender=os2.sTypoAscender, sTypoDescender=os2.sTypoDescender,
                  sTypoLineGap=os2.sTypoLineGap, usWinAscent=os2.usWinAscent,
                  usWinDescent=os2.usWinDescent)
    font.setupPost()
    # A fixed timestamp keeps rebuilds byte-identical.
    font.font["head"].created = font.font["head"].modified = 3_850_000_000
    font.font.recalcTimestamp = False
    font.save(Path(__file__).with_name("KittyTabPie.ttf"))


if __name__ == "__main__":
    main()
