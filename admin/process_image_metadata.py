"""อ่านข้อมูลจากโปสเตอร์รุ่นพี่ด้วย OCR ภาษาไทย แล้วสร้าง metadata สำหรับหน้าเว็บ"""

from __future__ import annotations

import json
import re
from pathlib import Path

from paddleocr import PaddleOCR


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data_images.json"
OUTPUT = ROOT / "image_metadata.json"
OCR_OUTPUT = ROOT / "ocr_text.json"


def extract_text(result: object) -> list[str]:
    payload = result.json
    return payload["res"]["rec_texts"]


def main() -> None:
    items = json.loads(SOURCE.read_text(encoding="utf-8"))
    old = {}
    if OCR_OUTPUT.exists():
        try:
            old = {item["path"]: item for item in json.loads(OCR_OUTPUT.read_text(encoding="utf-8"))}
        except (ValueError, KeyError, TypeError):
            old = {}
    ocr = PaddleOCR(
        lang="th",
        text_detection_model_name="PP-OCRv5_mobile_det",
        text_recognition_model_name="th_PP-OCRv5_mobile_rec",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        enable_mkldnn=False,
    )

    raw = []
    for index, item in enumerate(items, start=1):
        if item["path"] in old:
            raw.append({**old[item["path"]], "year": item["year"], "path": item["path"]})
            print(f"[{index}/{len(items)}] skip {item['path']}")
            continue
        results = list(ocr.predict(str(ROOT / item["path"])))
        texts = extract_text(results[0]) if results else []
        raw.append({**item, "texts": texts})
        print(f"[{index}/{len(items)}] {item['path']}")

    OCR_OUTPUT.write_text(
        json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # แปลงผล OCR เป็น metadata พร้อมใช้ filter ต่อทันที
    from build_metadata import main as build_metadata

    build_metadata()


if __name__ == "__main__":
    main()
