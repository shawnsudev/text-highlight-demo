# Image Highlight Demo (Cairo + Pango)

This repo shows **exactly** which inline-text features can be controlled
purely with Pango markup by rendering sentences to PNG via Cairo.

`pango_feature_demos.py` writes one PNG per feature so future contributors
see what is feasible without struggling with ImageMagick’s Pango delegate.

## Quick Start

```
# 1. install Homebrew libs + Python wheels
./install.sh

# 2. generate demo images
python3 pango_feature_demos.py \
  --sentence "Growth comes from stepping out of the comfort zone." \
  --highlight "comfort zone" \
  --basename demo
```

## Why Cairo + Pango instead of Blender VSE?

### Pros
- **Pixel-perfect text layout** using Pango’s typography engine (proper kerning, shaping, word-wrapping) – VSE text strip is very limited.
- **Programmatic generation**: run headless on CI or server; no Blender GUI required.
- **Full inline styling** via markup (`size`, `family`, `weight`, `color`, etc.).
- **Lightweight dependencies** (Cairo, Pango) vs. full Blender install.
- **Faster iteration** when you just need 2-D text images.

### Cons
- No built-in timeline/key-frame UI – you must script any animation yourself (e.g. loop 30 frames and vary opacity).
- No 3-D text extrusion or advanced compositor effects that Blender offers.
- Requires a small amount of Python/GTK knowledge, whereas VSE can be used entirely through its UI.

---

## Pango-Markup Features Demonstrated
| File suffix | Attribute(s) | Effect |
|-------------|--------------|--------|
| `_color`    | `foreground` | Blue text |
| `_size`     | `size`       | 1.4× font size |
| `_family`   | `font_family`| Courier New |
| `_weight`   | `weight`     | Bold |
| `_style`    | `style`      | Italic |
| `_underline`| `underline`  | Single underline |
| `_strike`   | `strikethrough` | Strikethrough |
| `_rise`     | `rise`       | Superscript |

## Do / Don’t for Installation & Configuration

### ✅ Do
1. **Use Homebrew** to install `pygobject3`, `py3cairo`, and
   `gobject-introspection` on macOS (Apple-silicon & Intel):
   ```bash
   brew install pygobject3 py3cairo gobject-introspection
   ```
2. **Use pip** only for pure-Python wheels (currently just `pycairo` is
   required in `requirements.txt`).
3. **Render with Cairo/Pango** instead of ImageMagick’s `pangocairo:` coder.
   It is faster, avoids delegate crashes, and gives full control.
4. **Keep build paths short & space-free** if you _must_ compile
   ImageMagick from source (libtool errors otherwise).

### ❌ Don’t
1. **Don’t rely on Homebrew’s `imagemagick` bottle** – it is built **without
   Pango support**.
2. **Don’t use old third-party taps** such as `imagemagick-pango`; source
   URLs are 404 and formulas are outdated.
3. **Don’t place temporary Pango markup files in paths containing spaces** –
   older `pangocairo` aborts on those paths.
4. **Don’t expect stroke/outline via markup** – Pango markup has no such
   attribute; composite a second stroked layer instead.

## Troubleshooting
• *ModuleNotFoundError: cairo* – ensure `brew install py3cairo` succeeded and
  the Homebrew Python is on PATH.
• *gi.repository.* errors – `pygobject3` must match your Python version.

---

© 2025  Released under MIT licence.
