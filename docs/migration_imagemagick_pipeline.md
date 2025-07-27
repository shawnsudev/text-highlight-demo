# Integrating the “highlight-text → PNG → transparent video” pipeline into **blender-YT-AI**

> Migration playbook generated on **2025-07-27** (verbatim).

# Question: how to incorporate this pipeline into blender-YT-AI?

---
## 1. Add assets & dependencies
1. Copy the experimental folder:
   ```bash
   cp -R imagemagick-highlight-text \
       /Users/weiweisu/CodingWorkspace/blender-YT-AI/src/flashcard_gen/im_highlight/
   ```
2. Append these Python packages to the big project (requirements.txt or pyproject.toml):
   ```
   pyyaml
   cairo                           # or pycairo on Linux
   pangocairocffi                  # or pygobject, whichever works on macOS
   ffmpeg-python
   ```
   FFmpeg itself is already installed system-wide.

---
## 2. Replace the image-build stage (S0 replacement)
Create `src/flashcard_gen/im_highlight/build_png.py`:
```python
from pathlib import Path
from flashcard_gen.im_highlight.pango_feature_demos import main as build_png

def render_flashcard_png(text: str, out_dir: Path) -> Path:
    """Generate transparent PNG with highlighted text."""
    out_dir.mkdir(parents=True, exist_ok=True)
    return Path(build_png(text=text, output_dir=out_dir))
```
Swap the old Blender call:
```python
# OLD
png_path = render_with_blender(...)
# NEW
from flashcard_gen.im_highlight.build_png import render_flashcard_png
png_path = render_flashcard_png(text, tmp_dir)
```

---
## 3. Replace “one-PNG → video” stage (S2 replacement)
Inside the S2 orchestrator (eventually called by `S2_ffmpeg_orchestrate_flashcard_video.py`):
```python
from flashcard_gen.im_highlight.video_pipeline import build_ffmpeg_command, run_cmd
import yaml

cfg = yaml.safe_load(open("config/video_pipeline_flashcard.yml"))
cfg["png_path"] = str(png_path)      # produced in prev step
cfg["output_video"] = str(out_path)  # where S2 expects the clip

run_cmd(build_ffmpeg_command(cfg))
```
Put `video_pipeline_flashcard.yml` (copy of working `config_video.yml`) under `config/`.

---
## 4. Config touch-ups
* Expose HSLA colour keys in your main config so both PNG generation and other assets share colours.

---
## 5. Stub out unused Blender utilities (optional)
If modules now import `bpy` unnecessarily:
```python
try:
    import bpy
except ModuleNotFoundError:
    bpy = None
```

---
## 6. CLI switch (optional)
If the big project has a CLI, add a flag:
```bash
flashcard-cli video --render-backend imagemagick
```

---
## 7. Smoke-test the full flow
```bash
cd /Users/weiweisu/CodingWorkspace/blender-YT-AI
python src/S0_generate_flashcards_text.py --dry-run
python src/S2_ffmpeg_orchestrate_flashcard_video.py --ffmpeg-verbose
```
✔ PNG with alpha generated.
✔ `flashcard_video.webm` fades to full transparency.
✔ Subsequent concatenation still works (or switch codec to ProRes 4444 if VP9-alpha unsupported).
