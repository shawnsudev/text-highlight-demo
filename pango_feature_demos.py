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

import yaml
from datetime import datetime

# Canvas/settings – populated from YAML config (initial placeholders)
CANVAS_WIDTH = 0
CANVAS_HEIGHT = 0
WRAP_RATIO = 0.0
WRAP_WIDTH = 0
BACKGROUND_COLOR = (0.0, 0.0, 0.0)
TEXT_COLOR = (1.0, 1.0, 1.0)
DEFAULT_HIGHLIGHT_COLOR = (0.0, 0.6, 1.0)
BASE_FONT_FAMILY = "Arial"
BASE_FONT_SIZE_PT = 12
CANVAS_WIDTH: int
CANVAS_HEIGHT: int
WRAP_RATIO: float
WRAP_WIDTH: int
BACKGROUND_COLOR: Tuple[float, float, float]
TEXT_COLOR: Tuple[float, float, float]
DEFAULT_HIGHLIGHT_COLOR: Tuple[float, float, float]
BASE_FONT_FAMILY: str
BASE_FONT_SIZE_PT: int


# ---------------------------------------------------------------------------

def rgb_to_hex(rgb: Tuple[float, float, float]) -> str:
    return "#" + "".join(f"{int(c*255):02x}" for c in rgb)


def make_markup(
    sentence: str,
    phrase: str,
    *,
    extra_attrs: Dict[str, str] | None = None,
    highlight_color: Tuple[float, float, float] | None = None,
    font_size_pt: float | None = None,
) -> str:
    if phrase not in sentence:
        raise ValueError("highlight phrase not found in sentence")

    start = sentence.index(phrase)
    end = start + len(phrase)



    if highlight_color is None:
        highlight_color = DEFAULT_HIGHLIGHT_COLOR
    if font_size_pt is None:
        font_size_pt = BASE_FONT_SIZE_PT

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
    ap.add_argument("--sentence")
    ap.add_argument("--highlight")
    ap.add_argument("--basename", default="demo")
    ap.add_argument("--config", default="config.yml", help="YAML configuration file")
    args = ap.parse_args()

    # Load configuration --------------------------------------------------
    cfg_path = Path(args.config)
    if cfg_path.exists():
        with cfg_path.open() as f:
            cfg = yaml.safe_load(f) or {}
    else:
        cfg = {}

    # Apply config overrides to globals -----------------------------------
    global CANVAS_WIDTH, CANVAS_HEIGHT, WRAP_RATIO, WRAP_WIDTH
    global BACKGROUND_COLOR, TEXT_COLOR, DEFAULT_HIGHLIGHT_COLOR
    global BASE_FONT_FAMILY, BASE_FONT_SIZE_PT

    CANVAS_WIDTH = cfg.get("canvas_width", CANVAS_WIDTH)
    CANVAS_HEIGHT = cfg.get("canvas_height", CANVAS_HEIGHT)
    WRAP_RATIO = cfg.get("wrap_ratio", WRAP_RATIO)
    WRAP_WIDTH = int(CANVAS_WIDTH * WRAP_RATIO)

    BACKGROUND_COLOR = tuple(cfg.get("background_color", BACKGROUND_COLOR))  # type: ignore[arg-type]
    TEXT_COLOR = tuple(cfg.get("text_color", TEXT_COLOR))  # type: ignore[arg-type]
    DEFAULT_HIGHLIGHT_COLOR = tuple(cfg.get("default_highlight_color", DEFAULT_HIGHLIGHT_COLOR))  # type: ignore[arg-type]
    BASE_FONT_FAMILY = cfg.get("base_font_family", BASE_FONT_FAMILY)
    BASE_FONT_SIZE_PT = cfg.get("base_font_size_pt", BASE_FONT_SIZE_PT)

    # Determine output directory -----------------------------------------
    output_root = Path(cfg.get("output_dir", "output"))
    mode = cfg.get("output_dir_mode", "timestamped")
    if mode == "timestamped":
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = output_root / timestamp
    else:
        output_dir = output_root
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sentence / highlight ------------------------------------------------
    if args.sentence and args.highlight:
        sent, phrase = args.sentence, args.highlight
    else:
        text_cfg = cfg.get("text") or {}
        sent = text_cfg.get("base")
        phrase = text_cfg.get("highlight")
        if not (sent and phrase):
            ap.error("Provide --sentence/--highlight or set text.base and text.highlight in config.yaml")
    stem = Path(args.basename).stem

    # Variants ------------------------------------------------------------
    variants_cfg = cfg.get("variants")
    if variants_cfg:
        variants = []
        for suffix, detail in variants_cfg.items():
            extra_attrs = detail.get("extra_attrs", {})
            color = tuple(detail.get("highlight_color", DEFAULT_HIGHLIGHT_COLOR))  # type: ignore[arg-type]
            variants.append((suffix, extra_attrs, color))
    else:
        variants = [
            ("color", {}, (0.0, 0.6, 1.0)),
            ("size", {"size": str(int(BASE_FONT_SIZE_PT * 1.4 * 1024))}, DEFAULT_HIGHLIGHT_COLOR),
            ("family", {"font_family": "Courier New"}, DEFAULT_HIGHLIGHT_COLOR),
            ("weight", {"weight": "bold"}, DEFAULT_HIGHLIGHT_COLOR),
            ("style", {"style": "italic"}, DEFAULT_HIGHLIGHT_COLOR),
            ("underline", {"underline": "single"}, DEFAULT_HIGHLIGHT_COLOR),
            ("strike", {"strikethrough": "true"}, DEFAULT_HIGHLIGHT_COLOR),
            ("rise", {"rise": "10000"}, DEFAULT_HIGHLIGHT_COLOR),
        ]

    # Render --------------------------------------------------------------
    for suffix, extra_attrs, color in variants:
        markup = make_markup(sent, phrase, extra_attrs=extra_attrs, highlight_color=color)
        render(markup, output_dir / f"{stem}_{suffix}.png")


if __name__ == "__main__":
    main()
