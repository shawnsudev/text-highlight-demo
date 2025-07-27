"""Video generation pipeline using ffmpeg.

Reads parameters from `config_video.yml` and produces a video that:
1. Starts with an ease-out fade-in (configurable duration/easing).
2. Shows a static transparent PNG for the middle section.
3. Ends with an ease-in fade-out (configurable duration/easing).

FFmpeg is invoked through subprocess; make sure FFmpeg is installed.
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
    """Construct FFmpeg CLI from config values."""
    png = str((ROOT / cfg["png_path"]).expanduser())
    out = str((ROOT / cfg["output_video"]).expanduser())

    width = cfg.get("width")
    height = cfg.get("height")
    fps = cfg.get("fps", 30)
    duration = cfg.get("total_duration", 10)
    fade_in = cfg.get("fade_in_duration", 1.5)
    fade_out = cfg.get("fade_out_duration", 1.5)

    easing_in = EASING_MAP.get(cfg.get("easing_in", "linear"), "linear")
    easing_out = EASING_MAP.get(cfg.get("easing_out", "linear"), "linear")

    # Build filter string
    start_out = duration - fade_out
    vf_parts = [
        f"scale={width}:{height}",
        f"fade=t=in:st=0:d={fade_in}:alpha=1:curve={easing_in}",
        f"fade=t=out:st={start_out}:d={fade_out}:alpha=1:curve={easing_out}",
    ]
    vf = ",".join(vf_parts)

    cmd = [
        "ffmpeg",
        "-y",                   # overwrite output
        "-loop", "1",
        "-i", png,
        "-t", str(duration),
        "-vf", vf,
        "-c:v", cfg.get("codec", "libx265"),
        "-pix_fmt", "yuva420p",  # alpha support (may vary per codec)
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
