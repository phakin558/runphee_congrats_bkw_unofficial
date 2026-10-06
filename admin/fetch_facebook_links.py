"""ดึง direct preview image URLs จาก public Facebook albums ผ่าน fromfb.app

ลิงก์ที่ได้เป็น signed URLs จึงควรรันสคริปต์นี้ซ้ำเมื่อหมดอายุ
สคริปต์ไม่ดาวน์โหลดรูปภาพลงเครื่อง
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent.parent
ALBUMS = json.loads((ROOT / "album_sources.json").read_text(encoding="utf-8"))
OUTPUT = ROOT / "facebook_images.json"
PUBLIC_OUTPUT = ROOT / "public" / "facebook_images.json"
BASE = "https://fromfb.app"


def resolve(session: requests.Session, album_url: str) -> dict:
    last_error = "ไม่สามารถอ่าน album ได้"
    for attempt in range(1, 4):
        try:
            csrf_response = session.get(f"{BASE}/api/csrf", timeout=30)
            csrf_response.raise_for_status()
            csrf = csrf_response.json().get("token")
            if not csrf:
                raise RuntimeError("ไม่ได้ CSRF token")
            response = session.post(
                f"{BASE}/api/resolve",
                headers={"X-CSRF-TOKEN": csrf, "Accept": "application/json"},
                data={"locale": "en", "url": album_url, "mode": "photo"},
                timeout=90,
            )
            payload = response.json()
            if not response.ok:
                last_error = payload.get("error", f"HTTP {response.status_code}")
                raise RuntimeError(last_error)
            if not payload.get("ok") or payload.get("kind") != "album":
                raise RuntimeError(payload.get("error", last_error))
            return payload["album"]
        except (requests.RequestException, ValueError, RuntimeError) as error:
            last_error = str(error)
            if attempt < 3:
                time.sleep(attempt * 3)
    raise RuntimeError(last_error)


def finish_enumeration(session: requests.Session, album: dict) -> dict:
    """รอให้ fromfb ไล่รูปทั้งอัลบั้มเสร็จ และรวมรายการที่ทยอยส่งกลับมา"""
    items = list(album.get("items", []))
    seen = {item.get("id") for item in items if item.get("id")}
    status_url = album.get("status_url")
    started = time.monotonic()
    while album.get("state") == "enumerating" and status_url:
        if time.monotonic() - started > 180:
            raise TimeoutError("รอรายการรูปจาก Facebook เกิน 180 วินาที")
        time.sleep(2)
        response = session.get(
            f"{status_url}?after={len(items)}&locale=en",
            headers={"Accept": "application/json"},
            timeout=60,
        )
        response.raise_for_status()
        update = response.json()
        for item in update.get("items", []):
            item_id = item.get("id")
            if not item_id or item_id not in seen:
                items.append(item)
                if item_id:
                    seen.add(item_id)
        album["state"] = update.get("state", album.get("state"))
        if update.get("title") and not album.get("title"):
            album["title"] = update["title"]
        print(f"  collecting: {len(items)} items ({album.get('state')})")
    album["items"] = items
    return album


def main() -> None:
    session = requests.Session()
    session.headers.update({"User-Agent": "BKW-Alumni-Album-Refresh/1.0"})
    previous = {}
    if OUTPUT.exists():
        try:
            previous = {str(row["year"]): row for row in json.loads(OUTPUT.read_text(encoding="utf-8"))}
        except (ValueError, KeyError, TypeError):
            previous = {}
    output = []
    for year, album_url in sorted(ALBUMS.items(), key=lambda pair: int(pair[0]), reverse=True):
        try:
            album = finish_enumeration(session, resolve(session, album_url))
            record = {
                "year": int(year),
                "albumUrl": album_url,
                "title": album.get("title"),
                "images": [
                    {
                        "facebookId": item.get("id"),
                        "number": item.get("num"),
                        "imageUrl": item.get("preview_url"),
                        "width": item.get("width"),
                        "height": item.get("height"),
                    }
                    for item in album.get("items", [])
                    if item.get("preview_url")
                ],
            }
            print(f"year {year}: {len(record['images'])} image links")
        except Exception as error:
            record = previous.get(str(year), {"year": int(year), "albumUrl": album_url, "title": None, "images": []})
            record["albumUrl"] = album_url
            record["error"] = str(error)
            print(f"year {year}: ERROR {error}")
        output.append(record)
        time.sleep(0.5)
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PUBLIC_OUTPUT.parent.mkdir(exist_ok=True)
    PUBLIC_OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.name}")


if __name__ == "__main__":
    main()
