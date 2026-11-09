# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 my3w-98
#
# This file is part of HEIC Convert.
# https://github.com/my3w-98/heic-convert
"""HEIC/HEIF bulk conversion using pillow-heif + Pillow."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

SUPPORTED_INPUTS = {".heic", ".heif"}

OUTPUT_FORMATS: dict[str, dict] = {
    "JPEG": {"ext": ".jpg", "pil": "JPEG", "lossy": True, "needs_rgb": True},
    "PNG": {"ext": ".png", "pil": "PNG", "lossy": False, "needs_rgb": False},
    "WebP": {"ext": ".webp", "pil": "WEBP", "lossy": True, "needs_rgb": False},
    "TIFF": {"ext": ".tiff", "pil": "TIFF", "lossy": False, "needs_rgb": False},
    "BMP": {"ext": ".bmp", "pil": "BMP", "lossy": False, "needs_rgb": True},
    "GIF": {"ext": ".gif", "pil": "GIF", "lossy": False, "needs_rgb": True},
}


@dataclass
class ConvertResult:
    source: Path
    destination: Path | None
    ok: bool
    error: str | None = None


def collect_heic_files(paths: list[Path], recursive: bool = True) -> list[Path]:
    """Expand files/folders into a de-duplicated sorted list of HEIC/HEIF paths."""
    found: set[Path] = set()
    for path in paths:
        path = path.resolve()
        if path.is_file() and path.suffix.lower() in SUPPORTED_INPUTS:
            found.add(path)
        elif path.is_dir():
            pattern = "**/*" if recursive else "*"
            for child in path.glob(pattern):
                if child.is_file() and child.suffix.lower() in SUPPORTED_INPUTS:
                    found.add(child.resolve())
    return sorted(found)


def _prepare_image(img: Image.Image, needs_rgb: bool) -> Image.Image:
    if needs_rgb:
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            background = Image.new("RGB", img.size, (255, 255, 255))
            rgba = img.convert("RGBA")
            background.paste(rgba, mask=rgba.split()[-1])
            return background
        return img.convert("RGB")
    if img.mode == "P":
        return img.convert("RGBA")
    return img


def convert_file(
    source: Path,
    output_dir: Path,
    format_name: str,
    quality: int = 90,
    overwrite: bool = False,
) -> ConvertResult:
    """Convert a single HEIC/HEIF file to the chosen format."""
    source = source.resolve()
    fmt = OUTPUT_FORMATS[format_name]
    dest = output_dir / f"{source.stem}{fmt['ext']}"

    if dest.exists() and not overwrite:
        # Avoid clobbering: photo.jpg -> photo_1.jpg, photo_2.jpg, ...
        n = 1
        while True:
            candidate = output_dir / f"{source.stem}_{n}{fmt['ext']}"
            if not candidate.exists():
                dest = candidate
                break
            n += 1

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as img:
            prepared = _prepare_image(img, fmt["needs_rgb"])
            save_kwargs: dict = {}
            if fmt["lossy"]:
                save_kwargs["quality"] = max(1, min(100, quality))
            if format_name == "JPEG":
                save_kwargs["optimize"] = True
            if format_name == "WebP":
                save_kwargs["method"] = 4
            prepared.save(dest, format=fmt["pil"], **save_kwargs)
        return ConvertResult(source=source, destination=dest, ok=True)
    except Exception as exc:  # noqa: BLE001 — surface any decode/encode failure to the UI
        return ConvertResult(source=source, destination=None, ok=False, error=str(exc))


ProgressCallback = Callable[[int, int, ConvertResult], None]


def convert_batch(
    sources: list[Path],
    output_dir: Path,
    format_name: str,
    quality: int = 90,
    overwrite: bool = False,
    workers: int = 4,
    on_progress: ProgressCallback | None = None,
) -> list[ConvertResult]:
    """Convert many files; optional progress callback receives (done, total, result)."""
    if format_name not in OUTPUT_FORMATS:
        raise ValueError(f"Unsupported format: {format_name}")

    total = len(sources)
    results: list[ConvertResult] = []
    if total == 0:
        return results

    workers = max(1, min(workers, total))
    done = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(convert_file, src, output_dir, format_name, quality, overwrite): src
            for src in sources
        }
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            done += 1
            if on_progress:
                on_progress(done, total, result)

    results.sort(key=lambda r: str(r.source).lower())
    return results
