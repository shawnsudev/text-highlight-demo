"""Video generation pipeline using ffmpeg.

Reads parameters from `config_video.yml` and produces a video that:
1. Starts with an ease-out fade-in (configurable duration/easing).
2. Shows a static transparent PNG for the middle section.
3. Ends with an ease-in fade-out (configurable duration/easing).

FFmpeg is invoked through subprocess; make sure FFmpeg is installed.

Note: Some FFmpeg builds lack the `curve` option on the `fade` filter. We
therefore omit it for broad compatibility (fade will default to linear).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Dict

import yaml

ROOT = Path(__file__).resolve().parent

CONFIG_PATH = ROOT / "config_video.yml"

EASING_MAP: Dict[str, str] = {
    "linear": "linear",
    "easein": "quadratic",   # approximate mapping
    "easeout": "quadratic",
    "easeinout": "cubic",
}

def run_cmd(cmd: list[str]) -> None:
    """Run a shell command and stream output."""
    print(" \\n> " + " ".join(cmd))
    proc = subprocess.run(cmd, check=True)
    if proc.returncode != 0:
        sys.exit(proc.returncode)


def build_ffmpeg_command(cfg: dict) -> list[str]:
    """Construct FFmpeg CLI from config values.

    If `hw_accel` is true in the YAML and running on macOS/Apple Silicon, we
    switch codec to `hevc_videotoolbox` for hardware-accelerated encoding.
    """
    """Construct FFmpeg CLI from config values."""
    png_cfg = cfg["png_path"]
    png_path = (ROOT / png_cfg).expanduser()
    if not png_path.exists():
        # auto-discover latest demo_color.png under output/
        candidates = sorted((ROOT / "output").rglob("demo_color.png"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not candidates:
            raise FileNotFoundError(f"PNG not found: {png_cfg} and no candidates under output/")
        png_path = candidates[0]
        print(f"⚠️ Using discovered PNG: {png_path.relative_to(ROOT)}")
    png = str(png_path)
    out = str((ROOT / cfg["output_video"]).expanduser())

    use_hw = bool(cfg.get("hw_accel", False))

    width = cfg.get("width")
    height = cfg.get("height")
    fps = cfg.get("fps", 30)
    duration = cfg.get("total_duration", 10)
    fade_in = cfg.get("fade_in_duration", 1.5)
    fade_out = cfg.get("fade_out_duration", 1.5)

    easing_in = EASING_MAP.get(cfg.get("easing_in", "linear"), "linear")
    easing_out = EASING_MAP.get(cfg.get("easing_out", "linear"), "linear")

    # Build filter string
    # Start fade-out one frame earlier to ensure opacity hits 0 on last frame
    start_out = duration - fade_out - (1.0 / fps)
    vf_parts = [
        f"scale={width}:{height}",
        f"fade=t=in:st=0:d={fade_in}:alpha=1",
        f"fade=t=out:st={start_out}:d={fade_out}:alpha=1",
    ]
    vf = ",".join(vf_parts)

    codec = cfg.get("codec", "libx265")
    if codec == "vp9alpha":
        codec = "libvpx-vp9"
    if use_hw and codec == "libx265":
        codec = "hevc_videotoolbox"

    cmd = [
        # Note: `pix_fmt yuva420p` can fail with libx265; removed for robustness.
        "ffmpeg",
        "-y",                   # overwrite output
        "-loop", "1",
        "-i", png,
        "-t", str(duration),
        "-vf", vf,
        "-c:v", codec,
        "-pix_fmt", "yuva420p",
       
        "-r", str(fps),
        out,
    ]
    return cmd


def main() -> None:
    if not CONFIG_PATH.exists():
        print(f"Config file {CONFIG_PATH} not found.", file=sys.stderr)
        sys.exit(1)

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    cmd = build_ffmpeg_command(cfg)
    run_cmd(cmd)
    print("\n✅ Video generated at:", cfg["output_video"])


if __name__ == "__main__":
    main()
