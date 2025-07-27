#!/usr/bin/env python3
"""Generate separate PNG images demonstrating individual Pango markup features.

Each output shows the *highlight* phrase styled differently from the rest of the
sentence using **only** Pango span attributes (no Cairo strokes).  This lets you
see exactly which font-related attributes are controllable via markup.

Created variants:
  • _color   – blue highlight colour
  • _size    – 1.4× larger font size
  • _family  – different font family (Courier New)
  • _weight  – bold
  • _style   – italic
  • _underline – single underline
  • _strike  – strikethrough
  • _rise    – superscript rise

Usage example:
  python3 pango_feature_demos.py \
      --sentence "Growth comes from stepping out of the comfort zone." \
      --highlight "comfort zone" \
      --basename demo

This will create files like `demo_color.png`, `demo_size.png`, … in the current
folder.
"""
from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
from typing import Dict, Tuple

import cairo  # type: ignore
import gi  # type: ignore

gi.require_version("Pango", "1.0")

gi.require_version("PangoCairo", "1.0")
from gi.repository import Pango, PangoCairo  # type: ignore

# Canvas/settings
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080
WRAP_RATIO = 0.92
WRAP_WIDTH = int(CANVAS_WIDTH * WRAP_RATIO)
BACKGROUND_COLOR = (0.2, 0.2, 0.2)
TEXT_COLOR = (1.0, 1.0, 1.0)
DEFAULT_HIGHLIGHT_COLOR = (0.0, 0.6, 1.0)  # blue
BASE_FONT_FAMILY = "Arial"
BASE_FONT_SIZE_PT = 100


# ---------------------------------------------------------------------------

def rgb_to_hex(rgb: Tuple[float, float, float]) -> str:
    return "#" + "".join(f"{int(c*255):02x}" for c in rgb)


def make_markup(sentence: str, phrase: str, *, extra_attrs: Dict[str, str] | None = None, highlight_color: Tuple[float, float, float] = DEFAULT_HIGHLIGHT_COLOR, font_size_pt: float = BASE_FONT_SIZE_PT) -> str:
    if phrase not in sentence:
        raise ValueError("highlight phrase not found in sentence")

    start = sentence.index(phrase)
    end = start + len(phrase)

    base_span_open = f"<span font_family='{BASE_FONT_FAMILY}' size='{int(font_size_pt*1024)}' foreground='{rgb_to_hex(TEXT_COLOR)}'>"

    attrs = {
        "foreground": rgb_to_hex(highlight_color),
    }
    if extra_attrs:
        attrs.update(extra_attrs)

    attrs_str = " ".join(f"{k}='{v}'" for k, v in attrs.items())
    highlight_open = f"<span {attrs_str}>"

    return (
        base_span_open
        + escape(sentence[:start])
        + highlight_open
        + escape(phrase)
        + "</span>"  # close highlight
        + escape(sentence[end:])
        + "</span>"  # close base
    )


def render(markup: str, output: Path) -> None:
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, CANVAS_WIDTH, CANVAS_HEIGHT)
    ctx = cairo.Context(surface)

    ctx.set_source_rgb(*BACKGROUND_COLOR)
    ctx.paint()

    layout = PangoCairo.create_layout(ctx)
    layout.set_width(WRAP_WIDTH * Pango.SCALE)
    layout.set_wrap(Pango.WrapMode.WORD_CHAR)
    layout.set_markup(markup, -1)

    _, logical = layout.get_pixel_extents()
    ctx.translate((CANVAS_WIDTH-logical.width)/2, (CANVAS_HEIGHT-logical.height)/2)

    PangoCairo.show_layout(ctx, layout)
    surface.write_to_png(str(output))
    print(f"Wrote {output}")


# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sentence", required=True)
    ap.add_argument("--highlight", required=True)
    ap.add_argument("--basename", default="demo")
    args = ap.parse_args()

    base = Path(args.basename)
    stem = base.stem
    parent = base.parent
    sent, phrase = args.sentence, args.highlight

    variants = [
        ("color", {}, (0.0, 0.6, 1.0)),
        ("size", {"size": str(int(BASE_FONT_SIZE_PT*1.4*1024))}, DEFAULT_HIGHLIGHT_COLOR),
        ("family", {"font_family": "Courier New"}, DEFAULT_HIGHLIGHT_COLOR),
        ("weight", {"weight": "bold"}, DEFAULT_HIGHLIGHT_COLOR),
        ("style", {"style": "italic"}, DEFAULT_HIGHLIGHT_COLOR),
        ("underline", {"underline": "single"}, DEFAULT_HIGHLIGHT_COLOR),
        ("strike", {"strikethrough": "true"}, DEFAULT_HIGHLIGHT_COLOR),
        ("rise", {"rise": "10000"}, DEFAULT_HIGHLIGHT_COLOR),  # 10k Pango units ≈ 10px
    ]

    for suffix, extra_attrs, color in variants:
        markup = make_markup(sent, phrase, extra_attrs=extra_attrs, highlight_color=color)
        render(markup, parent / f"{stem}_{suffix}.png")


if __name__ == "__main__":
    main()
