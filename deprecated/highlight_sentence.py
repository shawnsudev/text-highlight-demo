#!/usr/bin/env python3
"""Generate a 1920×1080 PNG containing a sentence where a target phrase is highlighted.

Key features
------------
• Text wraps to 92 % of the canvas width (≈ 1765 px) so nothing overruns the edge.
• Grey background fills the entire full-HD canvas.
• Highlighted words are rendered in yellow; other text is white.
• Everything is rendered in a single ImageMagick call using Pango markup, so
  line-breaking remains natural.

Example
-------
python highlight_sentence.py \
    --sentence "Sarah finally saw the light at the end of the tunnel, after months of hard work on this challenging project." \
    --highlight "the end of the tunnel" \
    --output idiom.png
"""

from __future__ import annotations

import argparse
import html
import shutil
import subprocess
import sys
from pathlib import Path

CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080
WRAP_WIDTH = int(CANVAS_WIDTH * 0.92)  # 92 % of width
FONT_FAMILY = "Arial"
POINT_SIZE = 100  # pt
DEFAULT_COLOR = "white"
HIGHLIGHT_COLOR = "yellow"
BACKGROUND_COLOR = "gray"


def check_dependencies() -> None:
    """Ensure ImageMagick (`magick`) CLI tool is available."""
    if shutil.which("magick") is None:
        sys.exit("ImageMagick 'magick' command not found. Install with: brew install imagemagick")


def escape(text: str) -> str:
    """Escape text for inclusion in Pango XML markup."""
    return html.escape(text, quote=True)


def build_markup(sentence: str, phrase: str) -> str:
    """Return a Pango markup string with `phrase` highlighted yellow."""
    if phrase not in sentence:
        sys.exit("Highlight phrase must be a substring of the sentence.")

    esc_sentence = escape(sentence)
    esc_phrase = escape(phrase)
    span = f"<span foreground='{HIGHLIGHT_COLOR}'>{esc_phrase}</span>"
    marked = esc_sentence.replace(esc_phrase, span, 1)

    # Point-size in Pango markup is in Pango units = pt * 1024
    size_attr = POINT_SIZE * 1024
    return (
        f"<span font_family='{FONT_FAMILY}' foreground='{DEFAULT_COLOR}' size='{size_attr}'>"
        f"{marked}</span>"
    )


def render_image(markup_path: Path, output_path: Path) -> None:
    """Invoke ImageMagick to composite wrapped text onto grey canvas."""
    cmd = [
        "magick",
        # 1. Create solid grey canvas
        "-size",
        f"{CANVAS_WIDTH}x{CANVAS_HEIGHT}",
        f"xc:{BACKGROUND_COLOR}",
        # 2. Generate wrapped text as a separate image using Pango
        "(",
        "-size",
        f"{WRAP_WIDTH}x",  # width only, height auto
        "-background",
        "none",
        f"pango:@{markup_path}",
        ")",
        # 3. Composite centre
        "-gravity",
        "center",
        "-composite",
        str(output_path),
    ]

    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a text image with highlighted phrase.")
    parser.add_argument("--sentence", required=True, help="Full sentence text.")
    parser.add_argument("--highlight", required=True, help="Phrase within the sentence to highlight.")
    parser.add_argument("--output", default="output.png", help="Output PNG file path.")
    args = parser.parse_args()

    check_dependencies()

    import tempfile
    # Use system temporary directory to avoid paths with spaces that confuse Pango
    tmp_dir = Path(tempfile.gettempdir()) / "im_markup"
    tmp_dir.mkdir(exist_ok=True)
    markup_file = tmp_dir / "markup.txt"
    markup_file.write_text(build_markup(args.sentence, args.highlight), encoding="utf-8")

    render_image(markup_file, Path(args.output))
    print(f"Image written to {args.output}")


if __name__ == "__main__":
    main()
