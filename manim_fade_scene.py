"""Simple Manim scene that applies fade-in / fade-out on a PNG.

Configuration is pulled from `config_video.yml` so durations and easing stay in sync
with `video_pipeline.py`.

Usage (inside project root):
    manim -pqh manim_fade_scene.py FadePNGScene

The output video is then post-processed by `video_pipeline.py` if further encoding
(clean looping, h.265) is needed.  You can skip running Manim if you only need
FFmpeg-based fades.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import yaml
from manim import *  # noqa: F401,F403 – Manim constants (Scene, VGroup, etc.)

ROOT = Path(__file__).resolve().parent
CFG_PATH = ROOT / "config_video.yml"

# Map config easing names to Manim rate functions
EASING_TO_RATE_FUNC: Dict[str, callable] = {
    "linear": linear,
    "easein": ease_in_sine,
    "easeout": ease_out_sine,
    "easeinout": ease_in_out_sine,
}


class FadePNGScene(Scene):
    """Fade a static PNG in/out according to YAML config."""

    def construct(self) -> None:  # noqa: D401 – Manim convention
        if not CFG_PATH.exists():
            raise FileNotFoundError(f"Config file not found: {CFG_PATH}")

        with CFG_PATH.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        png_path = str((ROOT / cfg["png_path"]).expanduser())
        fade_in_dur = cfg.get("fade_in_duration", 1.5)
        fade_out_dur = cfg.get("fade_out_duration", 1.5)
        total_dur = cfg.get("total_duration", 10)
        steady_dur = total_dur - fade_in_dur - fade_out_dur

        easing_in = cfg.get("easing_in", "linear").lower()
        easing_out = cfg.get("easing_out", "linear").lower()

        rate_in = EASING_TO_RATE_FUNC.get(easing_in, linear)
        rate_out = EASING_TO_RATE_FUNC.get(easing_out, linear)

        # Create ImageMobject
        img = ImageMobject(png_path).scale_to_fit_height(config.frame_height)
        img.set_opacity(0.0)
        self.add(img)

        # Fade-in
        self.play(img.animate.set_opacity(1.0), run_time=fade_in_dur, rate_func=rate_in)
        # Static hold
        self.wait(max(0, steady_dur))
        # Fade-out
        self.play(img.animate.set_opacity(0.0), run_time=fade_out_dur, rate_func=rate_out)
