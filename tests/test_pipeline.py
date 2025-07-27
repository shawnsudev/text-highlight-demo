from pathlib import Path
from video_pipeline import build_ffmpeg_command


def test_hw_accel_codec(tmp_path):
    dummy_png = tmp_path / "dummy.png"
    dummy_png.write_bytes(b"\x89PNG\r\n\x1a\n")
    cfg = {
        "png_path": str(dummy_png),
        "output_video": str(tmp_path / "out.mp4"),
        "duration": 1,
        "width": 640,
        "height": 360,
        "fps": 30,
        "fade_in": 0.1,
        "fade_out": 0.1,
        "hw_accel": True,
    }
    cmd = build_ffmpeg_command(cfg)
    assert "hevc_videotoolbox" in cmd


def test_sw_codec(tmp_path):
    dummy_png = tmp_path / "dummy.png"
    dummy_png.write_bytes(b"\x89PNG\r\n\x1a\n")
    cfg = {
        "png_path": str(dummy_png),
        "output_video": str(tmp_path / "out.mp4"),
        "duration": 1,
        "width": 640,
        "height": 360,
        "fps": 30,
        "fade_in": 0.1,
        "fade_out": 0.1,
        "hw_accel": False,
    }
    cmd = build_ffmpeg_command(cfg)
    assert "libx265" in cmd
