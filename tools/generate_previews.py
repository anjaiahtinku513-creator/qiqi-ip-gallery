from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageSequence


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "previews"
SUPPORTED = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
STATIC_MAX_SIZE = (1280, 1280)
ANIMATED_MAX_SIZE = (360, 360)


def has_alpha(image: Image.Image) -> bool:
    return image.mode in {"RGBA", "LA"} or (
        image.mode == "P" and "transparency" in image.info
    )


def make_static_preview(source: Path, destination: Path) -> None:
    with Image.open(source) as image:
        converted = image.convert("RGBA" if has_alpha(image) else "RGB")
        converted.thumbnail(STATIC_MAX_SIZE, Image.Resampling.LANCZOS)
        converted.save(destination, "WEBP", quality=80, method=6)


def make_animated_preview(source: Path, destination: Path) -> None:
    with Image.open(source) as image:
        default_duration = image.info.get("duration", 100)
        loop = image.info.get("loop", 0)
        frames: list[Image.Image] = []
        durations: list[int] = []

        for frame in ImageSequence.Iterator(image):
            converted = frame.convert("RGBA")
            converted.thumbnail(ANIMATED_MAX_SIZE, Image.Resampling.LANCZOS)
            frames.append(converted.copy())
            durations.append(frame.info.get("duration", default_duration))

        frames[0].save(
            destination,
            "WEBP",
            save_all=True,
            append_images=frames[1:],
            duration=durations,
            loop=loop,
            quality=70,
            method=6,
        )


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    sources = sorted(
        path
        for path in ROOT.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED
    )

    for source in sources:
        destination = OUTPUT / f"{source.stem}.webp"
        with Image.open(source) as probe:
            animated = bool(getattr(probe, "is_animated", False))

        if animated:
            make_animated_preview(source, destination)
        else:
            make_static_preview(source, destination)

        original_kb = source.stat().st_size / 1024
        preview_kb = destination.stat().st_size / 1024
        print(
            f"{source.name}: {original_kb:.1f} KB -> "
            f"previews/{destination.name}: {preview_kb:.1f} KB"
        )


if __name__ == "__main__":
    main()
