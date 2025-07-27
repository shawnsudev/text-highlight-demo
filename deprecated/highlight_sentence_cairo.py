#!/usr/bin/env python3
"""Generate a 1920x1080 PNG of a sentence with a highlighted phrase using Cairo + Pango.

This script avoids ImageMagick's Pango delegate by using the Pango / Cairo
bindings available via GObject-Introspection (gi.repository).

Dependencies (macOS Homebrew):
  brew install pygobject3 pycairo

You may also need to ensure the Python libffi site-package can find
GObject introspection typelibs; this is handled automatically when using the
Homebrew Python.

Usage:
  python3 highlight_sentence_cairo.py \
      --sentence "Sarah finally saw the light at the end of the tunnel." \
      --highlight "the end of the tunnel" \
      --output output.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import gi  # type: ignore
except ImportError as exc:  # pragma: no cover
    sys.stderr.write(
        "PyGObject not available. Install with: brew install pygobject3 pycairo\n"
    )
    raise exc

gi.require_version("Pango", "1.0")

gi.require_version("PangoCairo", "1.0")

import cairo  # PyCairo bindings
from gi.repository import Pango, PangoCairo  # type: ignore  # noqa: E402
from html import escape


# ---- Constants ---------------------------------------------------------------
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080
WRAP_RATIO = 0.92  # 92 %
WRAP_WIDTH = int(CANVAS_WIDTH * WRAP_RATIO)
FONT_FAMILY = "Arial"
BASE_FONT_SIZE_PT = 100  # points
BACKGROUND_COLOR = (0.2, 0.2, 0.2)  # gray
TEXT_COLOR = (1.0, 1.0, 1.0)  # white
HIGHLIGHT_COLOR = (1.0, 1.0, 0.0)  # yellow


# ---- Helpers -----------------------------------------------------------------


def build_markup(sentence: str, phrase: str, *, font_size_pt: float = BASE_FONT_SIZE_PT, highlight_font: str | None = None) -> str:
    """Return a Pango markup string with *phrase* highlighted."""
    if phrase not in sentence:
        raise ValueError("highlight phrase not found in sentence")

    start = sentence.index(phrase)
    end = start + len(phrase)

    base_span = f"<span font_family='{FONT_FAMILY}' size='{int(font_size_pt * 1024)}' foreground='{rgb_to_hex(TEXT_COLOR)}'>"
    highlight_span_open = f"<span foreground='{rgb_to_hex(HIGHLIGHT_COLOR)}'"
    if highlight_font:
        highlight_span_open += f" font_family='{highlight_font}'"
    highlight_span_open += ">"

    return (
        base_span
        + escape(sentence[:start])
        + highlight_span_open
        + escape(phrase)
        + "</span>"
        + escape(sentence[end:])
        + "</span>"
    )


def rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    """Convert (r, g, b) floats 0-1 to #RRGGBB."""
    return "#" + "".join(f"{int(c * 255):02x}" for c in rgb)


# ---- Main rendering ----------------------------------------------------------


def render(sentence: str, phrase: str, output: Path, *, font_size_pt: float = BASE_FONT_SIZE_PT, stroke: bool = False, highlight_font: str | None = None) -> None:
    # Create Cairo ARGB surface and context
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, CANVAS_WIDTH, CANVAS_HEIGHT)
    ctx = cairo.Context(surface)

    # Fill background
    ctx.set_source_rgb(*BACKGROUND_COLOR)
    ctx.paint()

    # Create Pango layout
    layout = PangoCairo.create_layout(ctx)
    layout.set_width(WRAP_WIDTH * Pango.SCALE)
    layout.set_wrap(Pango.WrapMode.WORD_CHAR)

    markup = build_markup(sentence, phrase, font_size_pt=font_size_pt, highlight_font=highlight_font)
    layout.set_markup(markup, -1)

    # Query text extents to centre it
    _, logical_extents = layout.get_pixel_extents()
    text_width = logical_extents.width
    text_height = logical_extents.height

    x = (CANVAS_WIDTH - text_width) / 2
    y = (CANVAS_HEIGHT - text_height) / 2

    ctx.translate(x, y)

    if stroke:
        # Draw text path then stroke with red border
        PangoCairo.layout_path(ctx, layout)
        ctx.set_source_rgb(1.0, 0.0, 0.0)  # red
        ctx.set_line_width(5)
        ctx.stroke_preserve()
        # Fill text afterwards
    PangoCairo.show_layout(ctx, layout)

    surface.write_to_png(str(output))
    print(f"Image written to {output}")


# ---- CLI ---------------------------------------------------------------------


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("--sentence", required=True)
    parser.add_argument("--highlight", required=True)
    parser.add_argument("--basename", default="output", help="Base filename without extension")
    args = parser.parse_args()

    base_path = Path(args.basename)
    stem = base_path.stem
    parent = base_path.parent
    # Variant 1: baseline
    render(args.sentence, args.highlight, parent / f"{stem}_v1.png", font_size_pt=BASE_FONT_SIZE_PT)
    # Variant 2: 1.3x font size
    render(args.sentence, args.highlight, parent / f"{stem}_v2.png", font_size_pt=BASE_FONT_SIZE_PT * 1.3)
    # Variant 3: red stroke border 5px
    render(args.sentence, args.highlight, parent / f"{stem}_v3.png", font_size_pt=BASE_FONT_SIZE_PT, stroke=True)
    # Variant 4: different font for highlight (e.g., Times New Roman)
    render(args.sentence, args.highlight, parent / f"{stem}_v4.png", font_size_pt=BASE_FONT_SIZE_PT, highlight_font="Times New Roman")

    print("Variants written:")
    for i in range(1, 5):
        print(f"  {stem}_v{i}.png")


if __name__ == "__main__":  # pragma: no cover
    main()
