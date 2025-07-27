from manim import *
from pathlib import Path

# Configuration values (edit as needed)
IMAGE_PATH = Path("output/demo/2025-07-27_14-09-42/demo_color.png")  # generated PNG
OUTPUT_RESOLUTION = (1920, 1080)  # match canvas size
FADE_DURATION = 1.5  # seconds
TOTAL_DURATION = 10  # seconds
HOLD_DURATION = TOTAL_DURATION - 2 * FADE_DURATION  # middle section


class ImageFade(Scene):
    """Simple Scene that fades an ImageMobject in, waits, then fades it out."""

    def construct(self):
        # Load image and scale to full width while preserving aspect ratio
        if not IMAGE_PATH.exists():
            raise FileNotFoundError(f"{IMAGE_PATH} not found. Generate image first.")

        img = ImageMobject(str(IMAGE_PATH))
        img.set_resampling_algorithm(RESAMPLING_ALGEBRAIC)
        # Auto scale based on width of scene
        img.set(width=OUTPUT_RESOLUTION[0] * 0.9)
        self.camera.background_color = (0, 0, 0, 0)  # transparent background

        # Fade in, hold, fade out
        self.play(FadeIn(img, run_time=FADE_DURATION))
        self.wait(HOLD_DURATION)
        self.play(FadeOut(img, run_time=FADE_DURATION))


if __name__ == "__main__":
    # Convenience: run manim programmatically when executed directly
    from manim import config, tempconfig

    # Ensure transparency and override default writer if desired
    with tempconfig({
        "transparent": True,
        "background_opacity": 0.0,
        "frame_rate": 30,
        "pixel_height": OUTPUT_RESOLUTION[1],
        "pixel_width": OUTPUT_RESOLUTION[0],
    }):
        scene = ImageFade()
        scene.render()

        # After render, convert to efficient 10-second h.265 using ffmpeg by
        # looping a single frame (middle) would be done in a separate step.
        # Example command (run separately):
        # ffmpeg -y -loop 1 -i output_frame.png -c:v libx265 -t 10 \ 
        #   -vf "format=rgba,fade=t=in:st=0:d=1.5:alpha=1,fade=t=out:st=8.5:d=1.5:alpha=1" \
        #   -pix_fmt yuv420p final.mp4
