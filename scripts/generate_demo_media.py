"""Generate stable synthetic demo media for the RadScan Lite README."""

from __future__ import annotations

from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "demo_assets"
WIDTH = 1280
HEIGHT = 720


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    options = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for name in options:
        path = Path(name)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, size: int, color: str, bold: bool = False) -> None:
    draw.text(xy, value, fill=color, font=font(size, bold))


def card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str = "#ffffff") -> None:
    draw.rounded_rectangle(box, radius=18, fill=fill)


def render_frame() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#f5f7fa")
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, WIDTH, 92), fill="#1d3447")
    text(draw, (44, 28), "RadScan Lite", 36, "#ffffff", True)
    text(draw, (846, 34), "Synthetic DICOM preflight scan", 20, "#cad7e4")

    card(draw, (44, 122, 362, 274))
    text(draw, (72, 148), "Files scanned", 21, "#667085", True)
    text(draw, (72, 184), "15", 58, "#194185", True)
    text(draw, (154, 204), "synthetic DICOM files", 20, "#667085")

    card(draw, (392, 122, 710, 274))
    text(draw, (420, 148), "Findings", 21, "#667085", True)
    text(draw, (420, 184), "8", 58, "#b42318", True)
    text(draw, (484, 204), "quality and privacy checks", 20, "#667085")

    card(draw, (740, 122, 1058, 274))
    text(draw, (768, 148), "Profile", 21, "#667085", True)
    text(draw, (768, 190), "sharing-review", 30, "#116149", True)
    text(draw, (768, 232), "Privacy-weighted report view", 18, "#667085")

    card(draw, (44, 306, 620, 648))
    text(draw, (72, 336), "Finding summary", 25, "#243b67", True)
    rows = [
        ("ERROR", "Duplicate SOP Instance UID", "2 files"),
        ("WARNING", "Private tags present", "5 files"),
        ("WARNING", "BurnedInAnnotation missing", "5 files"),
        ("INFO", "Pixel spacing varies by series", "1 series"),
    ]
    y = 394
    colors = {"ERROR": "#b42318", "WARNING": "#b76e00", "INFO": "#175cd3"}
    for severity, finding, scope in rows:
        draw.rounded_rectangle((72, y - 8, 588, y + 42), radius=10, fill="#f2f4f7")
        text(draw, (92, y), severity, 17, colors[severity], True)
        text(draw, (208, y), finding, 17, "#344054")
        text(draw, (504, y), scope, 17, "#667085")
        y += 62

    card(draw, (660, 306, 1236, 648))
    text(draw, (688, 336), "Series review", 25, "#243b67", True)
    bars = [("clean_ct", 96, "#157347"), ("inconsistent_ct", 68, "#b76e00"), ("privacy_warning", 42, "#b42318")]
    y = 408
    for name, width, color in bars:
        text(draw, (688, y - 32), name, 19, "#344054", True)
        draw.rounded_rectangle((688, y, 1148, y + 28), radius=12, fill="#e4e7ec")
        draw.rounded_rectangle((688, y, 688 + int(width * 4.6), y + 28), radius=12, fill=color)
        text(draw, (1168, y - 1), f"{width}%", 18, "#667085")
        y += 82

    text(
        draw,
        (44, 676),
        "Synthetic files only - generated for public documentation and regression demos.",
        18,
        "#667085",
    )
    return image


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    frame = render_frame()
    frame.save(ASSET_DIR / "demo-poster.png")
    frames = [frame.copy() for _ in range(4)]
    frames[0].save(ASSET_DIR / "demo.gif", save_all=True, append_images=frames[1:], duration=650, loop=0)
    with imageio.get_writer(ASSET_DIR / "demo.mp4", fps=1, codec="libx264", quality=8) as writer:
        for still in frames:
            writer.append_data(np.asarray(still))


if __name__ == "__main__":
    main()
