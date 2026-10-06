"""สร้าง data_images.json จากรูปภาพทุกโฟลเดอร์รุ่นที่รู้จัก"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data_images.json"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def natural_key(path: Path) -> tuple[int, str]:
    """เรียงเลขท้ายชื่อไฟล์ เช่น 2 ก่อน 10"""
    match = re.search(r"(\d+)(?=\.[^.]+$)", path.name)
    return (int(match.group(1)) if match else -1, path.name.lower())


def main() -> None:
    folders = []
    for path in ROOT.iterdir():
        if not path.is_dir():
            continue
        match = re.fullmatch(r"bkw(\d{4})", path.name)
        real_match = re.fullmatch(r"bkw_real_(\d{4})", path.name)
        if match:
            year = int(match.group(1))
            if path.name == "bkw2566":
                year = 2565
            folders.append((year, path))
        elif real_match:
            folders.append((int(real_match.group(1)), path))
    years = sorted(folders, key=lambda pair: pair[0])

    images = []
    for year, folder in years:
        files = sorted(
            (
                path
                for path in folder.iterdir()
                if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
            ),
            key=natural_key,
        )
        images.extend(
            {
                "year": year,
                "path": path.relative_to(ROOT).as_posix(),
            }
            for path in files
        )

    OUTPUT.write_text(
        json.dumps(images, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(images)} images to {OUTPUT.name}")


if __name__ == "__main__":
    main()
